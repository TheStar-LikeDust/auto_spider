"""
Shared testing utilities

Provides basic file operations with smart paths:
- data_input: Git-tracked standard inputs (supports nested folders)
- data_input_local: User-modified inputs (overrides data_input, not tracked)
- data_output: Auto-generated outputs with timestamps

Auto-detects caller module for organized file structure
Recursively searches subdirectories for flexible file organization

File Naming Convention:
- Example files: example_{feature}.py
- Function name: {feature}_main()
- Input data: data_input/**/example_{feature}.json (recursive search)
- Local input: data_input_local/**/example_{feature}.json (recursive search)
- Output: data_output/example_{feature}_{timestamp}.json

Test Data Convention:
- Input files are .json (git tracked, empty values)
- Local files are .json (git ignored, actual values)
- All JSON files use 2-space indentation
- Keep test data minimal and focused
- Files can be organized in subdirectories (e.g., studio/, api/)
- If multiple same-name files exist, uses most recently modified
"""

import argparse
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple


# Module level anchor to tests directory
TESTS_ROOT = Path(__file__).parent
INPUT_DIR = TESTS_ROOT / "data_input"
INPUT_LOCAL_DIR = TESTS_ROOT / "data_input_local"
OUTPUT_DIR = TESTS_ROOT / "data_output"

# Module level argument cache
_parsed_args = None


def _ensure_directories():
    """Create required directories with .gitkeep on module import"""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Add .gitkeep to track empty directories
    gitkeep_input = INPUT_DIR / ".gitkeep"
    if not gitkeep_input.exists():
        gitkeep_input.touch()


# Auto-initialize directories when module is imported
_ensure_directories()


def _get_cli_args() -> argparse.Namespace:
    """
    Get parsed CLI arguments (cached)
    
    Returns parsed arguments with:
    - input_data: JSON string input
    - output: Output filename
    """
    global _parsed_args
    if _parsed_args is None:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--input-data", type=str, default=None)
        parser.add_argument("--output", type=str, default=None)
        _parsed_args, _ = parser.parse_known_args()
    return _parsed_args


def _get_caller_info() -> str:
    """
    Get caller module name from call stack
    
    Returns:
        module_name e.g., "example_action_studio_login"
    """
    frame = inspect.currentframe()
    
    # Walk up the stack to find first frame outside test_tools.py
    current_file = Path(__file__).resolve()
    while frame:
        frame = frame.f_back
        if frame:
            caller_file = frame.f_globals.get("__file__", "")
            caller_path = Path(caller_file).resolve()
            
            # Return first caller outside test_tools.py
            if caller_path != current_file:
                return caller_path.stem
    
    return "unknown"


def _get_input_path(filename: str) -> Path:
    """
    Get input file path with input_local override support
    Recursively searches through subdirectories
    
    Priority:
    1. tests/data_input_local/**/{module}.json (recursive)
    2. tests/data_input/**/{module}.json (recursive)
    """
    module_name = _get_caller_info()
    
    # Search in data_input_local (recursive)
    local_matches = list(INPUT_LOCAL_DIR.glob(f"**/{module_name}.json"))
    if local_matches:
        return local_matches[0] if len(local_matches) == 1 else max(local_matches, key=lambda p: p.stat().st_mtime)
    
    # Search in data_input (recursive)
    standard_matches = list(INPUT_DIR.glob(f"**/{module_name}.json"))
    if standard_matches:
        return standard_matches[0] if len(standard_matches) == 1 else max(standard_matches, key=lambda p: p.stat().st_mtime)
    
    # Fallback to root level path
    return INPUT_DIR / f"{module_name}.json"


def _get_output_path(filename: str) -> Path:
    """
    Generate output file path with timestamp
    
    Format: tests/data_output/{module}_{timestamp}.json
    """
    module_name = _get_caller_info()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    base_name = Path(filename).stem
    ext = Path(filename).suffix or ".json"
    
    output_filename = f"{module_name}_{timestamp}{ext}"
    return OUTPUT_DIR / output_filename


def load(filename: str = "data.json", input_data_path: str = None) -> Any:
    """
    Load JSON with priority:
    1. tests/data_input_local/**/{module}.json (recursive search)
    2. tests/data_input/**/{module}.json (recursive search)
    3. --input-data CLI argument (JSON string)
    4. Error if none found
    
    Recursively searches through all subdirectories, allowing flexible file organization.
    If multiple matches found, uses the most recently modified file.
    
    Args:
        filename: Not used, kept for compatibility
        input_data_path: Manual override path (absolute or relative to TESTS_ROOT)
    """
    if input_data_path:
        filepath = Path(input_data_path) if Path(input_data_path).is_absolute() else TESTS_ROOT / input_data_path
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    module_name = _get_caller_info()
    
    # Search in data_input_local (recursive)
    local_matches = list(INPUT_LOCAL_DIR.glob(f"**/{module_name}.json"))
    if local_matches:
        filepath = local_matches[0] if len(local_matches) == 1 else max(local_matches, key=lambda p: p.stat().st_mtime)
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Search in data_input (recursive)
    standard_matches = list(INPUT_DIR.glob(f"**/{module_name}.json"))
    if standard_matches:
        filepath = standard_matches[0] if len(standard_matches) == 1 else max(standard_matches, key=lambda p: p.stat().st_mtime)
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback to CLI argument
    args = _get_cli_args()
    if args.input_data:
        return json.loads(args.input_data)
    
    raise FileNotFoundError(
        f"No input found for '{module_name}.json' in:\n"
        f"  - {INPUT_LOCAL_DIR}/** (recursive)\n"
        f"  - {INPUT_DIR}/** (recursive)\n"
        f"  - --input-data CLI argument"
    )


def save(data: Any, filename: str = None, save_data_path: str = None) -> None:
    """
    Save JSON to tests/data_output/ with auto-generated name
    Uses --output CLI argument if provided, otherwise defaults to module name
    
    Args:
        data: Data to save
        filename: Base filename for auto-generated path (default: None, uses --output or module name)
        save_data_path: Manual override path (absolute or relative to TESTS_ROOT)
    """
    if save_data_path:
        filepath = Path(save_data_path) if Path(save_data_path).is_absolute() else TESTS_ROOT / save_data_path
    else:
        if filename is None:
            args = _get_cli_args()
            if args.output:
                filename = args.output
            else:
                filename = _get_caller_info()
        
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        filepath = _get_output_path(filename)
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_output(pattern: str = None, latest: bool = True) -> Any:
    """
    Load JSON from tests/data_output/
    
    Args:
        pattern: Module name pattern (default: auto-detect from caller)
        latest: Load latest file if multiple matches (default: True)
    
    Returns:
        Loaded JSON data
    
    Example:
        # Load latest output from example_action_studio_login
        data = load_output("example_action_studio_login")
        
        # Load oldest output
        data = load_output("example_action_studio_login", latest=False)
    """
    if pattern is None:
        pattern = _get_caller_info()
    
    output_files = sorted(OUTPUT_DIR.glob(f"{pattern}_*.json"))
    
    if not output_files:
        raise FileNotFoundError(
            f"No output files found: {OUTPUT_DIR}/{pattern}_*.json"
        )
    
    target_file = output_files[-1] if latest else output_files[0]
    
    with open(target_file, "r", encoding="utf-8") as f:
        return json.load(f)
