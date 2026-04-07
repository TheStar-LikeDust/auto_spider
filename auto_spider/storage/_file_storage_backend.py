"""
File-based storage backend.

File naming uses task index as prefix for ordered storage:
    001_task.json, 001_action.json, 001.html
    002_task.json, 002_action.json, 002.html

Even if task3 finishes before task2, files are named by original index.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

_base_dir = 'output'
_use_timestamp = True
_stage_dirs = {}


def setup(plan_config):
    """Configure file paths from plan_config and create base directory."""
    global _base_dir, _use_timestamp, _stage_dirs
    _base_dir, _use_timestamp = _resolve_config(plan_config)
    _stage_dirs = {}
    Path(_base_dir).mkdir(parents=True, exist_ok=True)


def process_result(result: dict):
    """Save result to file storage. Uses result['stage'] for directory routing."""
    stage = result.get('stage', 'unknown')
    output_dir = _get_or_create_stage_dir(stage)
    prefix = _make_prefix(f"task{result.get('index', 'unknown')}")

    if result.get('error'):
        _save_failed_result(output_dir, prefix, result)
    else:
        _save_success_result(output_dir, prefix, stage, result)


def _resolve_config(plan_config):
    """Extract base_dir and use_timestamp from plan_config."""
    output_dir = getattr(plan_config, 'OUTPUT_DIR', None) or 'output'
    plan_name = getattr(plan_config, 'PLAN_NAME', None)
    use_timestamp = getattr(plan_config, 'STORAGE_TIMESTAMP', True)
    base_dir = str(Path(output_dir) / plan_name) if plan_name else output_dir
    return base_dir, use_timestamp


def _save_failed_result(output_dir: Path, prefix: str, result: dict):
    """Write failed task metadata to disk."""
    failed_data = {
        'task': result.get('task', {}),
        'error': result['error'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    _save_file(output_dir, f'{prefix}_failed.json', failed_data, is_json=True)


def _save_success_result(output_dir: Path, prefix: str, stage: str, result: dict):
    """Write task, stage result, action result, and HTML content to disk."""
    _save_file(output_dir, f'{prefix}_task.json', result.get('task', {}), is_json=True)

    stage_result = result.get('result')
    if stage_result is not None:
        _save_file(output_dir, f'{prefix}_{stage}.json', stage_result, is_json=True)

    action_result = result.get('action_result')
    if action_result is not None:
        _save_file(output_dir, f'{prefix}_action.json', action_result, is_json=True)

    content = result.get('content')
    if content:
        _save_file(output_dir, f'{prefix}.html', content)


def _get_or_create_stage_dir(stage: str) -> Path:
    """Get cached stage dir or create a new one."""
    if stage in _stage_dirs:
        return _stage_dirs[stage]
    base_path = Path(_base_dir)
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


def _get_stage_dir(stage: str) -> Path:
    """Get stage directory: use cached path or find latest."""
    if stage in _stage_dirs:
        return _stage_dirs[stage]
    return _find_latest_stage_dir(stage)


def _find_latest_stage_dir(stage: str) -> Path:
    base_path = Path(_base_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Base directory not found: {base_path}")
    fixed_dir = base_path / stage
    if fixed_dir.exists():
        return fixed_dir
    pattern = f"{stage}_*"
    matching_dirs = sorted(base_path.glob(pattern), key=lambda x: x.name, reverse=True)
    if not matching_dirs:
        raise FileNotFoundError(f"No stage directories found for {stage}")
    return matching_dirs[0]


def _save_file(output_dir: Path, filename: str, content, is_json: bool = False):
    file_path = output_dir / filename
    if is_json:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(content) if content else '')


def _make_prefix(task_name: str) -> str:
    """Extract numeric index from task_name (e.g. 'task3' -> '003')."""
    num = ''.join(c for c in task_name if c.isdigit())
    return num.zfill(3) if num else task_name


def _load_directory(output_dir: Path) -> List[dict]:
    """Load all task results from a stage directory, sorted by filename prefix."""
    if not output_dir.exists():
        return []
    task_files = sorted(output_dir.glob('*_task.json'))
    results = []
    for task_file in task_files:
        prefix = task_file.stem.replace('_task', '')
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)

        action = _load_json(output_dir / f"{prefix}_action.json")
        parse = _load_json(output_dir / f"{prefix}_parse.json")
        content = _load_text(output_dir / f"{prefix}.html")
        results.append({'task': task, 'action': action, 'parse': parse, 'content': content})
    return results


def _load_json(path: Path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _load_text(path: Path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


# ── save / load for each stage ──

def load_action_result() -> List[dict]:
    return _load_directory(_get_stage_dir('action'))


def load_parse_result() -> List[dict]:
    return _load_directory(_get_stage_dir('parse'))


def load_failed_tasks(stage: str = 'action') -> List[dict]:
    """Load all failed tasks for a stage."""
    try:
        output_dir = _get_stage_dir(stage)
    except FileNotFoundError:
        return []
    if not output_dir.exists():
        return []
    failed_files = sorted(output_dir.glob('*_failed.json'))
    return [json.load(open(f, 'r', encoding='utf-8')) for f in failed_files]
