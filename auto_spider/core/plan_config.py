"""
Plan configuration management.

Provides default configuration and config merge utilities.
"""

from typing import Optional


class PlanConfig(dict):
    """
    Plan execution configuration with dict and attribute access.
    
    Supports both styles:
        config.max_workers          # attribute access (with IDE hints)
        config['max_workers']       # dict access (flexible)
    
    Config fields:
        plan_name: Plan name for output directory
        max_workers: Number of concurrent workers
        rate_limit: Delay between tasks in seconds (None = no limit)
        output_dir: Custom output directory (None = auto create)
    
    Example:
        # Use default config
        config = DEFAULT_CONFIG.copy()
        
        # Override specific values
        config = PlanConfig(plan_name='myplan', max_workers=2)
        
        # Merge configs
        config = merge_config(DEFAULT_CONFIG, {'rate_limit': 1.0})
    """
    
    def __init__(
        self,
        plan_name: Optional[str] = None,
        max_workers: int = 4,
        rate_limit: Optional[float] = None,
        output_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize plan configuration.
        
        Args:
            plan_name: Plan name for output directory
            max_workers: Number of concurrent workers (default: 4)
            rate_limit: Delay between tasks in seconds (None = no limit)
            output_dir: Custom output directory (None = auto create)
            **kwargs: Additional config fields
        """
        super().__init__(**kwargs)
        self.plan_name = plan_name
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.output_dir = output_dir
        
        # also store in dict for dict access
        self['plan_name'] = plan_name
        self['max_workers'] = max_workers
        self['rate_limit'] = rate_limit
        self['output_dir'] = output_dir
        
        # store additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
            self[key] = value
    
    def __setitem__(self, key, value):
        """Sync dict and attribute access."""
        super().__setitem__(key, value)
        setattr(self, key, value)
    
    def __repr__(self):
        return f"PlanConfig(plan_name={self.plan_name!r}, max_workers={self.max_workers}, rate_limit={self.rate_limit})"
    
    def copy(self):
        """Create a copy of config."""
        return PlanConfig(
            plan_name=self.plan_name,
            max_workers=self.max_workers,
            rate_limit=self.rate_limit,
            output_dir=self.output_dir,
            **{k: v for k, v in self.items() if k not in ['plan_name', 'max_workers', 'rate_limit', 'output_dir']}
        )


# Default configuration
DEFAULT_CONFIG = PlanConfig(
    plan_name=None,
    max_workers=4,
    rate_limit=None,
    output_dir=None,
)


def merge_config(base: PlanConfig, overrides: dict) -> PlanConfig:
    """
    Merge base config with override values.
    
    Creates new config with override values taking precedence.
    Only non-None values from overrides are applied.
    
    Args:
        base: Base configuration
        overrides: Dict of override values
        
    Returns:
        New PlanConfig with merged values
        
    Example:
        config = merge_config(DEFAULT_CONFIG, {
            'plan_name': 'myplan',
            'max_workers': 2,
            'rate_limit': 1.0
        })
    """
    # start with base values
    merged = base.copy()
    
    # apply overrides (only if not None)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    
    return merged


def load_config_from_module(module) -> PlanConfig:
    """
    Load configuration from plan module.
    
    Reads PLAN_CONFIG dict or individual config variables from module.
    
    Args:
        module: Plan module object
        
    Returns:
        PlanConfig object loaded from module
        
    Example:
        # In plan file:
        PLAN_CONFIG = {
            'plan_name': 'myplan',
            'max_workers': 2,
            'rate_limit': 1.0
        }
        
        # Or individual variables:
        PLAN_NAME = 'myplan'
        MAX_WORKERS = 2
        RATE_LIMIT = 1.0
    """
    # Try to load PLAN_CONFIG dict first
    config_dict = getattr(module, 'PLAN_CONFIG', None)
    
    if config_dict:
        return PlanConfig(**config_dict)
    
    # Fallback: load individual variables
    return PlanConfig(
        plan_name=getattr(module, 'PLAN_NAME', None),
        max_workers=getattr(module, 'MAX_WORKERS', 4),
        rate_limit=getattr(module, 'RATE_LIMIT', None),
        output_dir=getattr(module, 'OUTPUT_DIR', None),
    )
