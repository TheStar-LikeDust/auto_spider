"""
CLI main entry point using Click.

Usage:
    auto-spider init
    auto-spider generate myplan
    auto-spider run plan_myplan.py --action
"""

import click

from .cmd_init import cmd_init
from .cmd_generate import cmd_generate
from .cmd_run import cmd_run


@click.group()
@click.version_option(version='0.1.0', prog_name='auto-spider')
def cli():
    """Auto Spider - Web scraping automation framework."""
    pass


cli.add_command(cmd_init, name='init')
cli.add_command(cmd_generate, name='generate')
cli.add_command(cmd_run, name='run')

# aliases
cli.add_command(cmd_init, name='i')
cli.add_command(cmd_generate, name='gen')
cli.add_command(cmd_generate, name='g')
cli.add_command(cmd_run, name='r')


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
