"""
Dynamic loader for actions and plans.

Scan directories and load all @action, @parse, @extract functions.
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List


def load_actions_from_file(filepath: str):
    """
    Load actions from a single Python file.
    
    Args:
        filepath: Path to Python file
    """
    filepath = Path(filepath)
    
    if not filepath.exists() or filepath.suffix != '.py':
        return
    
    # load module
    module_name = filepath.stem
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if not spec or not spec.loader:
        return
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    try:
        spec.loader.exec_module(module)
    except Exception:
        return
    
    # scan for @action/@parse/@extract functions (already auto-registered by decorator)
    # nothing to do here, decorator handles registration


def load_actions_from_directory(directory: str, recursive: bool = True):
    """
    Load all actions from directory.
    
    Args:
        directory: Directory path
        recursive: Scan subdirectories
    """
    directory = Path(directory)
    
    if not directory.exists() or not directory.is_dir():
        return
    
    # find all .py files
    py_files = directory.rglob('*.py') if recursive else directory.glob('*.py')
    
    # filter and load
    for filepath in py_files:
        if filepath.name != '__init__.py' and '__pycache__' not in str(filepath):
            load_actions_from_file(str(filepath))


def load_actions_from_directories(directories: List[str], recursive: bool = True):
    """
    Load actions from multiple directories.
    
    Args:
        directories: List of directory paths
        recursive: Scan subdirectories
    """
    for directory in directories:
        load_actions_from_directory(directory, recursive=recursive)


def auto_load_actions(base_path: str = None):
    """
    Auto load actions from default locations.
    
    Args:
        base_path: Base path (default: current directory)
    """
    if base_path is None:
        base_path = os.getcwd()
    
    base_path = Path(base_path)
    
    # default locations
    default_locations = [
        base_path / 'actions',
        base_path / 'auto_spider' / 'actions',
    ]
    
    for location in default_locations:
        if location.exists():
            load_actions_from_directory(str(location), recursive=True)
