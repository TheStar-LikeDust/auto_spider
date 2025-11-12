"""
Process and thread scheduler for tasks.

Multi-process task execution with resource reuse.
"""

import json
from pathlib import Path
from typing import Callable, List, Any
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..step import Context, Task, generate_task_name
from .registry import execute_plan as _execute_plan
from .registry import execute_parse as _execute_parse
from .registry import execute_extract as _execute_extract
from .storage import create_output_dir, save_task_result, find_latest_output_dir, load_task_result
from ..logger import build_logger

_LOGGER = build_logger('scheduler')

# default process pool size
DEFAULT_MAX_WORKERS = 4


# Task and generate_task_name moved to step package


def _worker_process_tasks(args):
    """
    Worker function to process multiple tasks in one process.
    
    Reuses spider and initial resources across tasks.
    
    Args:
        args: Tuple of (task_batch, actions, spider_factory, initial_plan_factory, output_dir)
        
    Returns:
        List of result dicts
    """
    task_batch, actions, spider_factory, initial_plan_factory, output_dir = args
    results = []
    
    try:
        # initialize spider (reused across tasks)
        spider = spider_factory()
        spider.attach()
        
        # initialize plan resources (reused across tasks)
        initial = initial_plan_factory()
        
        # inject output_dir and save function
        if not isinstance(initial, dict):
            initial = {'resources': initial}
        
        initial['output_dir'] = output_dir
        initial['save_result'] = lambda task_name, result, ext='html': save_task_result(output_dir, task_name, result, ext)
        
        _LOGGER.info(f"Worker processing {len(task_batch)} tasks")
        _LOGGER.debug(f"Worker initialized - Spider: {type(spider).__name__}, Initial resources: {list(initial.keys())}")
        
        # process each task with new context
        for i, task in enumerate(task_batch):
            task_name = generate_task_name(task, i)
            
            try:
                _LOGGER.info(f"Executing task: {task_name}")
                _LOGGER.debug(f"Task details: {dict(task)}")
                
                # create new context for this task
                context = Context(spider=spider, task=task, initial=initial)
                _LOGGER.debug(f"Context created with keys: {list(context.keys())}")
                
                result = _execute_plan(actions, context=context)
                _LOGGER.debug(f"Action execution completed, result type: {type(result)}")
                
                # auto save result (save context['result'] directly as html)
                task_result = context.get('result')
                if task_result is not None:
                    save_task_result(output_dir, task_name, task_result, 'html')
                    _LOGGER.info(f"Task result saved: {task_name}.html ({len(str(task_result))} chars)")
                else:
                    _LOGGER.warning(f"No result found in context['result'] for task: {task_name}")
                
                # save context data as json for debugging (exclude large content)
                context_data = {k: v for k, v in context.items() if k not in ['spider', 'result']}  # exclude spider and result
                save_task_result(output_dir, task_name, context_data, 'json')
                _LOGGER.debug(f"Context data saved: {task_name}.json")
                
                results.append({
                    'task_name': task_name,
                    'success': True,
                    'result': result
                })
                
            except Exception as e:
                _LOGGER.error(f"Task failed: {task_name}, error: {e}")
                results.append({
                    'task_name': task_name,
                    'success': False,
                    'error': str(e)
                })
        
        # cleanup
        spider.detach()
        
    except Exception as e:
        _LOGGER.error(f"Worker failed: {e}")
        # return failed results for all tasks in batch
        for task in task_batch:
            results.append({
                'task_name': task.get('name', 'unnamed'),
                'success': False,
                'error': str(e)
            })
    
    return results


def _worker_thread_parse(args):
    """
    Worker function to process parse tasks in thread.
    
    Parse stage loads action results from files.
    
    Args:
        args: Tuple of (task, parses, initial_plan_factory, output_dir)
        
    Returns:
        Result dict
    """
    task, parses, initial_plan_factory, output_dir = args
    task_name = generate_task_name(task)
    
    try:
        # initialize plan resources
        initial = initial_plan_factory()
        
        if not isinstance(initial, dict):
            initial = {'resources': initial}
        
        initial['output_dir'] = output_dir
        initial['save_result'] = lambda name, result, ext='html': save_task_result(output_dir, name, result, ext)
        
        # auto load latest action result
        try:
            # find latest action output directory for same plan
            plan_name = output_dir.name.split('_parse_')[0]  # extract plan name from parse dir
            latest_action_dir = find_latest_output_dir(plan_name, 'action')
            _LOGGER.debug(f"Found latest action directory: {latest_action_dir}")
            
            # load action result
            action_result = load_task_result(latest_action_dir, task_name, 'html')
            if action_result is None:
                action_result = ""
                _LOGGER.warning(f"No action result file found for task: {task_name}")
            else:
                _LOGGER.debug(f"Loaded action result for {task_name}: {len(str(action_result))} chars")
        except Exception as e:
            _LOGGER.warning(f"Failed to load action result for {task_name}: {e}")
            action_result = ""
        
        _LOGGER.info(f"Parsing task: {task_name}")
        _LOGGER.debug(f"Loaded action result: {len(str(action_result))} chars")
        
        # create context with action result
        context = Context(task=task, initial=initial)
        context['result'] = action_result  # load action result as 'result'
        _LOGGER.debug(f"Parse context created with keys: {list(context.keys())}")
        
        result = _execute_parse(parses, context=context)
        _LOGGER.debug(f"Parse execution completed, result type: {type(result)}")
        
        # auto save parse result (save context['result'] directly as html by default)
        parse_result = context.get('result')
        if parse_result is not None:
            # save result as html (default) - could be parsed HTML or other content
            save_task_result(output_dir, task_name, parse_result, 'html')
            _LOGGER.info(f"Parse result saved: {task_name}.html")
        else:
            _LOGGER.warning(f"No result found in context['result'] for parse task: {task_name}")
        
        # save context data as json for debugging (exclude large content)
        context_data = {k: v for k, v in context.items() if k not in ['spider', 'result']}  # exclude spider and result
        save_task_result(output_dir, task_name, context_data, 'json')
        _LOGGER.debug(f"Parse context data saved: {task_name}.json")
        
        return {
            'task_name': task_name,
            'success': True,
            'result': result
        }
        
    except Exception as e:
        _LOGGER.error(f"Parse task failed: {task_name}, error: {e}")
        return {
            'task_name': task_name,
            'success': False,
            'error': str(e)
        }


def _worker_thread_extract(args):
    """
    Worker function to process extract tasks in thread.
    
    Extract stage loads parse results from files.
    
    Args:
        args: Tuple of (task, extracts, initial_plan_factory, output_dir)
        
    Returns:
        Result dict
    """
    task, extracts, initial_plan_factory, output_dir = args
    task_name = generate_task_name(task)
    
    try:
        # initialize plan resources
        initial = initial_plan_factory()
        
        if not isinstance(initial, dict):
            initial = {'resources': initial}
        
        initial['output_dir'] = output_dir
        initial['save_result'] = lambda name, result, ext='html': save_task_result(output_dir, name, result, ext)
        
        # auto load latest parse result
        try:
            # find latest parse output directory for same plan
            plan_name = output_dir.name.split('_extract_')[0]  # extract plan name from extract dir
            latest_parse_dir = find_latest_output_dir(plan_name, 'parse')
            _LOGGER.debug(f"Found latest parse directory: {latest_parse_dir}")
            
            # load parse result
            parse_result = load_task_result(latest_parse_dir, task_name, 'json')
            if parse_result is None:
                parse_result = {}
                _LOGGER.warning(f"No parse result file found for task: {task_name}")
            else:
                _LOGGER.debug(f"Loaded parse result for {task_name}: {parse_result}")
        except Exception as e:
            _LOGGER.warning(f"Failed to load parse result for {task_name}: {e}")
            parse_result = {}
        
        _LOGGER.info(f"Extracting task: {task_name}")
        _LOGGER.debug(f"Loaded parse result: {parse_result}")
        
        # create context with parse result
        context = Context(task=task, initial=initial)
        context['result'] = parse_result  # load parse result as 'result'
        _LOGGER.debug(f"Extract context created with keys: {list(context.keys())}")
        
        result = _execute_extract(extracts, context=context)
        _LOGGER.debug(f"Extract execution completed, result type: {type(result)}")
        
        # auto save extract result (save context['result'] directly as html by default)
        extract_result = context.get('result')
        if extract_result is not None:
            # save result as html (default) - could be extracted data or other content
            save_task_result(output_dir, task_name, extract_result, 'html')
            _LOGGER.info(f"Extract result saved: {task_name}.html")
        else:
            _LOGGER.warning(f"No result found in context['result'] for extract task: {task_name}")
        
        # save context data as json for debugging (exclude large content)
        context_data = {k: v for k, v in context.items() if k not in ['spider', 'result']}  # exclude spider and result
        save_task_result(output_dir, task_name, context_data, 'json')
        _LOGGER.debug(f"Extract context data saved: {task_name}.json")
        
        return {
            'task_name': task_name,
            'success': True,
            'result': result
        }
        
    except Exception as e:
        _LOGGER.error(f"Extract task failed: {task_name}, error: {e}")
        return {
            'task_name': task_name,
            'success': False,
            'error': str(e)
        }


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
    Run plan by executing tasks in different stages.
    
    Stages (mutually exclusive):
    - Action stage: multiprocessing + spider (download)
    - Parse stage: threading + file reading (parse HTML)
    - Extract stage: threading + database (save data)
    
    Args:
        initial_spider: Function that creates spider (required for action stage)
        initial_task: Function that returns task list (required)
        initial_plan: Function that returns initial resources object (required)
        actions: List of action names (action stage)
        parses: List of parse names (parse stage)
        extracts: List of extract names (extract stage)
        max_workers: Worker pool size (default: 4)
        plan_name: Plan name for output directory (default: None)
        output_dir: Custom output directory path (default: None, auto-created)
        
    Example:
        # Action stage
        run_plan(initial_spider, initial_task, initial_plan, 
                 actions=['fetch_page'], plan_name='baidu')
        
        # Parse stage
        run_plan(initial_task=initial_task, initial_plan=initial_plan,
                 parses=['parse_html'], plan_name='baidu')
        
        # Extract stage
        run_plan(initial_task=initial_task, initial_plan=initial_plan,
                 extracts=['save_to_db'], plan_name='baidu')
    """
    # check mutual exclusivity
    stage_count = sum([bool(actions), bool(parses), bool(extracts)])
    if stage_count == 0:
        raise ValueError("Must specify one of: actions, parses, or extracts")
    if stage_count > 1:
        raise ValueError("Can only specify one stage at a time: actions, parses, or extracts")
    
    if not initial_task or not initial_plan:
        raise ValueError("initial_task and initial_plan are required")
    tasks = initial_task()
    
    if not tasks:
        _LOGGER.warning("No tasks to execute")
        return
    
    # create output directory with stage
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        if actions:
            stage = 'action'
        elif parses:
            stage = 'parse'
        elif extracts:
            stage = 'extract'
        else:
            stage = 'action'  # fallback
        
        output_path = create_output_dir(plan_name, stage)
    
    # execute different stages
    if actions:
        # Action stage: multiprocessing + spider
        if not initial_spider:
            raise ValueError("initial_spider is required for action stage")
        
        _LOGGER.info(f"Running action stage: {len(tasks)} tasks, {max_workers} workers, actions: {actions}")
        _LOGGER.info(f"Output directory: {output_path}")
        
        # split tasks into batches for workers
        batch_size = (len(tasks) + max_workers - 1) // max_workers
        task_batches = [tasks[i:i + batch_size] for i in range(0, len(tasks), batch_size)]
        
        # prepare args for each worker
        worker_args = [(batch, actions, initial_spider, initial_plan, output_path) for batch in task_batches]
        
        # execute with process pool
        with Pool(processes=max_workers) as pool:
            batch_results = pool.map(_worker_process_tasks, worker_args)
        
        # flatten results
        for batch in batch_results:
            for result in batch:
                task_name = result.get('task_name')
                success = result.get('success')
                _LOGGER.info(f"Task {task_name}: {'SUCCESS' if success else 'FAILED'}")
    
    elif parses:
        # Parse stage: threading + file reading
        _LOGGER.info(f"Running parse stage: {len(tasks)} tasks, {max_workers} workers, parses: {parses}")
        _LOGGER.info(f"Output directory: {output_path}")
        
        # prepare args for each task
        worker_args = [(task, parses, initial_plan, output_path) for task in tasks]
        
        # execute with thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_worker_thread_parse, worker_args))
        
        # log results
        for result in results:
            task_name = result.get('task_name')
            success = result.get('success')
            _LOGGER.info(f"Parse {task_name}: {'SUCCESS' if success else 'FAILED'}")
    
    elif extracts:
        # Extract stage: threading + database
        _LOGGER.info(f"Running extract stage: {len(tasks)} tasks, {max_workers} workers, extracts: {extracts}")
        _LOGGER.info(f"Output directory: {output_path}")
        
        # prepare args for each task
        worker_args = [(task, extracts, initial_plan, output_path) for task in tasks]
        
        # execute with thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_worker_thread_extract, worker_args))
        
        # log results
        for result in results:
            task_name = result.get('task_name')
            success = result.get('success')
            _LOGGER.info(f"Extract {task_name}: {'SUCCESS' if success else 'FAILED'}")


def run_plan_from_file(plan_file: str, actions: List[str], max_workers: int = DEFAULT_MAX_WORKERS):
    """
    Load and run plan from Python file.
    
    Plan file must define 3 functions:
    - initial_spider()
    - initial_task()
    - initial_plan()
    
    Args:
        plan_file: Path to plan Python file
        actions: List of action names to execute
        max_workers: Process pool size (default: 4)
        
    Example:
        run_plan_from_file('plan_example.py', 
                          actions=['fetch_page', 'parse'], 
                          max_workers=4)
    """
    import importlib.util
    import sys
    from pathlib import Path
    
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
    
    if not initial_spider or not initial_task or not initial_plan:
        raise ValueError(
            f"Plan file must define: initial_spider, initial_task, initial_plan"
        )
    
    # run plan
    run_plan(initial_spider, initial_task, initial_plan, actions=actions, max_workers=max_workers)
