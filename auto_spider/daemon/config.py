"""
Daemon configuration constants.
"""

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 9527
DEFAULT_MAX_WORKERS = 4

# Command types for daemon communication
ADD_PLAN = 'add_plan'
RELOAD = 'reload'
SHUTDOWN = 'shutdown'
