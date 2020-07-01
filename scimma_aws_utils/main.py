import dataclasses
import datetime
import json
import logging
import os
import os.path
import pathlib
import sys

import click
import humanize

from .awscreds import get_aws_creds, write_aws_config


logger = logging.getLogger(__name__)


def default_config_dir() -> pathlib.Path:
    if os.getenv("XDG_CONFIG_HOME"):
        config_root = pathlib.Path(os.getenv("XDG_CONFIG_HOME"))
    else:
        config_root = pathlib.Path.home() / ".config"
    return config_root / "scimma-aws"


def default_config_file() -> pathlib.Path:
    return default_config_dir() / "config"

def default_cache_dir() -> pathlib.Path:
    return default_config_dir() / "cache"

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
        "AWS credential profile name to use", type=str, default="default")
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
    write_aws_config(conf.profile_name, conf.region, sys.argv[0])
    click.echo(f"AWS configuration has been saved.")


@click.command()
@click.option("--config-file",
              default=default_config_file(),
              help="filename to store configuration information",
              type=click.Path(file_okay=True, writable=True),
              show_default=True)
@click.option("--cache-ignore", is_flag=True,
              help="ignore any cached credentials, and dont store in cache")
@click.option("--cache-force-refresh", is_flag=True,
              help="force an update of cached credentials")
@click.option("--cache-dir", default=default_cache_dir(),
              help="directory to cache credentials in")
def login(config_file, cache_ignore, cache_force_refresh, cache_dir):
    if not os.path.exists(config_file):
        raise click.UsageError("Config not setup. Run scimma-aws setup first.")
    config = Config.from_file(config_file)

    creds = None
    creds_cache_filename = cache_dir / config.profile_name
    if not cache_ignore and not cache_force_refresh:
        try:
            logger.debug("checking for credentials in cache at %s", creds_cache_filename)
            creds = CredentialSet.from_cache_file(creds_cache_filename)
        except FileNotFoundError:
            logger.debug("cached credentials not found")
            pass

    if creds is not None:
        # Cached credentials found. Check if they're still live.
        logger.debug("cached credentials found, checking expiration")
        if creds.expired():
            # No good.
            logger.debug("credentials are expired")
            creds = None

    if creds is None:
        logger.debug("refreshing credentials")
        raw_creds = get_aws_creds(config.username, config.password, config.entity_id)
        creds = CredentialSet.from_aws_creds(raw_creds)
        if not cache_ignore:
            logger.debug("storing credentials in cache")
            creds.to_cache_file(creds_cache_filename)

    print(json.dumps(creds.to_aws_creds()))


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


@dataclasses.dataclass
class CredentialSet:
    version: int
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime.datetime

    def to_aws_creds(self):
        return {
            "Version": self.version,
            "AccessKeyId": self.access_key_id,
            "SecretAccessKey": self.secret_access_key,
            "SessionToken": self.session_token,
            "Expiration": self.expiration.isoformat()
        }

    def to_cache_file(self, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        json_data = self.to_aws_creds()
        with open(filename, "w") as f:
            json.dump(json_data, f)

    @classmethod
    def from_aws_creds(cls, creds):
        try:
            expiration = datetime.datetime.fromisoformat(creds["Expiration"])
        except:
            expiration = creds["Expiration"]
        return CredentialSet(
            version=1,
            access_key_id=creds["AccessKeyId"],
            secret_access_key=creds["SecretAccessKey"],
            session_token=creds["SessionToken"],
            expiration=expiration,
        )

    @classmethod
    def from_cache_file(cls, filename):
        with open(filename, "r") as f:
            json_data = json.load(f)
            return CredentialSet.from_aws_creds(json_data)

    def expired(self, margin=datetime.timedelta(minutes=10)):
        return datetime.datetime.now(self.expiration.tzinfo) > (self.expiration - margin)


main.add_command(setup)
main.add_command(login)
