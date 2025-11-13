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

import time
import importlib.util
import sys
from pathlib import Path
from typing import Callable, List
from .worker import start_workers
from .storage import create_stage_dir
from .stage import get_tasks_for_stage
from ..logger import build_logger

_LOGGER = build_logger('scheduler')

DEFAULT_MAX_WORKERS = 4


def log_stage_start(stage: str, tasks: List, max_workers: int, step_names: List[str], output_path: Path = None):
    """
    Log stage start information with countdown.
    
    Args:
        stage: Stage name
        tasks: Task list
        max_workers: Number of workers
        step_names: Step names to execute
        output_path: Output directory (None for extract stage)
    """
    _LOGGER.info(f"Running {stage} stage: {len(tasks)} tasks, {max_workers} workers, {stage}s: {step_names}")
    if output_path:
        _LOGGER.info(f"Output directory: {output_path}")
    _LOGGER.info("")
    
    for i in range(2, 0, -1):
        _LOGGER.info(f"Starting in {i}...")
        time.sleep(1)
    _LOGGER.info("Execution started!")
    _LOGGER.info("")


def run_plan(
        initial_spider: Callable = None,
        initial_task: Callable = None,
        initial_plan: Callable = None,
        actions: List[str] = None,
        parses: List[str] = None,
        extracts: List[str] = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
        plan_name: str = None,
        output_dir: str = None
):
    """
    Run plan by executing tasks in stages.
    
    Entry point for all three workflows:
    - Action: Crawl data with spider, creates tasks and downloads
    - Parse: Parse HTML, reads action results to build TaskResult
    - Extract: Save to database, reads both action and parse results
    
    Can execute single or multiple stages in sequence with unified management.
    Each stage has slight differences handled by this function.
    
    Args:
        initial_spider: Spider factory (required for action, None for parse/extract)
        initial_task: Task list factory (required)
        initial_plan: Resources factory (required)
        actions: Action step names (crawl data with spider)
        parses: Parse step names (parse HTML from action results)
        extracts: Extract step names (save data from action and parse results)
        max_workers: Worker pool size (default: 4)
        plan_name: Plan name for output directory
        output_dir: Custom output directory
        
    Example:
        # Action only: crawl data
        run_plan(initial_spider, initial_task, initial_plan, 
                 actions=['fetch_page'], plan_name='plan1')
        
        # Parse only: parse existing action results
        run_plan(initial_task=initial_task, initial_plan=initial_plan,
                 parses=['parse_html'], plan_name='plan1')
        
        # Full pipeline: action → parse → extract
        run_plan(initial_spider, initial_task, initial_plan,
                 actions=['fetch_page'],
                 parses=['parse_html'],
                 extracts=['save_to_db'],
                 plan_name='plan1')
    """
    if not initial_task or not initial_plan:
        raise ValueError("initial_task and initial_plan are required")

    # validate action stage requirements
    if actions and not initial_spider:
        raise ValueError("initial_spider is required for action stage")

    # execute action stage
    if actions:
        tasks = get_tasks_for_stage('action', initial_task=initial_task)
        output_path = Path(output_dir) if output_dir else create_stage_dir(plan_name, 'action')
        log_stage_start('action', tasks, max_workers, actions, output_path)
        start_workers(tasks, actions, initial_spider, initial_plan, output_path, 'action', max_workers)

    # execute parse stage
    if parses:
        tasks = get_tasks_for_stage('parse', plan_name=plan_name)
        output_path = Path(output_dir) if output_dir else create_stage_dir(plan_name, 'parse')
        log_stage_start('parse', tasks, max_workers, parses, output_path)
        start_workers(tasks, parses, None, initial_plan, output_path, 'parse', max_workers)

    # execute extract stage (no output directory needed)
    if extracts:
        tasks = get_tasks_for_stage('extract', plan_name=plan_name)
        output_path = None
        log_stage_start('extract', tasks, max_workers, extracts, output_path)
        start_workers(tasks, extracts, None, initial_plan, output_path, 'extract', max_workers)

    # TODO: Worker status checking


def run_plan_from_file(
        plan_file: str,
        stage: str = 'action',
        step_names: List[str] = None,
        max_workers: int = DEFAULT_MAX_WORKERS
):
    """
    Wrapper for run_plan that loads plan from template file.
    
    Reads plan template and quickly starts execution.
    
    Plan file must define:
    - initial_spider() (for action stage)
    - initial_task() (required)
    - initial_plan() (required)
    - Optional: ACTION_LIST, PARSE_LIST, EXTRACT_LIST
    
    Args:
        plan_file: Path to plan Python file
        stage: Stage to run ('action', 'parse', 'extract')
        step_names: Step names to execute (auto-reads from module if None)
        max_workers: Worker pool size (default: 4)
        
    Example:
        # Action stage
        run_plan_from_file('plan_example.py', stage='action', 
                          step_names=['fetch_page'], max_workers=4)
        
        # Auto-read from ACTION_LIST in module
        run_plan_from_file('plan_example.py', stage='action')
    """
    plan_path = Path(plan_file).resolve()

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_file}")

    # load module
    spec = importlib.util.spec_from_file_location("plan_module", plan_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load plan file: {plan_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["plan_module"] = module
    spec.loader.exec_module(module)

    # get 3 fixed functions
    initial_spider = getattr(module, 'initial_spider', None)
    initial_task = getattr(module, 'initial_task', None)
    initial_plan = getattr(module, 'initial_plan', None)

    if not initial_task or not initial_plan:
        raise ValueError("Plan file must define: initial_task, initial_plan")

    if stage == 'action' and not initial_spider:
        raise ValueError("Plan file must define initial_spider for action stage")

    # get step names from module if not provided
    if step_names is None:
        if stage == 'action':
            step_names = getattr(module, 'ACTION_LIST', [])
        elif stage == 'parse':
            step_names = getattr(module, 'PARSE_LIST', [])
        else:
            step_names = getattr(module, 'EXTRACT_LIST', [])

    # prepare kwargs
    kwargs = {
        'initial_task': initial_task,
        'initial_plan': initial_plan,
        'max_workers': max_workers,
        'plan_name': plan_path.stem
    }

    if stage == 'action':
        kwargs['initial_spider'] = initial_spider
        kwargs['actions'] = step_names
    elif stage == 'parse':
        kwargs['parses'] = step_names
    else:
        kwargs['extracts'] = step_names

    # run plan
    run_plan(**kwargs)
