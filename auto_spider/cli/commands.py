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
    
    print(f"Generated plan file: {output_path}")
    
    if single_file:
        print("   Steps defined inline in plan file")
    else:
        print(f"   Generated steps package: steps_{name}/")
        print(f"      - action.py    (action stage steps)")
        print(f"      - parse.py     (parse stage steps)")
        print(f"      - extract.py   (extract stage steps)")
    
    print(f"\nNext steps:")
    print(f"   1. Edit plan_{name}.py to define tasks")
    if not single_file:
        print(f"   2. Edit steps_{name}/action.py to implement action steps")
        print(f"   3. Edit steps_{name}/parse.py to implement parse steps")
        print(f"   4. Edit steps_{name}/extract.py to implement extract steps")
    print(f"   5. Run action stage: python plan_{name}.py")
    print(f"   6. Run parse stage: Uncomment parse section in plan file")
    print(f"   7. Run extract stage: Uncomment extract section in plan file")
    
    return output_path


def cmd_run(plan_file: str, steps: str, stage: str = None, workers: int = DEFAULT_MAX_WORKERS):
    """
    Run plan file with specified stage.
    
    Args:
        plan_file: Path to plan file
        steps: Comma-separated step names
        stage: Stage name (action/parse/extract), auto-detect if None
        workers: Number of workers
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
    
    run_plan_from_file(plan_file, stage=stage, step_names=step_list, max_workers=workers)
    
    print(f"\nPlan execution completed")
