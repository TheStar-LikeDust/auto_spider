"""
Actions module for auto_spider.

Simple function-based action system.
"""

from auto_spider.actions.context import Context
from auto_spider.actions._base_action import execute_pipeline

__all__ = [
    'Context',
    'execute_pipeline',
]
