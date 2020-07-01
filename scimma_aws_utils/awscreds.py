import configparser
import os.path
import sys

import boto3
import botocore
import botocore.config
import requests

from .auth import login_aws_via_idp


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


def get_aws_creds(username, password, entity_id):
    assertion, roles = login_aws_via_idp(
        requests.Session(), username, password, entity_id)
    role_arn, principal_arn = choose_role(roles)
    return sts_creds_from_saml(role_arn, principal_arn, assertion)


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
