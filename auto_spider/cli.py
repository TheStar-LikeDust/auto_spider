"""
DEPRECATED: This file is deprecated.

Use instead:
    python -m auto_spider          # Run CLI
    python -m auto_spider.cli      # Also works (this file)

The main CLI is now in auto_spider/__main__.py
"""

from .core.plan_cli import main

if __name__ == '__main__':
    main()
