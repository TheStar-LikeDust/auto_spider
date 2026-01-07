"""File-based storage backend."""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

_base_dir = 'output'
_use_timestamp = True
_stage_dirs = {}

def configure(config=None, base_dir=None, use_timestamp=None, stage_dir=None, stage=None):
    global _base_dir, _use_timestamp
    if config is not None:
        _base_dir = getattr(config, 'OUTPUT_DIR', None) or 'output'
        _use_timestamp = getattr(config, 'STORAGE_TIMESTAMP', True)
    else:
        if base_dir is not None:
            _base_dir = base_dir
        if use_timestamp is not None:
            _use_timestamp = use_timestamp
    # for multiprocess workers: directly set stage directory
    if stage_dir and stage:
        _stage_dirs[stage] = Path(stage_dir)

def initial_storage(stage: str) -> Path:
    base_path = Path(_base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    if _use_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stage_dir_name = f"{stage}_{timestamp}"
    else:
        stage_dir_name = stage
    stage_path = base_path / stage_dir_name
    if not _use_timestamp and stage_path.exists():
        shutil.rmtree(stage_path)
    stage_path.mkdir(parents=True, exist_ok=True)
    _stage_dirs[stage] = stage_path
    return stage_path

def _find_latest_stage_dir(stage: str) -> Path:
    base_path = Path(_base_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Base directory not found: {base_path}")
    fixed_dir = base_path / stage
    if fixed_dir.exists():
        return fixed_dir
    pattern = f"{stage}_*"
    matching_dirs = list(base_path.glob(pattern))
    if not matching_dirs:
        raise FileNotFoundError(f"No stage directories found for {stage}")
    matching_dirs.sort(key=lambda x: x.name, reverse=True)
    return matching_dirs[0]

def _save_file(output_dir: Path, filename: str, content, is_json: bool = False):
    file_path = output_dir / filename
    if is_json:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

def _load_directory(output_dir: Path) -> List[dict]:
    if not output_dir.exists():
        return []
    task_files = sorted(output_dir.glob('*_task.json'))
    tasks = []
    for task_file in task_files:
        task_name = task_file.stem.replace('_task', '')
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
        action_file = output_dir / f"{task_name}_action.json"
        action = None
        if action_file.exists():
            with open(action_file, 'r', encoding='utf-8') as f:
                action = json.load(f)
        parse_file = output_dir / f"{task_name}_parse.json"
        parse = None
        if parse_file.exists():
            with open(parse_file, 'r', encoding='utf-8') as f:
                parse = json.load(f)
        content_file = output_dir / f"{task_name}.html"
        content = None
        if content_file.exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        tasks.append({'task': task, 'action': action, 'parse': parse, 'content': content})
    return tasks

def save_action_result(task_name: str, task: dict, action: dict, content: str):
    if 'action' in _stage_dirs:
        output_dir = _stage_dirs['action']
    else:
        output_dir = _find_latest_stage_dir('action')
    _save_file(output_dir, f'{task_name}_task.json', task, is_json=True)
    _save_file(output_dir, f'{task_name}_action.json', action, is_json=True)
    _save_file(output_dir, f'{task_name}.html', content, is_json=False)

def load_action_result() -> List[dict]:
    if 'action' in _stage_dirs:
        output_dir = _stage_dirs['action']
    else:
        output_dir = _find_latest_stage_dir('action')
    return _load_directory(output_dir)

def save_parse_result(task_name: str, task: dict, action: dict, parse: dict, content: str):
    if 'parse' in _stage_dirs:
        output_dir = _stage_dirs['parse']
    else:
        output_dir = _find_latest_stage_dir('parse')
    _save_file(output_dir, f'{task_name}_task.json', task, is_json=True)
    _save_file(output_dir, f'{task_name}_action.json', action, is_json=True)
    _save_file(output_dir, f'{task_name}_parse.json', parse, is_json=True)
    _save_file(output_dir, f'{task_name}.html', content, is_json=False)

def load_parse_result() -> List[dict]:
    if 'parse' in _stage_dirs:
        output_dir = _stage_dirs['parse']
    else:
        output_dir = _find_latest_stage_dir('parse')
    return _load_directory(output_dir)

def save_failed_task(task_name: str, task: dict, error: str, stage: str = 'action', worker_id: int = None):
    """
    Save failed task information.
    
    Args:
        task_name: Task name (e.g., 'task1')
        task: Original task dict
        error: Error message string
        stage: Stage name (default 'action')
        worker_id: Worker ID that failed
    """
    try:
        if stage in _stage_dirs:
            output_dir = _stage_dirs[stage]
        else:
            output_dir = _find_latest_stage_dir(stage)
        
        failed_data = {
            'task': task,
            'error': error,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if worker_id is not None:
            failed_data['worker_id'] = worker_id
        
        _save_file(output_dir, f'{task_name}_failed.json', failed_data, is_json=True)
    except Exception:
        # let it fail: if we can't save failed task, just ignore
        pass

def load_failed_tasks(stage: str = 'action') -> List[dict]:
    """
    Load all failed tasks for a stage.
    
    Args:
        stage: Stage name (default 'action')
        
    Returns:
        List of failed task dicts with 'task', 'error', 'timestamp', 'worker_id'
    """
    if stage in _stage_dirs:
        output_dir = _stage_dirs[stage]
    else:
        try:
            output_dir = _find_latest_stage_dir(stage)
        except FileNotFoundError:
            return []
    
    if not output_dir.exists():
        return []
    
    failed_files = sorted(output_dir.glob('*_failed.json'))
    failed_tasks = []
    for failed_file in failed_files:
        with open(failed_file, 'r', encoding='utf-8') as f:
            failed_tasks.append(json.load(f))
    
    return failed_tasks
