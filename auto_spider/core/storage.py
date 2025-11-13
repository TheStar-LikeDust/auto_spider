"""
Result storage and loading.

Save and load task results to/from output directory.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List

# default output directory
DEFAULT_OUTPUT_DIR = 'output'


def ensure_output_dir() -> Path:
    """
    Create and return output directory (can be called multiple times).
    
    Returns:
        Path to output directory
        
    Example:
        ensure_output_dir()  # output/
    """
    output_path = Path(DEFAULT_OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def ensure_plan_dir(plan_name: str) -> Path:
    """
    Create and return plan directory (can be called multiple times).
    
    Args:
        plan_name: Plan name
        
    Returns:
        Path to plan directory
        
    Example:
        ensure_plan_dir('baidu')  # output/baidu/
    """
    plan_path = ensure_output_dir() / plan_name
    plan_path.mkdir(parents=True, exist_ok=True)
    return plan_path


def create_stage_dir(plan_name: str, stage: str) -> Path:
    """
    Create timestamped stage directory for current execution.
    
    Args:
        plan_name: Plan name
        stage: Stage name ('action', 'parse')
        
    Returns:
        Path to stage directory
        
    Example:
        create_stage_dir('baidu', 'action')  # output/baidu/action_20241111_143000/
        create_stage_dir('baidu', 'parse')   # output/baidu/parse_20241111_143001/
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    stage_dir_name = f"{stage}_{timestamp}"
    
    stage_path = ensure_plan_dir(plan_name) / stage_dir_name
    stage_path.mkdir(parents=True, exist_ok=True)
    
    return stage_path


def save_task_result(output_dir: Path, task_name: str, result: Any, file_extension: str = 'html'):
    """
    Save task result to file (raw content from context['result']).
    
    Args:
        output_dir: Output directory path
        task_name: Task name (used as filename)
        result: Result data to save (raw content)
        file_extension: File extension (default: 'html')
        
    Example:
        save_task_result(output_dir, 'task1', '<html>...</html>', 'html')
        # saves to: output_dir/task1.html
        
        save_task_result(output_dir, 'task1', {'title': 'xxx'}, 'json')
        # saves to: output_dir/task1.json
    """
    result_file = output_dir / f"{task_name}.{file_extension}"
    
    if result is None:
        result = ""
    
    try:
        if file_extension.lower() == 'json':
            # JSON format
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            # Raw content (html, txt, etc.)
            if isinstance(result, (dict, list)):
                # If result is dict/list but extension is not json, convert to JSON string
                content = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                # Raw string content
                content = str(result)
            
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        # fallback: save error info as json
        error_file = output_dir / f"{task_name}_error.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump({
                'task_name': task_name,
                'result': str(result),
                'error': str(e)
            }, f, ensure_ascii=False, indent=2)


def find_latest_stage_dir(plan_name: str, stage: str) -> Path:
    """
    Find the latest stage directory for a plan.
    
    Args:
        plan_name: Plan name
        stage: Stage name ('action', 'parse')
        
    Returns:
        Path to latest stage directory
        
    Example:
        find_latest_stage_dir('baidu', 'action')  # output/baidu/action_20241111_143000/
    """
    plan_dir = ensure_output_dir() / plan_name
    if not plan_dir.exists():
        raise FileNotFoundError(f"Plan directory not found: {plan_dir}")
    
    # find all matching stage directories
    pattern = f"{stage}_*"
    matching_dirs = list(plan_dir.glob(pattern))
    
    if not matching_dirs:
        raise FileNotFoundError(f"No stage directories found for {plan_name}/{stage}")
    
    # sort by timestamp (directory name contains timestamp)
    matching_dirs.sort(key=lambda x: x.name, reverse=True)
    
    return matching_dirs[0]


def load_directory(output_dir: Path) -> list:
    """
    Load directory and return list of task data.
    
    File naming:
        - task1_task.json: original task
        - task1_action.json: action result
        - task1_parse.json: parse result
        - task1.html: content
    
    Args:
        output_dir: Output directory path
        
    Returns:
        List of dict with task, action, parse, content fields
        
    Example:
        tasks = load_directory(action_dir)
        for task_data in tasks:
            original_task = task_data['task']
            action_result = task_data['action']
            content = task_data['content']
    """
    if not output_dir.exists():
        return []
    
    task_map = {}
    
    # step 1: scan all files and group by base task name
    for file_path in output_dir.iterdir():
        if not file_path.is_file():
            continue
            
        filename = file_path.stem
        extension = file_path.suffix[1:]
        
        # parse filename: task1_task, task1_action, task1_parse, or task1
        if '_' in filename:
            # task1_task, task1_action, or task1_parse
            base_name, stage_suffix = filename.rsplit('_', 1)
        else:
            # task1.html
            base_name = filename
            stage_suffix = 'content'
        
        try:
            # step 2: load file content
            if extension.lower() == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            
            # step 3: group by base task name
            if base_name not in task_map:
                task_map[base_name] = {
                    'task': {},
                    'action': {},
                    'parse': {},
                    'content': ''
                }
            
            if extension.lower() == 'html':
                task_map[base_name]['content'] = file_content
            elif extension.lower() == 'json':
                # store by stage suffix
                if stage_suffix in ('task', 'action', 'parse'):
                    task_map[base_name][stage_suffix] = file_content
                
        except Exception:
            continue
    
    # step 4: create result list with all fields
    tasks = []
    for base_name in sorted(task_map.keys()):
        task_data = task_map[base_name]
        
        # need at least task file
        if not task_data['task']:
            continue
        
        # return dict with all fields
        tasks.append({
            'task': task_data['task'],
            'action': task_data['action'],
            'parse': task_data['parse'],
            'content': task_data['content']
        })
    
    return tasks
