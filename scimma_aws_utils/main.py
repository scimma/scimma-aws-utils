import logging

import click

from .cmd_setup import setup
from .cmd_login import login

logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", is_flag=True)
@click.option("--debug", is_flag=True)
def main(verbose, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)
    pass


main.add_command(setup)
main.add_command(login)
