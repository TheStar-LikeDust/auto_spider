"""
Plan configuration management.

`PlanConfig` is composed from three user-facing config classes and one internal mixin:

```
PlanConfig(dict, DictAttributeMixin, CommonConfig, StorageConfig, ExecutionConfig, RuntimeConfigMixin)
```

## CommonConfig — plan identity

| Field | Type | Default | Description |
|---|---|---|---|
| `PLAN_NAME` | `str | None` | `None` | Plan name, used for output directory naming |

## StorageConfig — storage behavior

| Field | Type | Default | Description |
|---|---|---|---|
| `OUTPUT_DIR` | `str | None` | `None` | Base output dir. Final path: `<OUTPUT_DIR>/<PLAN_NAME>/action_xxx` |
| `STORAGE_BACKEND` | `str` | `'file'` | Backend type: `file | shelve | sqlite | redis` |
| `STORAGE_OPTIONS` | `dict` | `{}` | Backend-specific options |
| `STORAGE_TIMESTAMP` | `bool` | `True` | Append timestamp to dir name, e.g. `action_20241118_150000` |
| `SAVE_RESULT` | `bool` | `True` | Write results to storage. `False` disables all file output |

## ExecutionConfig — concurrency / rate limit / retry

| Field | Type | Default | Description |
|---|---|---|---|
| `MAX_WORKERS` | `int` | `4` | Number of concurrent workers |
| `RATE_LIMIT` | `float | None` | `None` | Delay between tasks in seconds. `None` = no limit |
| `TASK_RETRY_COUNT` | `int` | `3` | Total attempts per task (1 initial + N-1 retries) |
| `USE_THREAD_WORKERS` | `bool` | `False` | Force Thread for all stages. Default: action=Process, parse/extract=Thread |
| `START_DELAY` | `int` | `0` | Countdown seconds before workers start |

## RuntimeConfigMixin — internal (set by system)

| Field | Type | Description |
|---|---|---|
| `_action_steps` | `List[str]` | Populated from `ACTION_STEPS` in plan module |
| `_parse_steps` | `List[str]` | Populated from `PARSE_STEPS` in plan module |
| `_extract_steps` | `List[str]` | Populated from `EXTRACT_STEPS` in plan module |

## Usage

```python
PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'
PLAN_CONFIG.MAX_WORKERS = 4
PLAN_CONFIG.RATE_LIMIT = 1.0

ACTION_STEPS = ['fetch_page']
PARSE_STEPS = ['parse_data']
EXTRACT_STEPS = ['save_data']
```

```bash
auto-spider run myplan.py --action
```
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any


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


class CommonConfig:
    """Common plan identity config."""

    # Plan name for output directory naming
    PLAN_NAME: Optional[str] = None


class StorageConfig:
    """Storage behavior config."""

    # Base output directory (final: <OUTPUT_DIR>/<PLAN_NAME>/action_xxx)
    OUTPUT_DIR: Optional[str] = None

    # Storage backend type ('file', 'shelve', 'sqlite', 'redis')
    STORAGE_BACKEND: str = 'file'

    # Backend-specific options
    STORAGE_OPTIONS: dict = None

    # Use timestamp in storage directory name (True: action_20241118_150000, False: action)
    STORAGE_TIMESTAMP: bool = True

    # Save results to storage (False = disable all file output)
    SAVE_RESULT: bool = True


class ExecutionConfig:
    """Worker execution config: concurrency, rate limit, retry strategy."""

    # Number of concurrent workers
    MAX_WORKERS: int = 4

    # Delay between tasks in seconds (None = no limit)
    RATE_LIMIT: Optional[float] = None

    # Task retry count (default: 3 = 1 initial + 2 retries)
    TASK_RETRY_COUNT: int = 3

    # Force thread workers for all stages (default: False)
    # If False: action uses Process, parse/extract use Thread
    # If True: all stages use Thread
    USE_THREAD_WORKERS: bool = False

    # Countdown delay before workers start (seconds, 0 = no countdown)
    START_DELAY: int = 0


class RuntimeConfigMixin:
    """
    Internal runtime variables set by the system during execution.
    Not user-facing. All prefixed with underscore.
    """

    # Step name lists (set by load_plan_module, used by run_plan)
    _action_steps: List[str] = []
    _parse_steps: List[str] = []
    _extract_steps: List[str] = []


class PlanConfig(dict, DictAttributeMixin, CommonConfig, StorageConfig, ExecutionConfig, RuntimeConfigMixin):
    """
    Plan execution configuration.

    Composed from:
        CommonConfig    - PLAN_NAME
        StorageConfig   - OUTPUT_DIR, STORAGE_BACKEND, STORAGE_OPTIONS, STORAGE_TIMESTAMP, SAVE_RESULT
        ExecutionConfig - MAX_WORKERS, RATE_LIMIT, TASK_RETRY_COUNT, USE_THREAD_WORKERS, START_DELAY

    Access methods:
        config.PLAN_NAME          # attribute access (with IDE hints)
        config['PLAN_NAME']       # dict access (flexible)

    Example:
        PLAN_CONFIG = PlanConfig()
        PLAN_CONFIG.PLAN_NAME = 'myplan'
        PLAN_CONFIG.MAX_WORKERS = 4
        PLAN_CONFIG.RATE_LIMIT = 1.0
    """

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
        plan_file: Path to plan file (with or without .py extension)
        
    Returns:
        Dict with keys:
            - initial_spider: Spider factory function
            - initial_task: Task factory function
            - initial_plan: Plan factory function
            - plan_config: PlanConfig instance (with _action_steps/_parse_steps/_extract_steps attached)
    """
    if not plan_file.endswith('.py'):
        plan_file = f"{plan_file}.py"
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
    
    # attach step names to plan_config for run_plan to read
    if plan_config:
        plan_config._action_steps = getattr(module, 'ACTION_STEPS', [])
        plan_config._parse_steps = getattr(module, 'PARSE_STEPS', [])
        plan_config._extract_steps = getattr(module, 'EXTRACT_STEPS', [])
    
    return {
        'initial_spider': initial_spider,
        'initial_task': initial_task,
        'initial_plan': initial_plan,
        'plan_config': plan_config
    }
