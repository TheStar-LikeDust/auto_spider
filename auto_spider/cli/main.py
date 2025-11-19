"""
CLI argument parsing.

Main entry point for CLI tool.
"""

import argparse
from .commands import cmd_generate, cmd_run
from ..core.scheduler import DEFAULT_MAX_WORKERS
from ..daemon.cli import (
    cmd_daemon_start,
    cmd_daemon_submit,
    cmd_daemon_reload,
    cmd_daemon_stop,
)
from ..daemon.manager import DEFAULT_HOST, DEFAULT_PORT


def _wrap_cmd_generate(args):
    """Wrapper for cmd_generate to handle argparse args."""
    cmd_generate(args.name, args.description, args.single_file)


def _wrap_cmd_run(args):
    """Wrapper for cmd_run to handle argparse args."""
    cmd_run(args.plan_file, args.steps, args.stage, args.workers, args.retry_failed)


def _wrap_daemon_start(args):
    """Wrapper for daemon start."""
    cmd_daemon_start(args.host, args.port, args.workers)


def _wrap_daemon_submit(args):
    """Wrapper for daemon submit."""
    cmd_daemon_submit(args.plan_file, args.stage, args.steps, args.host, args.port)


def _wrap_daemon_reload(args):
    """Wrapper for daemon reload."""
    cmd_daemon_reload(args.host, args.port)


def _wrap_daemon_stop(args):
    """Wrapper for daemon stop."""
    cmd_daemon_stop(args.host, args.port)




def main():
    """Main CLI entry with subcommands."""
    parser = argparse.ArgumentParser(
        description='Auto Spider - Web scraping automation framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate new plan
  auto-spider generate myplan
  auto-spider generate myplan --single-file
  
  # Run plan stages
  auto-spider run plan_myplan.py fetch_page --stage action
  auto-spider run plan_myplan.py parse_data --stage parse
  auto-spider run plan_myplan.py save_data --stage extract
  
  # Retry failed tasks
  auto-spider run plan_myplan.py fetch_page --stage action --retry-failed
  
  # Or just run the plan file directly
  python plan_myplan.py
  
  # Daemon mode
  auto-spider daemon start
  auto-spider daemon submit plan_myplan.py action fetch_page
  auto-spider daemon reload
  auto-spider daemon stop
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # generate subcommand
    parser_gen = subparsers.add_parser(
        'generate',
        help='Generate plan template',
        aliases=['gen', 'g']
    )
    parser_gen.add_argument('name', help='Plan name (generates plan_{name}.py)')
    parser_gen.add_argument('-d', '--description', help='Plan description')
    parser_gen.add_argument(
        '--single-file',
        action='store_true',
        help='Generate single file with inline steps (default: separate steps package)'
    )
    parser_gen.set_defaults(func=_wrap_cmd_generate)
    
    # run subcommand
    parser_run = subparsers.add_parser(
        'run',
        help='Run plan file',
        aliases=['r']
    )
    parser_run.add_argument('plan_file', help='Path to plan Python file')
    parser_run.add_argument('steps', help='Comma-separated step names (e.g., fetch_page,parse_data)')
    parser_run.add_argument(
        '-s', '--stage',
        choices=['action', 'parse', 'extract'],
        help='Execution stage (auto-detect if not specified)'
    )
    parser_run.add_argument(
        '-w', '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'Number of workers (default: {DEFAULT_MAX_WORKERS})'
    )
    parser_run.add_argument(
        '--retry-failed',
        action='store_true',
        help='Retry failed tasks from previous run instead of running initial_task (action stage only)'
    )
    parser_run.set_defaults(func=_wrap_cmd_run)
    
    # daemon subcommand
    parser_daemon = subparsers.add_parser(
        'daemon',
        help='Daemon mode commands',
        aliases=['d']
    )
    daemon_subparsers = parser_daemon.add_subparsers(dest='daemon_cmd', help='Daemon commands')
    
    # daemon start
    parser_daemon_start = daemon_subparsers.add_parser('start', help='Start daemon manager')
    parser_daemon_start.add_argument('--host', default=DEFAULT_HOST, help=f'Host (default: {DEFAULT_HOST})')
    parser_daemon_start.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Port (default: {DEFAULT_PORT})')
    parser_daemon_start.add_argument(
        '-w', '--workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'Number of workers (default: {DEFAULT_MAX_WORKERS})'
    )
    parser_daemon_start.set_defaults(func=_wrap_daemon_start)
    
    # daemon submit
    parser_daemon_submit = daemon_subparsers.add_parser('submit', help='Submit plan to daemon')
    parser_daemon_submit.add_argument('plan_file', help='Path to plan file')
    parser_daemon_submit.add_argument('stage', choices=['action', 'parse', 'extract'], help='Stage type')
    parser_daemon_submit.add_argument('steps', nargs='?', default='', help='Comma-separated step names')
    parser_daemon_submit.add_argument('--host', default=DEFAULT_HOST, help=f'Host (default: {DEFAULT_HOST})')
    parser_daemon_submit.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Port (default: {DEFAULT_PORT})')
    parser_daemon_submit.set_defaults(func=_wrap_daemon_submit)
    
    # daemon reload
    parser_daemon_reload = daemon_subparsers.add_parser('reload', help='Reload modules in daemon')
    parser_daemon_reload.add_argument('--host', default=DEFAULT_HOST, help=f'Host (default: {DEFAULT_HOST})')
    parser_daemon_reload.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Port (default: {DEFAULT_PORT})')
    parser_daemon_reload.set_defaults(func=_wrap_daemon_reload)
    
    # daemon stop
    parser_daemon_stop = daemon_subparsers.add_parser('stop', help='Stop daemon manager')
    parser_daemon_stop.add_argument('--host', default=DEFAULT_HOST, help=f'Host (default: {DEFAULT_HOST})')
    parser_daemon_stop.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Port (default: {DEFAULT_PORT})')
    parser_daemon_stop.set_defaults(func=_wrap_daemon_stop)

    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
