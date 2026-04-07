"""
CLI command: generate

Generate plan and steps template.
"""

import click

from ..template import generate_plan


@click.command('generate')
@click.argument('name')
@click.option('-d', '--description', default=None, help='Plan description')
@click.option('--module', is_flag=True, help='Generate with separate steps package')
@click.option('--single-file', is_flag=True, hidden=True, help='Alias for default single file mode')
def cmd_generate(name, description, module, single_file):
    """Generate plan template.
    
    Creates {NAME}.py (default) or {NAME}.py + steps_{NAME}/ (--module).
    """
    use_single_file = not module
    output_path = generate_plan(name, description, use_single_file)
    
    click.echo(f"Generated: {output_path}")
    if module:
        click.echo(f"Generated: steps_{name}/")
    
    click.echo(f"\nCommands:")
    click.echo(f"  auto-spider run {name}.py --action")
