"""
Result storage and loading.

Save and load task results to/from output directory.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# default output directory
DEFAULT_OUTPUT_DIR = 'output'


def create_output_dir(plan_name: str = None, stage: str = 'action') -> Path:
    """
    Create timestamped output directory for specific stage.
    
    Args:
        plan_name: Plan name (default: 'plan')
        stage: Stage name ('action', 'parse', 'extract')
        
    Returns:
        Path to created directory
        
    Example:
        create_output_dir('baidu', 'action')  # output/baidu_action_20241111_143000/
        create_output_dir('baidu', 'parse')   # output/baidu_parse_20241111_143000/
    """
    if not plan_name:
        plan_name = 'plan'
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dir_name = f"{plan_name}_{stage}_{timestamp}"
    
    output_path = Path(DEFAULT_OUTPUT_DIR) / dir_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    return output_path


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


def find_latest_output_dir(plan_name: str, stage: str) -> Path:
    """
    Find the latest output directory for a plan and stage.
    
    Args:
        plan_name: Plan name
        stage: Stage name ('action', 'parse', 'extract')
        
    Returns:
        Path to latest output directory
        
    Example:
        find_latest_output_dir('baidu', 'action')  # output/baidu_action_20241111_143000/
    """
    output_base = Path(DEFAULT_OUTPUT_DIR)
    if not output_base.exists():
        raise FileNotFoundError(f"Output directory {output_base} not found")
    
    # find all matching directories
    pattern = f"{plan_name}_{stage}_*"
    matching_dirs = list(output_base.glob(pattern))
    
    if not matching_dirs:
        raise FileNotFoundError(f"No output directories found for {plan_name}_{stage}")
    
    # sort by timestamp (directory name contains timestamp)
    matching_dirs.sort(key=lambda x: x.name, reverse=True)
    
    return matching_dirs[0]


def load_task_result(output_dir: Path, task_name: str, file_extension: str = 'html') -> Any:
    """
    Load task result from file.
    
    Args:
        output_dir: Output directory path
        task_name: Task name
        file_extension: File extension to load (default: 'html')
        
    Returns:
        Loaded result data (string for html/txt, dict for json)
        
    Example:
        html = load_task_result(output_dir, 'task1', 'html')  # returns string
        data = load_task_result(output_dir, 'task1', 'json')  # returns dict
    """
    result_file = output_dir / f"{task_name}.{file_extension}"
    
    if not result_file.exists():
        return None
    
    try:
        if file_extension.lower() == 'json':
            # JSON format
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Raw content (html, txt, etc.)
            with open(result_file, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception:
        return None


def list_task_results(output_dir: Path) -> list:
    """
    List all task result files in output directory.
    
    Args:
        output_dir: Output directory path
        
    Returns:
        List of task names
    """
    if not output_dir.exists():
        return []
    
    return [f.stem for f in output_dir.glob('*.json')]
