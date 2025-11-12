"""
auto_spider - Web scraping automation framework.

Workflow:
1. Create @action(), @parse(), @extract() functions in files
2. Load: core.load_actions_from_directory() (optional)
3. Execute: core.run_plan() with stage-specific parameters
"""

# for developing steps
from .step import Context, Task, TaskResult, TaskData, generate_task_name
from .core import active, action, parse, extract, set_active

# for runtime execution
from . import core, tools, components

__all__ = [
    # step data structures
    'Context', 'Task', 'TaskResult', 'TaskData', 'generate_task_name',
    # step decorators
    'active', 'action', 'parse', 'extract', 'set_active',
    # modules
    'core', 'tools', 'components', 'step',
]
