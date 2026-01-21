"""
auto_spider - Web scraping automation framework.

Workflow:
1. Create @action(), @parse(), @extract() functions in files
2. Import: import your action modules to register steps
3. Execute: core.run_plan() with stage-specific parameters
"""

__version__ = "0.1.0"

# for developing steps
from .step import Context, Task
from .core import active, action, parse, extract

# for runtime execution
from . import core, tools, components

__all__ = [
    # step data structures
    'Context', 'Task',
    # step decorators
    'active', 'action', 'parse', 'extract',
    # modules
    'core', 'tools', 'components', 'step',
]
