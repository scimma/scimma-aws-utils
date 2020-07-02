import click
import os.path
import json
import logging

from .awscreds import get_aws_creds
from .configs import Config, default_config_file, default_cache_dir
from .credentials import CredentialSet


logger = logging.getLogger(__name__)


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
            logger.debug("checking for credentials in cache at %s",
                         creds_cache_filename)
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
        raw_creds = get_aws_creds(
            config.username, config.password, config.entity_id, config.role_arn)
        creds = CredentialSet.from_aws_creds(raw_creds)
        if not cache_ignore:
            logger.debug("storing credentials in cache")
            creds.to_cache_file(creds_cache_filename)

    print(json.dumps(creds.to_aws_creds()))
