"""
Plan configuration management.

Provides default configuration and config merge utilities.

Configuration Fields
--------------------
PLAN_NAME : str
    Plan name for output directory naming
    Used by: scheduler, storage
    
MAX_WORKERS : int
    Number of concurrent workers (default: 4)
    Used by: scheduler, dispatcher
    
RATE_LIMIT : float or None
    Delay between tasks in seconds (None = no limit)
    Example: 1.0 = 1 task/sec, 0.5 = 2 tasks/sec
    Used by: scheduler, dispatcher
    
OUTPUT_DIR : str or None
    Custom output directory (None = auto create based on PLAN_NAME)
    Used by: scheduler, storage

STORAGE_BACKEND : str
    Storage backend type ('file', 'shelve', 'sqlite', 'redis')
    Default: 'file'
    Used by: storage
    
STORAGE_OPTIONS : dict
    Backend-specific options
    Example: {'base_dir': 'output'} for file/shelve
    Used by: storage

Usage in Modules
----------------
scheduler.py:
    - Reads: PLAN_NAME, MAX_WORKERS, RATE_LIMIT, OUTPUT_DIR
    - Creates output directories using PLAN_NAME
    - Controls worker count via MAX_WORKERS
    - Applies rate limiting via RATE_LIMIT

storage.py:
    - Reads: PLAN_NAME, OUTPUT_DIR
    - Creates stage directories based on PLAN_NAME
    - Uses OUTPUT_DIR if specified

worker.py:
    - Passes config to Context
    - Does not directly read config values

User Steps:
    @action()
    def my_step(context: Context):
        # Access any config value
        max_workers = context.config.MAX_WORKERS
        plan_name = context.config.PLAN_NAME

Recommended Usage
-----------------
# In plan file
PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'
PLAN_CONFIG.MAX_WORKERS = 4
PLAN_CONFIG.RATE_LIMIT = 1.0
PLAN_CONFIG.OUTPUT_DIR = None

# Pass to run_plan
run_plan(..., config=PLAN_CONFIG)

# Access in step
@action()
def fetch_page(context: Context):
    workers = context.config.MAX_WORKERS
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Callable, List, Tuple, Dict, Any


class DictAttributeMixin:
    """
    Mixin for dict-attribute synchronization.
    
    Provides automatic sync between dict access and attribute access:
        obj.key = value  <->  obj['key'] = value
    """
    
    def __setitem__(self, key, value):
        """Sync dict and attribute access."""
        super().__setitem__(key, value)
        setattr(self, key, value)
    
    def __setattr__(self, key, value):
        """Sync attribute and dict access."""
        super().__setattr__(key, value)
        if isinstance(self, dict):
            dict.__setitem__(self, key, value)


class RuntimeConfigMixin:
    """
    Mixin for runtime internal variables.
    
    These variables are set by scheduler/worker during execution,
    not by user. All prefixed with underscore.
    """
    
    # Current stage output directory (set by scheduler, used by worker)
    _stage_output_dir: Optional[str] = None


class PlanConfig(dict, DictAttributeMixin, RuntimeConfigMixin):
    """
    Plan execution configuration.
    
    Config Fields (all uppercase for clarity):
        PLAN_NAME: str - Plan name for output directory
        MAX_WORKERS: int - Number of concurrent workers
        RATE_LIMIT: float - Delay between tasks in seconds
        OUTPUT_DIR: str - Custom output directory
    
    Access methods:
        config.PLAN_NAME          # attribute access (with IDE hints)
        config['PLAN_NAME']       # dict access (flexible)
    
    Example:
        PLAN_CONFIG = PlanConfig()
        PLAN_CONFIG.PLAN_NAME = 'myplan'
        PLAN_CONFIG.MAX_WORKERS = 4
        PLAN_CONFIG.RATE_LIMIT = 1.0
    """
    
    # Plan name for output directory
    PLAN_NAME: Optional[str] = None
    
    # Number of concurrent workers
    MAX_WORKERS: int = 4
    
    # Delay between tasks (seconds)
    RATE_LIMIT: Optional[float] = None
    
    # Custom output directory
    OUTPUT_DIR: Optional[str] = None
    
    # Storage backend type
    STORAGE_BACKEND: str = 'file'
    
    # Storage backend options
    STORAGE_OPTIONS: dict = None
    
    # Use timestamp in storage directory name (True: action_20241118_150000, False: action)
    STORAGE_TIMESTAMP: bool = True
    
    def __init__(self):
        super().__init__()
        if self.STORAGE_OPTIONS is None:
            self.STORAGE_OPTIONS = {}


# Default configuration instance
DEFAULT_CONFIG = PlanConfig()


def load_plan_module(plan_file: str) -> Dict[str, Any]:
    """
    Load plan module and extract all configuration parameters.
    
    Args:
        plan_file: Path to plan file
        
    Returns:
        Dict with keys:
            - initial_spider: Spider factory function
            - initial_task: Task factory function
            - initial_plan: Plan factory function
            - actions: List of action step names
            - parses: List of parse step names
            - extracts: List of extract step names
            - config: PlanConfig instance
    """
    plan_path = Path(plan_file).resolve()
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_file}")

    plan_dir = plan_path.parent
    if str(plan_dir) not in sys.path:
        sys.path.insert(0, str(plan_dir))

    plan_module_name = plan_path.stem
    spec = importlib.util.spec_from_file_location(plan_module_name, plan_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load plan file: {plan_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[plan_module_name] = module
    spec.loader.exec_module(module)

    # extract factories
    initial_spider = getattr(module, 'initial_spider', None)
    initial_task = getattr(module, 'initial_task', None)
    initial_plan = getattr(module, 'initial_plan', None)
    
    # extract plan_config
    plan_config = getattr(module, 'PLAN_CONFIG', None)
    
    # extract step names
    stages_dict = getattr(module, 'STAGES', None)
    if stages_dict:
        actions = stages_dict.get('action', [])
        parses = stages_dict.get('parse', [])
        extracts = stages_dict.get('extract', [])
    else:
        actions = getattr(module, 'ACTION_LIST', [])
        parses = getattr(module, 'PARSE_LIST', [])
        extracts = getattr(module, 'EXTRACT_LIST', [])
    
    return {
        'initial_spider': initial_spider,
        'initial_task': initial_task,
        'initial_plan': initial_plan,
        'actions': actions,
        'parses': parses,
        'extracts': extracts,
        'plan_config': plan_config
    }
