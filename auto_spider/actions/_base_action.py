"""
DEPRECATED: Action execution moved to core module.

This file kept for backward compatibility only.
Use core._execute_actions or core.execute_plan instead.
"""

import warnings


def execute_pipeline(*args, **kwargs):
    """
    DEPRECATED: Use core._execute_actions instead.
    
    This function is deprecated and will be removed in future versions.
    """
    warnings.warn(
        "execute_pipeline is deprecated, use core._execute_actions instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    from ..core import _execute_actions
    return _execute_actions(*args, **kwargs)
