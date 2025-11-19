"""
CLI command implementations.

Business logic for CLI commands.
"""

from ..template import generate_plan
from ..core.scheduler import run_plan_from_file, DEFAULT_MAX_WORKERS


def cmd_generate(name: str, description: str = None, single_file: bool = False):
    """
    Generate plan and steps template.
    
    Args:
        name: Plan name
        description: Plan description
        single_file: Generate single file mode
        
    Returns:
        Path to generated file
    """
    output_path = generate_plan(name, description, single_file)
    
    print(f"Generated: {output_path}")
    if not single_file:
        print(f"Generated: steps_{name}/")
    
    print(f"\nCommands:")
    print(f"  python plan_{name}.py")
    print(f"  auto-spider run plan_{name}.py fetch_page --stage action")
    print(f"  auto-spider run plan_{name}.py fetch_page --stage action --retry-failed")
    
    return output_path


def cmd_run(plan_file: str, steps: str, stage: str = None, workers: int = DEFAULT_MAX_WORKERS, retry_failed: bool = False):
    """
    Run plan file with specified stage.
    
    Args:
        plan_file: Path to plan file
        steps: Comma-separated step names
        stage: Stage name (action/parse/extract), auto-detect if None
        workers: Number of workers
        retry_failed: Retry failed tasks instead of running initial_task
    """
    print(f"Running plan: {plan_file}")
    print(f"   Workers: {workers}")
    
    # parse step names
    step_list = [s.strip() for s in steps.split(',')]
    print(f"   Steps: {', '.join(step_list)}")
    
    # auto-detect stage if not specified
    if not stage:
        if any('parse' in s for s in step_list):
            stage = 'parse'
        elif any('extract' in s or 'save' in s for s in step_list):
            stage = 'extract'
        else:
            stage = 'action'
    
    print(f"   Stage: {stage}")
    if retry_failed:
        print(f"   Mode: Retry failed tasks")
    
    run_plan_from_file(plan_file, stage=stage, step_names=step_list, max_workers=workers, retry_failed=retry_failed)
    
    print(f"\nPlan execution completed")
