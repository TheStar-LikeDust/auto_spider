"""
Step module for auto_spider.

Unified step concept and data structures.
All execution units are steps with different types.
"""

from .context import Context
from .task import Task, generate_task_name
from .task_result import TaskResult
from .task_data import TaskData

__all__ = [
    'Context',
    'Task',
    'generate_task_name',
    'TaskResult',
    'TaskData',
]
