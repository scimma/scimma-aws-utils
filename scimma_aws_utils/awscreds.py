import configparser
import logging
import os.path
import sys

import boto3
import botocore
import botocore.config
import requests

from .auth import login_aws_via_idp

logger = logging.getLogger(__name__)


def write_aws_config(profile_name, region, executable):
    config_filepath = os.path.expanduser("~/.aws/config")
    config = configparser.RawConfigParser()
    config.read(config_filepath)

    section_name = f"profile {profile_name}"
    if not config.has_section(section_name):
        config.add_section(section_name)

    config.set(section_name, 'region', region)

    cred_process = f"{executable} login"
    config.set(section_name, "credential_process", cred_process)

    # Write the updated config file.
    with open(config_filepath, 'w+') as configfile:
        config.write(configfile)


def get_aws_creds(username, password, entity_id, role_arn):
    assertion, roles = login_aws_via_idp(
        requests.Session(), username, password, entity_id)
    arns = parse_roles(roles)
    if not role_arn in arns:
        logger.debug("all arns: %s", arns)
        raise ValueError(f"you do not have permission to assume {role_arn}")
    principal_arn = arns[role_arn]
    return sts_creds_from_saml(role_arn, principal_arn, assertion)


def parse_roles(roles):
    arns = {}
    for r in roles:
        role_arn, principal_arn = r.split(",", 1)
        arns[role_arn] = principal_arn
    return arns


def choose_role(awsroles):
    if len(awsroles) > 1:
        i = 0
        print("Please choose the role you would like to assume:")
        for awsrole in awsroles:
            print('[', i, ']: ', awsrole.split(',')[0])
            i += 1
        print("Selection: ", end=' ')
        selectedroleindex = input()

        # Basic sanity check of input
        if int(selectedroleindex) > (len(awsroles) - 1):
            print('You selected an invalid role index, please try again')
            sys.exit(0)

        role_arn = awsroles[int(selectedroleindex)].split(',')[0]
        principal_arn = awsroles[int(selectedroleindex)].split(',')[1]
    else:
        role_arn = awsroles[0].split(',')[0]
        principal_arn = awsroles[0].split(',')[1]
    return role_arn, principal_arn


def sts_creds_from_saml(role_arn, principal_arn, saml_assertion):
    # Skip using any credentials on disk.
    client_conf = botocore.config.Config(
        signature_version=botocore.UNSIGNED,
    )
    client = boto3.client("sts", config=client_conf)
    token = client.assume_role_with_saml(
        RoleArn=role_arn,
        PrincipalArn=principal_arn,
        SAMLAssertion=saml_assertion,
    )
    return token["Credentials"]
