"""
Stage manager for different execution stages.

Get tasks for stages and save stage results.
"""

from pathlib import Path
from typing import Callable, List
from .storage import find_latest_output_dir, load_task_result, list_task_results, save_task_result
from ..step import Context


def get_tasks_for_stage(stage: str, plan_name: str = None, initial_task: Callable = None) -> List:
    """
    Unified task getter for all stages.
    
    Load tasks with previous stage results for parse/extract.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        plan_name: Plan name (required for parse/extract)
        initial_task: Task factory (required for action)
        
    Returns:
        List of tasks with loaded previous results
    """
    # step action
    # run initial_task() from plan
    if stage == 'action':
        return initial_task()
    
    # step parse
    # load action content html file to content key
    # load action result json file to result key
    elif stage == 'parse':
        action_dir = find_latest_output_dir(plan_name, 'action')
        task_names = list_task_results(action_dir)
        
        tasks = []
        for task_name in task_names:
            content = load_task_result(action_dir, task_name, 'html') or ""
            result = load_task_result(action_dir, task_name, 'json') or {}
            
            tasks.append({
                'name': task_name,
                'content': content,     # action content (html)
                'result': result        # action result (json)
            })
        return tasks
    
    # step extract
    # load action content html file to content key
    # load action result json file to result key
    # load parse data json file to data key
    elif stage == 'extract':
        action_dir = find_latest_output_dir(plan_name, 'action')
        parse_dir = find_latest_output_dir(plan_name, 'parse')
        task_names = list_task_results(parse_dir)
        
        tasks = []
        for task_name in task_names:
            content = load_task_result(action_dir, task_name, 'html') or ""
            result = load_task_result(action_dir, task_name, 'json') or {}
            data = load_task_result(parse_dir, task_name, 'json') or {}
            
            tasks.append({
                'name': task_name,
                'content': content,     # action content (html)
                'result': result,       # action result (json)
                'data': data            # parse data (json)
            })
        return tasks
    
    else:
        raise ValueError(f"Unknown stage: {stage}")


def save_stage_result(stage: str, context: Context, output_dir: Path, task_name: str):
    """
    Save stage result based on stage type.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        context: Context object with results
        output_dir: Output directory path
        task_name: Task name
    """
    # step action
    # save content key to html (optional)
    # save result key to json
    if stage == 'action':
        # save content to html (optional)
        content = context.get('content')
        if content is not None:
            save_task_result(output_dir, task_name, content, 'html')
        
        # save result to json
        result = context.get('result')
        if result is not None:
            save_task_result(output_dir, task_name, result, 'json')
    
    # step parse
    # save data key to json
    elif stage == 'parse':
        data = context.get('data')
        if data is not None:
            save_task_result(output_dir, task_name, data, 'json')
    
    # step extract
    # nothing to save
    else:
        raise ValueError(f"Unknown stage: {stage}")
