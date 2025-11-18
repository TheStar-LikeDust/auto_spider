"""
Stage manager for different execution stages.

Get tasks for stages and save stage results.
"""

from pathlib import Path
from typing import Callable, List
from ..storage import find_latest_stage_dir, load_directory, save_task_result
from ..step import Context


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
        action_dir = find_latest_stage_dir(plan_name, 'action')
        loaded_tasks = load_directory(action_dir)
        
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
        parse_dir = find_latest_stage_dir(plan_name, 'parse')
        loaded_tasks = load_directory(parse_dir)
        
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


def save_stage_result(stage: str, context: Context, output_dir: Path, task_name: str):
    """
    Save stage result by reading from context keys.
    
    Saves all relevant data from context for each stage:
        - action: saves task, action_result, content
        - parse: saves task, action_result, parse_result, content
        - extract: does not save (side-effect only)
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        context: Context object with results
        output_dir: Output directory path
        task_name: Task name (e.g., 'task1')
    """
    if stage == 'action':
        # save original task
        task = context.task
        save_task_result(output_dir, f'{task_name}_task', dict(task), 'json')
        
        # save action result
        action_result = context.get('result', {})
        save_task_result(output_dir, f'{task_name}_action', action_result, 'json')
        
        # save content
        content = context.get('content')
        if content is not None:
            save_task_result(output_dir, task_name, content, 'html')
    
    elif stage == 'parse':
        # save original task
        task = context.task
        save_task_result(output_dir, f'{task_name}_task', dict(task), 'json')
        
        # save action result (from context)
        action_result = context.get('action_result', {})
        save_task_result(output_dir, f'{task_name}_action', action_result, 'json')
        
        # save parse result
        parse_result = context.get('result', {})
        save_task_result(output_dir, f'{task_name}_parse', parse_result, 'json')
        
        # save content
        content = context.get('content')
        if content is not None:
            save_task_result(output_dir, task_name, content, 'html')
    
    elif stage == 'extract':
        # extract stage: read only, no save
        pass
