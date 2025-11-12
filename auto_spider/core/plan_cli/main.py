"""
CLI argument parsing.

Main entry point for CLI tool.
"""

import argparse
from .commands import cmd_generate, cmd_run
from ..scheduler import DEFAULT_MAX_WORKERS


def _wrap_cmd_generate(args):
    """Wrapper for cmd_generate to handle argparse args."""
    cmd_generate(args.name, args.description, args.single_file)


def _wrap_cmd_run(args):
    """Wrapper for cmd_run to handle argparse args."""
    cmd_run(args.plan_file, args.steps, args.stage, args.workers)


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
  
  # Or just run the plan file directly
  python plan_myplan.py
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
    parser_run.set_defaults(func=_wrap_cmd_run)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
