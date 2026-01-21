"""
Duplicate detection utilities.

Function-based duplicate checker with cross-process compatible data structure.

Data structure is simple dict with set, can be extended to support:
- File-based storage for cross-process
- Redis-based storage for cross-machine
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path


def create_duplicate_checker(storage_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Create duplicate checker counter.
    
    Returns dict with serializable data structure for cross-process compatibility.
    
    Args:
        storage_file: Optional file path for persistent storage (cross-process)
        
    Returns:
        Duplicate checker dict
        
    Example:
        # in-memory (single process)
        checker = create_duplicate_checker()
        
        # file-based (cross-process)
        checker = create_duplicate_checker('seen_tasks.json')
    """
    checker = {
        'seen_hashes': set(),
        'count': 0,
        'storage_file': storage_file
    }
    
    # load from file if exists
    if storage_file and Path(storage_file).exists():
        try:
            with open(storage_file, 'r') as f:
                data = json.load(f)
                checker['seen_hashes'] = set(data.get('seen_hashes', []))
                checker['count'] = data.get('count', 0)
        except Exception:
            pass
    
    return checker


def _save_checker(checker: Dict[str, Any]):
    """Save checker to file if storage_file is set."""
    storage_file = checker.get('storage_file')
    if not storage_file:
        return
    
    try:
        data = {
            'seen_hashes': list(checker['seen_hashes']),
            'count': checker['count']
        }
        with open(storage_file, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass


def is_duplicate(checker: Dict[str, Any], task: dict) -> bool:
    """
    Check if task is duplicate.
    
    Args:
        checker: Duplicate checker from create_duplicate_checker()
        task: Task dict to check
        
    Returns:
        True if duplicate, False if new
        
    Example:
        checker = create_duplicate_checker()
        task1 = Task(url='http://a.com')
        
        is_duplicate(checker, task1)  # False (first time)
        is_duplicate(checker, task1)  # True (duplicate)
    """
    task_hash = hash(task)
    
    if task_hash in checker['seen_hashes']:
        return True
    
    checker['seen_hashes'].add(task_hash)
    checker['count'] += 1
    
    # save to file if cross-process storage enabled
    _save_checker(checker)
    
    return False


def get_duplicate_count(checker: Dict[str, Any]) -> int:
    """
    Get number of unique tasks seen.
    
    Args:
        checker: Duplicate checker
        
    Returns:
        Count of unique tasks
    """
    return checker['count']


def reset_duplicate_checker(checker: Dict[str, Any]):
    """
    Reset duplicate checker to empty state.
    
    Args:
        checker: Duplicate checker to reset
    """
    checker['seen_hashes'].clear()
    checker['count'] = 0
    _save_checker(checker)
