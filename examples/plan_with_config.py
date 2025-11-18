"""
Example plan demonstrating PlanConfig usage.

Shows all configuration options and best practices.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_spider import action, Context
from auto_spider.core import Task, run_plan, PlanConfig, DEFAULT_CONFIG
from auto_spider.components import RequestSpider


# ============== Configuration ==============

# Method 1: Dictionary config (recommended)
PLAN_CONFIG = {
    'plan_name': 'config_example',
    'max_workers': 2,       # number of concurrent workers
    'rate_limit': 1.0,      # delay between tasks in seconds (None = no limit)
    'output_dir': None,     # custom output directory (None = auto create)
}

# Step lists for each stage
STAGES = {
    'action': ['fetch_page'],
    'parse': [],
    'extract': [],
}


# ============== Plan Functions ==============

def initial_spider():
    """Create and return spider instance."""
    return RequestSpider()


def initial_task():
    """Create and return task list."""
    return [
        Task(url='https://example.com'),
        Task(url='https://example.org'),
    ]


def initial_plan():
    """Initialize and return resources object."""
    return {}


# ============== Steps ==============

@action()
def fetch_page(context: Context):
    """Fetch page content from task url."""
    url = context.task.get('url')
    print(f"Fetching: {url}")
    
    # simulate fetch
    content = f"<html><title>Page from {url}</title></html>"
    
    context['content'] = content
    context['result'] = {
        'url': url,
        'status': 200,
        'length': len(content)
    }
    
    return content


# ============== Execution Examples ==============

def example_dict_unpack():
    """Example 1: Direct dict unpacking (simplest)."""
    print("\n=== Example 1: Dict Unpacking ===")
    run_plan(
        initial_spider, initial_task, initial_plan,
        actions=STAGES['action'],
        **PLAN_CONFIG  # unpack config dict
    )


def example_config_object():
    """Example 2: Using PlanConfig object."""
    print("\n=== Example 2: Config Object ===")
    
    # create config object
    config = PlanConfig(**PLAN_CONFIG)
    
    # access via attributes (IDE hints)
    print(f"Plan name: {config.plan_name}")
    print(f"Workers: {config.max_workers}")
    print(f"Rate limit: {config.rate_limit}")
    
    # modify if needed
    config.max_workers = 4
    
    run_plan(
        initial_spider, initial_task, initial_plan,
        actions=STAGES['action'],
        plan_name=config.plan_name,
        max_workers=config.max_workers,
        rate_limit=config.rate_limit,
        output_dir=config.output_dir
    )


def example_default_config():
    """Example 3: Using DEFAULT_CONFIG."""
    print("\n=== Example 3: Default Config ===")
    
    from auto_spider.core import merge_config
    
    # merge with defaults
    config = merge_config(DEFAULT_CONFIG, {
        'plan_name': 'merged_example',
        'max_workers': 2,
    })
    
    print(f"Merged config: {config}")
    
    run_plan(
        initial_spider, initial_task, initial_plan,
        actions=STAGES['action'],
        **config  # unpack merged config
    )


def example_attribute_access():
    """Example 4: Attribute and dict access."""
    print("\n=== Example 4: Attribute Access ===")
    
    config = PlanConfig(plan_name='attr_test', max_workers=2)
    
    # attribute access
    print(f"config.plan_name = {config.plan_name}")
    
    # dict access
    print(f"config['max_workers'] = {config['max_workers']}")
    
    # modify via attribute
    config.rate_limit = 0.5
    
    # read via dict
    print(f"config['rate_limit'] = {config['rate_limit']}")


def example_runtime_override():
    """Example 5: Runtime config override."""
    print("\n=== Example 5: Runtime Override ===")
    
    # base config
    config = PLAN_CONFIG.copy()
    
    # runtime decision
    is_production = False
    if is_production:
        config['max_workers'] = 1
        config['rate_limit'] = 2.0
    else:
        config['max_workers'] = 4
        config['rate_limit'] = None
    
    print(f"Running with config: {config}")
    
    run_plan(
        initial_spider, initial_task, initial_plan,
        actions=STAGES['action'],
        **config
    )


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Config examples')
    parser.add_argument(
        '--example',
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help='Example number to run (1-5)'
    )
    
    args = parser.parse_args()
    
    examples = {
        1: example_dict_unpack,
        2: example_config_object,
        3: example_default_config,
        4: example_attribute_access,
        5: example_runtime_override,
    }
    
    print(f"Running example {args.example}...")
    examples[args.example]()
    
    print("\n✅ Example completed!")
