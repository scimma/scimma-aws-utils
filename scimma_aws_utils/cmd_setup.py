import click
import os.path
import requests
import logging
import sys

from typing import Dict

from .auth import login_aws_via_idp
from .awscreds import parse_roles, write_aws_config
from .configs import Config, default_config_file


logger = logging.getLogger(__name__)


@click.command()
@click.option("--config",
              default=default_config_file(),
              help="filename to store configuration information",
              type=click.Path(file_okay=True, writable=True),
              show_default=True)
def setup(config):
    if os.path.exists(config):
        confirmed = click.confirm(
            "Config file already exists. Proceeding will overwrite. OK?")
        if not confirmed:
            return

    # Prompt for IdP Entity ID
    click.echo(click.wrap_text(
        "You'll need to provide your SAML IdP entity ID. Details on campus "
        "IdPs including the SAML entity ID may be found at "
        "https://incommon.org/federation/incommon-federation-entities/.",
    ),
    )
    click.echo()
    print_well_known_idps()
    entity_id = click.prompt("Enter your IdP Entity ID", type=str).strip()

    # Prompt for username and password
    username = click.prompt(
        "Username you use to login to your IdP", type=str).strip()
    password = click.prompt("Password", hide_input=True, type=str)

    region = click.prompt("AWS Region to connect to",
                          type=str, default="us-west-2").strip()
    profile_name = click.prompt(
        "AWS credential profile name to use", type=str, default="default")
    profile_name = profile_name.strip()

    conf = Config(
        entity_id=entity_id,
        username=username,
        password=password,
        region=region,
        profile_name=profile_name,
    )

    click.secho(
        "Verifying your credentials by attempting to log in.", color="yellow")
    assertion, roles = login_aws_via_idp(
        requests.Session(), conf.username, conf.password, conf.entity_id,
    )
    click.secho("Log-in succesful!", color="green")

    roles = parse_roles(roles)
    if len(roles) == 1:
        conf.role_arn = list(roles.keys())[0]
    else:
        conf.role_arn = prompt_for_role(roles)
    click.echo(f"You will log in as {conf.role_arn}.")

    conf.to_file(config)
    click.echo(f"Your configuration has been saved to {config}.")
    write_aws_config(conf.profile_name, conf.region, sys.argv[0])
    click.echo("AWS configuration has been saved.")


def prompt_for_role(roles: Dict[str, str]):
    """ Prompt the user to pick one of the provided roles. """
    click.echo("Choose role to assume")
    enumerated = dict(enumerate(roles.keys(), start=1))
    for i, role_arn in sorted(enumerated.items()):
        click.echo(f"  [{i}]: {role_arn}")
        chosen_idx = click.prompt(
            "Choose role to assume", type=int,
        )
    return enumerated[chosen_idx]


def print_well_known_idps():
    click.echo("Some well-known IdP entity IDs:")
    well_known_idps = {
        "Cornell University": "https://shibidp.cit.cornell.edu/idp/shibboleth",
        "LIGO": "https://login.ligo.org/idp/shibboleth",
        "Penn State": "urn:mace:incommon:psu.edu",
        "University of California, Santa Barbara": "urn:mace:incommon:ucsb.edu",
        "University of Illinois at Urbana-Champaign": "urn:mace:incommon:uiuc.edu",
        "University of Washington": "urn:mace:incommon:washington.edu",
        "University of Wisconsin-Milwaukee": "https://idp.uwm.edu/idp/shibboleth",
    }
    for institution, entity in well_known_idps.items():
        click.secho(f"  {institution}", fg="yellow", nl=False)
        click.secho(f": {entity}")
