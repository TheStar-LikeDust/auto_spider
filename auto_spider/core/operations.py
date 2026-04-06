"""
Fixed operations for scheduler execution.

Simple, side-effect-free functions for common operations.
"""

from typing import Callable, List
from ..tools.logger import build_logger

_LOGGER = build_logger('operations')


def log_separator(title: str = None):
    """Log a separator line for visual clarity."""
    if title:
        _LOGGER.info(f"{'=' * 20} {title} {'=' * 20}")
    else:
        _LOGGER.info('=' * 50)


def initialize_spider(spider_factory: Callable):
    """
    Initialize and attach spider.
    
    Args:
        spider_factory: Spider factory function
        
    Returns:
        Initialized spider instance
    """
    spider = spider_factory()
    spider.attach()
    _LOGGER.debug(f"Spider initialized: {type(spider).__name__}")
    return spider


def cleanup_spider(spider):
    """
    Detach and cleanup spider.
    
    Args:
        spider: Spider instance to cleanup
    """
    if spider:
        spider.detach()
        _LOGGER.debug("Spider cleaned up")


def initialize_resources(initial_factory: Callable) -> dict:
    """
    Initialize plan resources.
    
    Args:
        initial_factory: Plan factory function
        
    Returns:
        Resources dict
    """
    initial = initial_factory()
    if not isinstance(initial, dict):
        initial = {'resources': initial}
    return initial


def log_stage_ready(tasks: List, max_workers: int):
    """Log task count and worker count before dispatch."""
    _LOGGER.info(f"{len(tasks)} tasks, {max_workers} workers")
