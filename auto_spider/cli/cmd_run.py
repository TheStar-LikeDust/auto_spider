"""
CLI command: run

Run plan file with specified stage.
"""

import click

from ..core.plan_scheduler import run_plan, DEFAULT_MAX_WORKERS


@click.command('run')
@click.argument('plan_file')
@click.argument('steps')
@click.option('-s', '--stage', type=click.Choice(['action', 'parse', 'extract']), 
              help='Execution stage (auto-detect if not specified)')
@click.option('-w', '--workers', type=int, default=DEFAULT_MAX_WORKERS,
              help=f'Number of workers (default: {DEFAULT_MAX_WORKERS})')
@click.option('--retry-failed', is_flag=True,
              help='Retry failed tasks from previous run')
def cmd_run(plan_file, steps, stage, workers, retry_failed):
    """Run plan file with specified stage.
    
    PLAN_FILE: Path to plan Python file
    STEPS: Comma-separated step names (e.g., fetch_page,parse_data)
    """
    click.echo(f"Running plan: {plan_file}")
    click.echo(f"   Workers: {workers}")
    
    # parse step names
    step_list = [s.strip() for s in steps.split(',')]
    click.echo(f"   Steps: {', '.join(step_list)}")
    
    # auto-detect stage if not specified
    if not stage:
        if any('parse' in s for s in step_list):
            stage = 'parse'
        elif any('extract' in s or 'save' in s for s in step_list):
            stage = 'extract'
        else:
            stage = 'action'
    
    click.echo(f"   Stage: {stage}")
    if retry_failed:
        click.echo(f"   Mode: Retry failed tasks")
    
    # build stage parameters
    stage_params = {}
    if stage == 'action':
        stage_params['actions'] = step_list
    elif stage == 'parse':
        stage_params['parses'] = step_list
    else:
        stage_params['extracts'] = step_list
    
    run_plan(plan_file=plan_file, max_workers=workers, retry_failed=retry_failed, **stage_params)
    
    click.echo(f"\nPlan execution completed")
