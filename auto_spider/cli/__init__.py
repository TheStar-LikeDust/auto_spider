"""
CLI package using Click.

Commands:
    init     - Initialize project with skills/docs
    generate - Generate plan template
    run      - Run plan file
"""

from .main import main, cli

__all__ = ['main', 'cli']
