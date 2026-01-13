"""
Step module for auto_spider.

Unified step concept and data structures.
All execution units are steps with different types.

Type hierarchy:
    ActionInput (Task)
      ↓
    ParseInput (action_input + result + content)
      ↓
    ExtractInput (parse_input + result)
"""

from ._context import Context
from ._action_input import Task, ActionInput
from ._parse_input import ParseInput
from ._extract_input import ExtractInput
from .step_executor import execute_steps

__all__ = [
    'Context',
    'Task',
    'ActionInput',
    'ParseInput',
    'ExtractInput',
    'execute_steps',
]
