"""
Code template generator.

Generate plan and action templates quickly.
"""

from pathlib import Path


ACTION_INIT_TEMPLATE = '''"""
{description}

Action module with example actions.
"""

# import to register actions
from .actions import *  # noqa: F401, F403
'''


ACTION_MODULE_TEMPLATE = '''"""
{description}
"""

from auto_spider import action, Context


@action()
def fetch_page(context: Context):
    """Fetch page from task url."""
    url = context.task.get('url')
    if not url:
        raise ValueError("Task must have 'url' field")
    
    response = context.spider.do_url(url, retry=3)

    # save to context['result'], will be auto-saved to output dir
    context['result'] = response.text
    return response.text
'''


PLAN_TEMPLATE = '''"""
{description}

Plan script with 3 fixed functions.
"""

from auto_spider.core import Task, run_plan
from auto_spider.components import RequestSpider

# import actions to register them
import actions_{name}  # noqa: F401


def initial_spider():
    """Create and return spider instance."""
    return RequestSpider()


def initial_task():
    """Create and return task list."""
    return [
        Task(name='task1', url='https://example.com'),
        Task(name='task2', url='https://example.com'),
    ]


def initial_plan():
    """
    Initialize and return resources object.
    
    Resources will be injected into context.initial
    Context will have: output_dir, save_result
    """
    # initialize db, cache, etc
    initial = {{
        # 'db': Database(),
        # 'cache': Cache(),
    }}
    return initial


ACTION_LIST = [
    'fetch_page',
]


if __name__ == '__main__':
    run_plan(initial_spider, initial_task, initial_plan, 
             actions=ACTION_LIST, plan_name='{name}')
'''


PLAN_SINGLE_FILE_TEMPLATE = '''"""
{description}

Plan script with 3 fixed functions and inline actions.
"""

from auto_spider import action, Context
from auto_spider.core import Task, run_plan
from auto_spider.components import RequestSpider


def initial_spider():
    """Create and return spider instance."""
    return RequestSpider()


def initial_task():
    """Create and return task list."""
    return [
        Task(name='task1', url='https://example.com'),
        Task(name='task2', url='https://example.com'),
    ]


def initial_plan():
    """
    Initialize and return resources object.
    
    Resources will be injected into context.initial
    Context will have: output_dir, save_result
    """
    # initialize db, cache, etc
    initial = {
        # 'db': Database(),
        # 'cache': Cache(),
    }
    return initial


@action()
def fetch_page(context: Context):
    """Fetch page from task url."""
    url = context.task.get('url')
    if not url:
        raise ValueError("Task must have 'url' field")
    
    response = context.spider.do_url(url, retry=3)

    # save to context['result'], will be auto-saved to output dir
    context['result'] = response.text
    return response.text


ACTION_LIST = [
    'fetch_page',
]


if __name__ == '__main__':
    run_plan(initial_spider, initial_task, initial_plan, 
             actions=ACTION_LIST, plan_name='{name}')
'''


def generate_actions(name: str, description: str = None) -> Path:
    """
    Generate actions package with template actions.
    
    Args:
        name: Package name (will generate actions_{name}/)
        description: Package description
        
    Returns:
        Path to generated package directory
        
    Example:
        generate_actions('baidu', description='Baidu scraping actions')
    """
    if not description:
        description = f'Actions for {name}'
    
    package_name = f'actions_{name}'
    package_path = Path(package_name)
    package_path.mkdir(exist_ok=True)
    
    # generate __init__.py
    init_path = package_path / '__init__.py'
    init_content = ACTION_INIT_TEMPLATE.format(description=description)
    init_path.write_text(init_content, encoding='utf-8')
    
    # generate actions.py
    actions_path = package_path / 'actions.py'
    actions_content = ACTION_MODULE_TEMPLATE.format(description=f'{description} - Action implementations')
    actions_path.write_text(actions_content, encoding='utf-8')
    
    return package_path


def generate_plan(name: str, description: str = None, single_file: bool = False) -> Path:
    """
    Generate plan_xxx.py template file in current directory.
    
    Args:
        name: Plan name (will generate plan_{name}.py)
        description: Plan description
        single_file: Include actions inline in plan file (default: False)
        
    Returns:
        Path to generated file
        
    Example:
        # with actions package
        generate_plan('baidu', description='Fetch baidu homepage')
        
        # single file with inline actions
        generate_plan('baidu', description='Fetch baidu homepage', single_file=True)
    """
    if not description:
        description = f'Plan for {name}'
    
    filename = f'plan_{name}.py'
    output_path = Path(filename)
    
    # choose template based on mode
    if single_file:
        # inline actions mode
        content = PLAN_SINGLE_FILE_TEMPLATE.format(description=description, name=name)
    else:
        # separate actions package mode
        content = PLAN_TEMPLATE.format(description=description, name=name)
        generate_actions(name, description=f'Actions for {name}')
    
    output_path.write_text(content, encoding='utf-8')
    
    return output_path
