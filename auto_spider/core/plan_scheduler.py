"""
Task scheduler for multi-worker execution.

Coordinate multiple workers for parallel task processing.

Execution Flow:
    - Validate parameters: Check initial_task and initial_plan
        - Action stage requires initial_spider
        - Parse/Extract stages do not need spider
    
    - Get tasks: Call initial_task() to get task list
    
    - Execute stages: Process each provided stage in order (actions → parses → extracts)
        - Determine stage type and step names
        - Create output directory for current stage
        - Log stage start information
        - Countdown 3 seconds
        - Start workers (multiprocessing for action, threading for parse/extract)
        - Worker handles execution and result loading

Stage Requirements:
    - Action: Creates tasks with spider, downloads data
    - Parse: Reads action results to build TaskResult, parses HTML
    - Extract: Reads action and parse results, saves to database
"""

from typing import Callable, List
from .stage import prepare_action_tasks, prepare_parse_tasks, prepare_extract_tasks
from .operations import setup_storage, setup_stage_storage, log_stage_start, setup_worker_storage
from .plan_worker import dispatch_workers
from .plan_config import load_plan_module
from ..tools.logger import build_logger

_LOGGER = build_logger('scheduler')

DEFAULT_MAX_WORKERS = 4


def _run_single_stage(
        stage_name: str,
        step_names: List[str],
        tasks: List,
        spider_factory: Callable,
        initial_factory: Callable,
        plan_name: str,
        max_workers: int,
        rate_limit: float,
        plan_config
):
    """
    Run a single stage.
    
    Args:
        stage_name: Stage name ('action', 'parse', 'extract')
        step_names: Step function names
        tasks: Prepared task list
        spider_factory: Spider factory (None for parse/extract)
        initial_factory: Initial resources factory
        plan_name: Plan name
        max_workers: Worker count
        rate_limit: Rate limit
        plan_config: PlanConfig instance
    """
    if not tasks:
        return

    setup_stage_storage(stage_name, plan_config)
    log_stage_start(stage_name, tasks, max_workers, step_names)
    setup_worker_storage(plan_config, stage_name)

    worker_type = 'process' if stage_name == 'action' else 'thread'
    dispatch_workers(
        tasks=tasks,
        stage_name=stage_name,
        step_names=step_names,
        spider_factory=spider_factory,
        initial_factory=initial_factory,
        plan_name=plan_name,
        plan_config=plan_config,
        worker_type=worker_type,
        max_workers=max_workers,
        rate_limit=rate_limit
    )

def run_plan(
        initial_spider: Callable,
        initial_task: Callable,
        initial_plan: Callable,
        plan_config,
        actions: List[str] = None,
        parses: List[str] = None,
        extracts: List[str] = None,
        retry_failed: bool = False
):
    """
    Run plan by executing tasks in stages.
    
    Args:
        initial_spider: Spider factory
        initial_task: Task factory
        initial_plan: Plan factory
        plan_config: PlanConfig instance
        actions: Action step names
        parses: Parse step names
        extracts: Extract step names
        retry_failed: Retry failed tasks (action stage only)
        
    Example:
        run_plan(initial_spider, initial_task, initial_plan, PLAN_CONFIG,
                 actions=['fetch_page'], parses=['parse_html'])
    """
    plan_name = plan_config.PLAN_NAME
    max_workers = plan_config.MAX_WORKERS
    rate_limit = plan_config.RATE_LIMIT
    output_dir = plan_config.OUTPUT_DIR

    setup_storage(plan_config, plan_name, output_dir)

    if actions:
        tasks = prepare_action_tasks(initial_task, retry_failed)
        _run_single_stage('action', actions, tasks, initial_spider, initial_plan,
                          plan_name, max_workers, rate_limit, plan_config)

    if parses:
        tasks = prepare_parse_tasks(plan_name)
        _run_single_stage('parse', parses, tasks, None, initial_plan,
                          plan_name, max_workers, rate_limit, plan_config)

    if extracts:
        tasks = prepare_extract_tasks(plan_name)
        _run_single_stage('extract', extracts, tasks, None, initial_plan,
                          plan_name, max_workers, rate_limit, plan_config)


def run_plan_with_file(plan_file: str):
    """
    Run plan by loading from plan file.
    
    Args:
        plan_file: Path to plan file
        
    Example:
        run_plan_with_file('plan_example.py')
    """
    plan_params = load_plan_module(plan_file)

    run_plan(
        initial_spider=plan_params['initial_spider'],
        initial_task=plan_params['initial_task'],
        initial_plan=plan_params['initial_plan'],
        plan_config=plan_params['plan_config'],
        actions=plan_params['actions'],
        parses=plan_params['parses'],
        extracts=plan_params['extracts']
    )
