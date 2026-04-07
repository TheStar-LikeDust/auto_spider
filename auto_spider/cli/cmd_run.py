"""
CLI command: run

Run plan file with specified stage.
"""

import json

import click

from ..core.plan_core import run_plan_with_file


@click.command('run')
@click.argument('plan_file')
@click.option('--action', is_flag=True, help='Run action stage')
@click.option('--parse', is_flag=True, help='Run parse stage')
@click.option('--extract', is_flag=True, help='Run extract stage')
@click.option('--retry-failed', is_flag=True,
              help='Retry failed tasks from previous run')
@click.option('--task', '-t', 'params', multiple=True,
              metavar='KEY=VALUE', help='Inject param into each task (repeatable)')
@click.option('--init', '-i', 'init_params', multiple=True,
              metavar='KEY=VALUE', help='Inject param into initial_task (repeatable)')
@click.option('--tasks', default=None,
              metavar='JSON', help='JSON string of task list, bypasses initial_task')
def cmd_run(plan_file, action, parse, extract, retry_failed, params, init_params, tasks):
    """Run plan file with specified stage.
    
    PLAN_FILE: Path to plan file, .py extension is optional (tp or tp.py both work)

    Steps are defined in ACTION_STEPS/PARSE_STEPS/EXTRACT_STEPS lists in the plan file.
    """
    if not (action or parse or extract):
        raise click.UsageError("Must specify at least one of: --action, --parse, --extract")
    
    stages = [s for s, v in [('action', action), ('parse', parse), ('extract', extract)] if v]
    click.echo(f"Running plan: {plan_file}")
    click.echo(f"   Stage: {', '.join(stages)}")
    if retry_failed:
        click.echo(f"   Mode: Retry failed tasks")
    
    task_params = dict(p.split('=', 1) for p in params) if params else None
    init_params = dict(p.split('=', 1) for p in init_params) if init_params else None
    tasks = json.loads(tasks) if tasks else None
    run_plan_with_file(plan_file, action=action, parse=parse, extract=extract,
                       retry_failed=retry_failed, task_params=task_params, init_params=init_params,
                       tasks=tasks)
    
    click.echo(f"\nPlan execution completed")
