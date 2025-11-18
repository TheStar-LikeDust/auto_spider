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
from typing import Callable, List, Optional
from multiprocessing import Process, JoinableQueue, Barrier
from threading import Thread, Barrier as ThreadBarrier
from queue import Queue
from .stage import get_tasks_for_stage
from ..logger import build_logger

_LOGGER = build_logger('scheduler')

DEFAULT_MAX_WORKERS = 4


def dispatch_tasks(
    tasks: List,
    worker_func: Callable,
    worker_type: str = 'process',
    max_workers: int = 4,
    rate_limit: Optional[float] = None,
    **worker_kwargs
):
    """
    Dispatch tasks to workers using JoinableQueue.
    
    Uses barriers and task_done for synchronization:
    1. Ready barrier: all workers complete preparation
    2. Start barrier: main process countdown complete, workers start execution
    3. Queue.join(): wait for all tasks (including dynamically added) to complete
    
    Supports incremental crawling where tasks can generate new tasks.
    Rate limiting is achieved by a dedicated feeder thread that controls task feeding speed.
    
    Args:
        tasks: Task list
        worker_func: Worker function to execute each task
        worker_type: 'process' or 'thread'
        max_workers: Number of concurrent workers
        rate_limit: Delay between tasks in seconds (None = no limit, e.g., 1.0 = 1 task/sec, 0.5 = 2 tasks/sec)
        **worker_kwargs: Additional arguments passed to worker_func
    """
    from .worker import SHUTDOWN_SIGNAL
    
    if worker_type == 'process':
        worker_class = Process
        ready_barrier = Barrier(max_workers + 1)
        start_barrier = Barrier(max_workers + 1)
        task_queue = JoinableQueue()
    elif worker_type == 'thread':
        worker_class = Thread
        ready_barrier = ThreadBarrier(max_workers + 1)
        start_barrier = ThreadBarrier(max_workers + 1)
        task_queue = Queue()
    else:
        raise ValueError(f"Unknown worker_type: {worker_type}")
    
    # feeder thread for rate-limited task feeding
    feeder_thread = None
    if rate_limit:
        task_buffer = [(i, task) for i, task in enumerate(tasks)]
        
        def feed_tasks():
            """Feed tasks to queue at controlled rate"""
            for i, task_item in enumerate(task_buffer):
                task_queue.put(task_item)
                if i < len(task_buffer) - 1:
                    time.sleep(rate_limit)
            _LOGGER.debug(f"Feeder completed: {len(task_buffer)} tasks fed")
        
        feeder_thread = Thread(target=feed_tasks)
        feeder_thread.start()
        _LOGGER.info(f"Rate limiter enabled: {rate_limit}s delay between tasks")
    else:
        # no rate limit: put all tasks immediately
        for i, task in enumerate(tasks):
            task_queue.put((i, task))
    
    # start workers
    workers = [
        worker_class(target=worker_func, args=(worker_id, task_queue, ready_barrier, start_barrier), kwargs=worker_kwargs)
        for worker_id in range(max_workers)
    ]
    
    for worker in workers:
        worker.start()
    
    # wait for all workers to complete preparation
    _LOGGER.info(f"Waiting for {max_workers} workers to complete preparation...")
    ready_barrier.wait()
    
    # countdown in main process
    _LOGGER.info("All workers ready!")
    _LOGGER.info("")
    for i in range(2, 0, -1):
        _LOGGER.info(f"Starting execution in {i}...")
        time.sleep(1)
    _LOGGER.info("Workers executing!")
    
    # release start barrier, workers begin execution
    start_barrier.wait()
    
    # wait for feeder to complete (if rate limiting enabled)
    if feeder_thread:
        _LOGGER.info("Waiting for task feeder to complete...")
        feeder_thread.join()
        _LOGGER.info("All tasks have been fed to queue")
    
    # wait for all tasks to complete (including dynamically added tasks)
    _LOGGER.info("Waiting for all tasks to complete...")
    task_queue.join()
    _LOGGER.info("All tasks completed! ready to exit...")
    time.sleep(1)
    
    # send stop signal to workers
    for _ in range(max_workers):
        task_queue.put(SHUTDOWN_SIGNAL)
    
    for worker in workers:
        worker.join()
    
    _LOGGER.debug(f"All workers exited: {max_workers} {worker_type}s")


def start_workers(
    tasks: List,
    steps: List[str],
    spider_factory: Callable,
    initial_factory: Callable,
    plan_name: str,
    stage: str,
    max_workers: int,
    rate_limit: Optional[float] = None,
    reload_event: Optional = None,
    config: Optional = None
):
    """
    Start workers for any stage.
    
    Uses Process for action stage, Thread for parse/extract stages.
    Workers fetch tasks from Queue until empty.
    
    Args:
        tasks: List of tasks
        steps: List of step function names
        spider_factory: Spider factory function (None for parse/extract)
        initial_factory: Plan factory function
        plan_name: Plan name for storage
        stage: Stage name ('action', 'parse', 'extract')
        max_workers: Number of concurrent workers
        rate_limit: Delay between tasks in seconds (None = no limit, e.g., 1.0 = 1 task/sec, 0.5 = 2 tasks/sec)
        reload_event: Optional event to signal module reload (for daemon mode)
        config: PlanConfig instance to pass to workers
    """
    from .worker import run_worker
    
    worker_type = 'process' if stage == 'action' else 'thread'
    
    dispatch_tasks(
        tasks=tasks,
        worker_func=run_worker,
        worker_type=worker_type,
        max_workers=max_workers,
        rate_limit=rate_limit,
        steps=steps,
        spider_factory=spider_factory,
        initial_factory=initial_factory,
        plan_name=plan_name,
        stage=stage,
        reload_event=reload_event,
        config=config
    )


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
        config = None,
        max_workers: int = None,
        rate_limit: float = None,
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
        config: PlanConfig instance (recommended, overrides individual params)
        max_workers: Worker pool size (default: 4, overridden by config)
        rate_limit: Delay between tasks in seconds (None = no limit, overridden by config)
        plan_name: Plan name for output directory (overridden by config)
        output_dir: Custom output directory (overridden by config)
        
    Example:
        # Using config object (recommended)
        PLAN_CONFIG = PlanConfig()
        PLAN_CONFIG.PLAN_NAME = 'myplan'
        PLAN_CONFIG.MAX_WORKERS = 2
        PLAN_CONFIG.RATE_LIMIT = 1.0
        
        run_plan(initial_spider, initial_task, initial_plan, 
                 actions=['fetch_page'], config=PLAN_CONFIG)
        
        # Legacy: individual params
        run_plan(initial_spider, initial_task, initial_plan, 
                 actions=['fetch_page'], plan_name='plan1', max_workers=2)
        
        # Full pipeline
        run_plan(initial_spider, initial_task, initial_plan,
                 actions=['fetch_page'], parses=['parse_html'],
                 extracts=['save_to_db'], config=PLAN_CONFIG)
    """
    if not initial_task or not initial_plan:
        raise ValueError("initial_task and initial_plan are required")

    # validate action stage requirements
    if actions and not initial_spider:
        raise ValueError("initial_spider is required for action stage")

    # extract config values (config takes precedence)
    if config:
        _plan_name = config.PLAN_NAME if plan_name is None else plan_name
        _max_workers = config.MAX_WORKERS if max_workers is None else max_workers
        _rate_limit = config.RATE_LIMIT if rate_limit is None else rate_limit
        _output_dir = config.OUTPUT_DIR if output_dir is None else output_dir
    else:
        _plan_name = plan_name
        _max_workers = max_workers if max_workers is not None else DEFAULT_MAX_WORKERS
        _rate_limit = rate_limit
        _output_dir = output_dir
    
    # configure storage
    from ..storage import configure, initial_storage as init_storage
    
    if config:
        configure(config)
    elif _output_dir:
        configure(base_dir=_output_dir)

    # execute action stage
    if actions:
        tasks = get_tasks_for_stage('action', initial_task=initial_task)
        output_path = init_storage('action')
        log_stage_start('action', tasks, _max_workers, actions, output_path)
        start_workers(tasks, actions, initial_spider, initial_plan, _plan_name, 'action', _max_workers, rate_limit=_rate_limit, config=config)

    # execute parse stage
    if parses:
        tasks = get_tasks_for_stage('parse', plan_name=_plan_name)
        output_path = init_storage('parse')
        log_stage_start('parse', tasks, _max_workers, parses, output_path)
        start_workers(tasks, parses, None, initial_plan, _plan_name, 'parse', _max_workers, rate_limit=_rate_limit, config=config)

    # execute extract stage (no storage needed)
    if extracts:
        tasks = get_tasks_for_stage('extract', plan_name=_plan_name)
        output_path = None
        log_stage_start('extract', tasks, _max_workers, extracts, output_path)
        start_workers(tasks, extracts, None, initial_plan, _plan_name, 'extract', _max_workers, rate_limit=_rate_limit, config=config)

    # TODO: Worker status checking


def run_plan_from_file(
        plan_file: str,
        stage: str = 'action',
        step_names: List[str] = None,
        max_workers: int = None,
        rate_limit: float = None,
        config = None
):
    """
    Wrapper for run_plan that loads plan from template file.
    
    Reads plan template and quickly starts execution.
    
    Plan file must define:
    - initial_spider() (for action stage)
    - initial_task() (required)
    - initial_plan() (required)
    - Optional: PLAN_CONFIG (PlanConfig instance)
    - Optional: STAGES dict or ACTION_LIST, PARSE_LIST, EXTRACT_LIST
    
    Args:
        plan_file: Path to plan Python file
        stage: Stage to run ('action', 'parse', 'extract')
        step_names: Step names to execute (auto-reads from module if None)
        max_workers: Worker pool size (overrides config)
        rate_limit: Delay between tasks (overrides config)
        config: PlanConfig instance (overrides module config)
        
    Example:
        # Using module's config
        run_plan_from_file('plan_example.py', stage='action')
        
        # Override with custom config
        my_config = PlanConfig(plan_name='custom', max_workers=8)
        run_plan_from_file('plan_example.py', stage='action', config=my_config)
        
        # Override individual params
        run_plan_from_file('plan_example.py', stage='action', max_workers=4)
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

    # get config from module or use provided config
    if config is None:
        # try to load PLAN_CONFIG from module
        module_config = getattr(module, 'PLAN_CONFIG', None)
        if module_config:
            config = module_config
    
    # get step names from module if not provided
    if step_names is None:
        # try STAGES dict first
        stages_dict = getattr(module, 'STAGES', None)
        if stages_dict:
            step_names = stages_dict.get(stage, [])
        else:
            # fallback to individual lists
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
        'config': config,
        'max_workers': max_workers,
        'rate_limit': rate_limit,
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
