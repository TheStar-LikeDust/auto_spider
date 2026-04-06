"""
CLI command: init

Initialize project with skills and docs for Claude Code.
"""

import shutil
from pathlib import Path

import click


def _get_package_data_dir():
    """Get the package data directory (where skills/docs are stored)."""
    return Path(__file__).parent.parent


@click.command('init')
@click.argument('target', default='.', required=False)
@click.option('--skills-only', is_flag=True, help='Only copy skills, skip docs')
@click.option('--docs-only', is_flag=True, help='Only copy docs, skip skills')
def cmd_init(target, skills_only, docs_only):
    """Initialize project with skills and docs for Claude Code.
    
    Copies skills to .claude/skills and docs to docs/ in TARGET directory.
    """
    target = Path(target).resolve()
    pkg_dir = _get_package_data_dir()
    
    skills = not docs_only
    docs = not skills_only
    copied = []
    
    if skills:
        src = pkg_dir / 'skills'
        dst = target / '.claude' / 'skills'
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            copied.append(f'.claude/skills/ ({len(list(dst.iterdir()))} skills)')
    
    if docs:
        src = pkg_dir / 'docs'
        dst = target / 'docs'
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            file_count = sum(1 for _ in dst.rglob('*') if _.is_file())
            copied.append(f'docs/ ({file_count} files)')
    
    if copied:
        click.echo(f"Initialized in: {target}")
        for item in copied:
            click.echo(f"  - {item}")
    else:
        click.echo("Nothing to copy (skills/docs not found in package)")
