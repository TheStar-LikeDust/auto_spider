"""
CLI command: generate

Generate plan and steps template.
"""

import click

from ..template import generate_plan


@click.command('generate')
@click.argument('name')
@click.option('-d', '--description', default=None, help='Plan description')
@click.option('--single-file', is_flag=True, help='Generate single file with inline steps')
def cmd_generate(name, description, single_file):
    """Generate plan template.
    
    Creates plan_{NAME}.py and optionally steps_{NAME}/ package.
    """
    output_path = generate_plan(name, description, single_file)
    
    click.echo(f"Generated: {output_path}")
    if not single_file:
        click.echo(f"Generated: steps_{name}/")
    
    click.echo(f"\nCommands:")
    click.echo(f"  python plan_{name}.py")
    click.echo(f"  auto-spider run plan_{name}.py fetch_page --stage action")
