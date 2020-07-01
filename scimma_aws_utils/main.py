import dataclasses
import datetime
import json
import logging
import os
import os.path
import pathlib

import click
import humanize

from .awscreds import get_aws_creds, write_aws_credentials


def default_config_dir() -> pathlib.Path:
    if os.getenv("XDG_CONFIG_HOME"):
        config_root = pathlib.Path(os.getenv("XDG_CONFIG_HOME"))
    else:
        config_root = pathlib.Path.home() / ".config"
    return config_root / "scimma-aws"


def default_config_file() -> pathlib.Path:
    return default_config_dir() / "config"


@click.group()
@click.option("--verbose", is_flag=True)
@click.option("--debug", is_flag=True)
def main(verbose, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)
    pass


@click.command()
@click.option("--config",
              default=default_config_file(),
              help="filename to store configuration information",
              type=click.Path(file_okay=True, writable=True),
              show_default=True)
def setup(config):
    if config_exists(config):
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
    click.echo("Some well-known IdP entity IDs:")
    well_known_idps = {
        "LIGO": "https://login.ligo.org/idp/shibboleth",
        "University of Washington": "urn:mace:incommon:washington.edu",
    }
    for institution, entity in well_known_idps.items():
        click.secho(f"  {institution}", fg="yellow", nl=False)
        click.secho(f": {entity}")
    entity_id = click.prompt("Enter your IdP Entity ID", type=str).strip()

    # Prompt for username and password
    username = click.prompt(
        "Username you use to login to your IdP", type=str).strip()
    password = click.prompt("Password", hide_input=True, type=str)

    region = click.prompt("AWS Region to connect to",
                          type=str, default="us-west-2").strip()
    profile_name = click.prompt(
        "AWS credential profile name to use", type=str, default="scimma")
    profile_name = profile_name.strip()
    # Write config file
    conf = Config(
        entity_id=entity_id,
        username=username,
        password=password,
        region=region,
        profile_name=profile_name,
    )
    conf.to_file(config)
    click.echo(f"Your configuration has been saved to {config}.")


@click.command()
@click.option("--config-file",
              default=default_config_file(),
              help="filename to store configuration information",
              type=click.Path(file_okay=True, writable=True),
              show_default=True)
@click.option("--eval", is_flag=True,
              help="emits only 'export AWS_PROFILE=<...>' so you can eval output")
def login(config_file, eval):
    if not config_exists(config_file):
        click.fail("Config not setup. Run scimma-aws setup first.")
        return
    config = Config.from_file(config_file)

    creds = get_aws_creds(config.username, config.password, config.entity_id)
    write_aws_credentials(config.profile_name, "", config.region, creds)
    expiration = creds["Expiration"]
    duration = humanize.naturaldelta(
        expiration - datetime.datetime.now(expiration.tzinfo))
    if eval:
        print(f"export AWS_PROFILE={config.profile_name}")
    else:
        click.echo(
            f"Done. Credentials will last for the next {duration}, expiring at {expiration}."
        )
        click.echo(
            f"Activate this by running 'export AWS_PROFILE={config.profile_name}'")


@dataclasses.dataclass
class Config:
    username: str
    password: str
    entity_id: str
    region: str
    profile_name: str

    def to_file(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        config_data = {
            "username": self.username,
            "password": self.password,
            "entity_id": self.entity_id,
            "region": self.region,
            "profile_name": self.profile_name,
        }
        with open(filepath, "w") as f:
            json.dump(config_data, f)
        os.chmod(filepath, 0o600)

    @classmethod
    def from_file(cls, filepath):
        data = json.load(open(filepath, "r"))
        return Config(**data)


def config_exists(filepath):
    return os.path.exists(filepath)


main.add_command(setup)
main.add_command(login)
