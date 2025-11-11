"""
auto_spider - Web scraping automation framework.

Workflow:
1. Create @action(), @parse(), @extract() functions in files
2. Load: core.load_actions_from_directory() (optional)
3. Execute: core.run_plan() with stage-specific parameters
"""

# for developing actions
from .actions import Context
from .core import active, action, parse, extract, set_active

# for runtime execution
from . import core, tools, components

__all__ = [
    'Context',
    'active',
    'action',
    'parse',
    'extract',
    'set_active',
    'core',
    'tools',
    'components',
]
