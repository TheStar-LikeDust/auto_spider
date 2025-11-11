"""
CLI tool for auto_spider.

Quick commands for common tasks.
"""

import argparse
from .templates import generate_plan
from ..core import run_plan_from_file, DEFAULT_MAX_WORKERS


def cmd_generate(args):
    """Generate plan template file."""
    output_path = generate_plan(
        name=args.name,
        description=args.description,
        single_file=args.single_file
    )
    print(f"Generated plan file: {output_path}")
    
    if args.single_file:
        print("Actions defined inline in plan file")
    else:
        print(f"Generated actions package: actions_{args.name}/")


def cmd_run(args):
    """Run plan file."""
    print(f"Running plan: {args.plan_file} with {args.workers} workers")
    
    # parse actions
    actions = [a.strip() for a in args.actions.split(',')]
    
    run_plan_from_file(args.plan_file, actions=actions, max_workers=args.workers)
    
    print(f"\nPlan execution completed")


def main():
    """Main CLI entry with subcommands."""
    parser = argparse.ArgumentParser(description='Auto Spider CLI tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # generate subcommand
    parser_gen = subparsers.add_parser('generate', help='Generate plan template file')
    parser_gen.add_argument('name', help='Plan name (will generate plan_{name}.py)')
    parser_gen.add_argument('-d', '--description', help='Plan description')
    parser_gen.add_argument('--single-file', action='store_true', 
                           help='Generate single file with inline actions (default: separate actions package)')
    parser_gen.set_defaults(func=cmd_generate)
    
    # run subcommand
    parser_run = subparsers.add_parser('run', help='Run plan file')
    parser_run.add_argument('plan_file', help='Path to plan Python file')
    parser_run.add_argument('actions', help='Comma-separated action names (e.g., fetch,parse)')
    parser_run.add_argument('-w', '--workers', type=int, default=DEFAULT_MAX_WORKERS,
                           help=f'Number of worker processes (default: {DEFAULT_MAX_WORKERS})')
    parser_run.set_defaults(func=cmd_run)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
