"""
auto_spider - Web scraping automation framework.

Workflow:
1. Create @active() actions in files
2. Load: tools.load_actions_from_directory()
3. Execute: core.execute_plan()
"""

# for developing actions
from auto_spider.actions import Context
from auto_spider.core import active, set_active

# for loading and execution
from auto_spider import tools, core, plan

__all__ = [
    'Context',
    'active', 
    'set_active',
    'tools',
    'core',
    'plan',
]
