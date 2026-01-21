"""
Fixed operations for scheduler execution.

Simple, side-effect-free functions for common operations.
"""

import time
from pathlib import Path
from typing import Callable, Optional, List
from ..storage import configure, initial_storage
from ..tools.logger import build_logger

_LOGGER = build_logger('operations')


def log_separator(title: str = None):
    """Log a separator line for visual clarity."""
    if title:
        _LOGGER.info(f"{'=' * 20} {title} {'=' * 20}")
    else:
        _LOGGER.info('=' * 50)


def setup_storage(plan_config=None, plan_name: str = None, output_dir: str = None):
    """
    Configure storage backend.
    
    Args:
        plan_config: PlanConfig instance (takes precedence)
        plan_name: Plan name for default output directory
        output_dir: Custom output directory
    """
    if plan_config:
        _output_dir = plan_config.OUTPUT_DIR if output_dir is None else output_dir
        if not _output_dir and plan_name:
            _output_dir = f"steps_{plan_name}/output"
            plan_config.OUTPUT_DIR = _output_dir
        configure(plan_config)
    elif output_dir:
        configure(base_dir=output_dir)
    elif plan_name:
        _output_dir = f"steps_{plan_name}/output"
        configure(base_dir=_output_dir)


def create_stage_storage(stage: str) -> Path:
    """
    Create storage directory for stage.
    
    Args:
        stage: Stage name ('action', 'parse', 'extract')
        
    Returns:
        Path to stage output directory
    """
    return initial_storage(stage)


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


def setup_worker_storage(plan_config, stage_name: str):
    """
    Setup storage for multiprocess workers.
    
    Args:
        plan_config: PlanConfig instance with _stage_output_dir
        stage_name: Stage name
    """
    if plan_config and plan_config._stage_output_dir:
        from ..storage import configure
        configure(stage_dir=plan_config._stage_output_dir, stage=stage_name)


def setup_stage_storage(stage_name: str, plan_config):
    """
    Create and configure storage for stage.
    
    Args:
        stage_name: Stage name ('action', 'parse', 'extract')
        plan_config: PlanConfig instance
    """
    if stage_name in ('action', 'parse'):
        output_path = create_stage_storage(stage_name)
        if plan_config:
            plan_config._stage_output_dir = str(output_path)
        _LOGGER.info(f"Output directory: {output_path}")
    else:
        _LOGGER.info("Extract stage: no output directory")


def log_stage_start(stage_name: str, tasks: List, max_workers: int, step_names: List[str]):
    """
    Log stage start information.
    
    Args:
        stage_name: Stage name
        tasks: Task list
        max_workers: Number of workers
        step_names: Step names to execute
    """
    log_separator(f"{stage_name.upper()} STAGE")
    _LOGGER.info(f"{len(tasks)} tasks, {max_workers} workers, steps: {step_names}")
