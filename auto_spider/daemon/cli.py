"""
CLI commands for daemon mode.

Provides start, submit, reload, stop commands.
"""

import sys
import time
from pathlib import Path
from ..logger import build_logger
from .manager import DaemonManager, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_MAX_WORKERS
from .client import add_plan, reload, shutdown

_LOGGER = build_logger('daemon.cli')


def cmd_daemon_start(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, max_workers: int = DEFAULT_MAX_WORKERS):
    """
    Start daemon manager in foreground.
    
    Args:
        host: Manager host
        port: Manager port
        max_workers: Number of workers
    """
    print(f"Starting daemon manager on {host}:{port} with {max_workers} workers...")
    
    manager = DaemonManager(host=host, port=port, max_workers=max_workers)
    
    try:
        manager.start()
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, shutting down...")
        manager._handle_shutdown()
    except Exception as e:
        _LOGGER.error(f"Manager error: {e}")
        sys.exit(1)


def cmd_daemon_submit(plan_file: str, stage: str = 'action', steps: str = '', 
                     host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Submit plan to daemon manager.
    
    Args:
        plan_file: Path to plan file
        stage: Stage type
        steps: Comma-separated step names
        host: Manager host
        port: Manager port
    """
    # parse steps
    step_list = [s.strip() for s in steps.split(',') if s.strip()] if steps else []
    
    print(f"Submitting plan: {plan_file}, stage={stage}, steps={step_list}")
    
    response = add_plan(plan_file, stage, step_list, host, port)

    if response['success']:
        print(f"✓ {response['message']}")
    else:
        print(f"✗ Error: {response['message']}")
        sys.exit(1)


def cmd_daemon_reload(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Trigger module reload in daemon.
    
    Args:
        host: Manager host
        port: Manager port
    """
    print("Triggering reload...")
    
    response = reload(host, port)

    if response['success']:
        print(f"✓ {response['message']}")
    else:
        print(f"✗ Error: {response['message']}")
        sys.exit(1)


def cmd_daemon_stop(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    Stop daemon manager.
    
    Args:
        host: Manager host
        port: Manager port
    """
    print("Stopping daemon manager...")
    
    response = shutdown(host, port)

    if response['success']:
        print(f"✓ {response['message']}")
    else:
        print(f"✗ Error: {response['message']}")
        sys.exit(1)


