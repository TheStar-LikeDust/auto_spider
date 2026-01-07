"""
Stage manager for different execution stages.

Get tasks for stages and save stage results.
"""

from pathlib import Path
from typing import Callable, List
from ..storage import load_action_result, load_parse_result, save_action_result, save_parse_result, load_failed_tasks
from ..step import Context
from ..tools.logger import build_logger

_LOGGER = build_logger('stage')


def get_tasks_for_stage(stage: str, plan_name: str = None, initial_task: Callable = None) -> List:
    """
    Unified task getter for all stages with structured context keys.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        plan_name: Plan name (required for parse/extract)
        initial_task: Task factory (required for action)
        
    Returns:
        List of tasks with proper context structure:
        
        Action stage: returns Task objects directly
        
        Parse stage: returns dict with keys:
            - input: action result dict
            - content: action HTML content
            - task: original task
            
        Extract stage: returns dict with keys:
            - input: parse result dict
            - content: action HTML content  
            - task: original task
            - parse_input: action result dict
    """
    # action stage: return raw tasks
    if stage == 'action':
        return initial_task()
    
    # parse stage: load action results
    elif stage == 'parse':
        loaded_tasks = load_action_result()
        
        tasks = []
        for loaded in loaded_tasks:
            # loaded has: task, action, parse, content
            tasks.append({
                'task': loaded['task'],            # original task
                'input': loaded['action'],         # action result (as parse input)
                'content': loaded['content'],      # HTML
                'action_result': loaded['action']  # for saving
            })
        return tasks
    
    # extract stage: load parse results
    elif stage == 'extract':
        loaded_tasks = load_parse_result()
        
        tasks = []
        for loaded in loaded_tasks:
            # loaded has: task, action, parse, content
            tasks.append({
                'task': loaded['task'],            # original task
                'input': loaded['parse'],          # parse result (as extract input)
                'content': loaded['content'],      # HTML
                'action_result': loaded['action'], # action result
                'parse_result': loaded['parse']    # parse result
            })
        return tasks
    
    else:
        raise ValueError(f"Unknown stage: {stage}")


def setup_context_for_stage(stage: str, context: Context, task_dict: dict):
    """
    Setup context keys for specific stage.
    
    Unified context setup logic for all stages:
        - action: input = task
        - parse: input = action result, adds action_result
        - extract: input = parse result, adds action_result and parse_result
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        context: Context object to setup
        task_dict: Task data dict from get_tasks_for_stage or initial_task
    """
    if stage == 'action':
        # action stage: input is the original task
        context['input'] = task_dict
        
    elif stage == 'parse':
        # parse stage: input is action result
        context['input'] = task_dict.get('input', {})           # action result
        context['content'] = task_dict.get('content', '')       # HTML
        context['action_result'] = task_dict.get('action_result', {}) # for saving
        
    elif stage == 'extract':
        # extract stage: input is parse result
        context['input'] = task_dict.get('input', {})           # parse result
        context['content'] = task_dict.get('content', '')       # HTML
        context['action_result'] = task_dict.get('action_result', {})
        context['parse_result'] = task_dict.get('parse_result', {})


def save_stage_result(stage: str, context: Context, plan_name: str, task_name: str):
    """
    Save stage result by reading from context keys.
    
    Saves all relevant data from context for each stage:
        - action: saves task, action_result, content
        - parse: saves task, action_result, parse_result, content
        - extract: does not save (side-effect only)
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        context: Context object with results
        plan_name: Plan name
        task_name: Task name (e.g., 'task1')
    """
    if stage == 'action':
        task = dict(context.task)
        action_result = context.get('result', {})
        content = context.get('content', '')
        save_action_result(task_name, task, action_result, content)
    
    elif stage == 'parse':
        task = dict(context.task)
        action_result = context.get('action_result', {})
        parse_result = context.get('result', {})
        content = context.get('content', '')
        save_parse_result(task_name, task, action_result, parse_result, content)
    
    elif stage == 'extract':
        # extract stage: read only, no save
        pass


def prepare_action_tasks(initial_task: Callable, retry_failed: bool = False) -> List:
    """
    Prepare tasks for action stage.
    
    Args:
        initial_task: Task factory function (required unless retry_failed=True)
        retry_failed: Retry failed tasks
        
    Returns:
        List of tasks
    """
    if retry_failed:
        failed_tasks = load_failed_tasks('action')
        tasks = [item['task'] for item in failed_tasks]
        if not tasks:
            _LOGGER.info("No failed tasks found, action stage will be skipped")
            return []
        _LOGGER.info(f"Retrying {len(tasks)} failed tasks")
        return tasks
    else:
        if not initial_task:
            raise ValueError("initial_task is required for action stage (unless retry_failed=True)")
        tasks = initial_task()
        if not tasks:
            _LOGGER.info("No tasks from initial_task, action stage will be skipped")
        return tasks


def prepare_parse_tasks(plan_name: str) -> List:
    """
    Prepare tasks for parse stage.
    
    Args:
        plan_name: Plan name for loading results
        
    Returns:
        List of tasks
    """
    tasks = get_tasks_for_stage('parse', plan_name=plan_name)
    if not tasks:
        _LOGGER.info("No tasks from parse stage, parse stage will be skipped")
    return tasks


def prepare_extract_tasks(plan_name: str) -> List:
    """
    Prepare tasks for extract stage.
    
    Args:
        plan_name: Plan name for loading results
        
    Returns:
        List of tasks
    """
    tasks = get_tasks_for_stage('extract', plan_name=plan_name)
    if not tasks:
        _LOGGER.info("No tasks from extract stage, extract stage will be skipped")
    return tasks
