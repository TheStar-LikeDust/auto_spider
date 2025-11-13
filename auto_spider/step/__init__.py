"""
Step module for auto_spider.

Unified step concept and data structures.
All execution units are steps with different types.
"""

from .context import Context
from .schemas import (
    Task,
    ActionInput,
    ActionResult,
    ParseResult,
    ParseInput,
    ExtractInput,
    generate_task_name,
    TaskResult,
    TaskData,
)
from .runner import execute_steps

__all__ = [
    'Context',
    'Task',
    'ActionInput',
    'ActionResult',
    'ParseResult',
    'ParseInput',
    'ExtractInput',
    'generate_task_name',
    'TaskResult',
    'TaskData',
    'execute_steps',
]
