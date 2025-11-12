"""
DEPRECATED: Template strings for code generation.

This file is deprecated. Templates are now loaded from template_files/ directory.
See generator.py for implementation.

The old approach (storing templates as Python strings) required complex escaping.
The new approach (storing templates as text files) is much cleaner.
"""

# Step package __init__.py template
STEP_INIT_TEMPLATE = '''"""
{description}

Step modules: action.py, parse.py, extract.py
"""

# import all steps to register them
from . import action, parse, extract  # noqa: F401
'''


# Action module template
ACTION_MODULE_TEMPLATE = '''"""
{description} - Action steps

Action stage: fetch data with spider.
"""

from auto_spider import action, Context


@action()
def fetch_page(context: Context):
    """Fetch page content from task url."""
    url = context.task.get('url')
    if not url:
        raise ValueError("Task must have 'url' field")
    
    response = context.spider.do_url(url)

    # save raw HTML to context['content']
    context['content'] = response.text
    # save metadata to context['result']
    context['result'] = {{
        'url': url,
        'status': response.status_code,
        'length': len(response.text)
    }}
    return response.text
'''


# Parse module template
PARSE_MODULE_TEMPLATE = '''"""
{description} - Parse steps

Parse stage: parse HTML to extract data.
"""

from auto_spider import parse, Context


@parse()
def parse_data(context: Context):
    """Parse HTML content to extract data."""
    content = context.get('content', '')
    
    # TODO: implement parsing logic
    # Example: extract title, links, etc.
    data = {{
        'title': 'Example Title',
        'items': []
    }}
    
    # save parsed data to context['data']
    context['data'] = data
    return data
'''


# Extract module template
EXTRACT_MODULE_TEMPLATE = '''"""
{description} - Extract steps

Extract stage: save data to database or file.
"""

from auto_spider import extract, Context


@extract()
def save_data(context: Context):
    """Save parsed data to database or file."""
    data = context.get('data', {{}})
    
    # TODO: implement save logic
    # Example: save to database, write to file, etc.
    # db = context.initial.get('db')
    # db.save(data)
    
    return f"Saved {{len(data)}} items"
'''


# Plan template with separate steps package
PLAN_TEMPLATE = '''"""
{description}

Plan script with 3 fixed functions.
"""

from auto_spider.core import Task, run_plan
from auto_spider.components import RequestSpider

# import steps to register them
import steps_{name}  # noqa: F401


def initial_spider():
    """Create and return spider instance."""
    return RequestSpider()


def initial_task():
    """Create and return task list."""
    return [
        Task(url='https://example.com/page1'),
        Task(url='https://example.com/page2'),
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


# Step lists for each stage
ACTION_LIST = [
    'fetch_page',
]

PARSE_LIST = [
    'parse_data',
]

EXTRACT_LIST = [
    'save_data',
]


if __name__ == '__main__':
    # Default: run action stage only
    run_plan(initial_spider, initial_task, initial_plan, 
             actions=ACTION_LIST, plan_name='{name}')
    
    # Uncomment to run parse stage
    # run_plan(initial_task=initial_task, initial_plan=initial_plan,
    #          parses=PARSE_LIST, plan_name='{name}')
    
    # Uncomment to run extract stage
    # run_plan(initial_task=initial_task, initial_plan=initial_plan,
    #          extracts=EXTRACT_LIST, plan_name='{name}')
'''


# Plan template with inline steps (single file)
PLAN_SINGLE_FILE_TEMPLATE = '''"""
{description}

Plan script with 3 fixed functions and inline steps.
"""

from auto_spider import action, parse, extract, Context
from auto_spider.core import Task, run_plan
from auto_spider.components import RequestSpider


def initial_spider():
    """Create and return spider instance."""
    return RequestSpider()


def initial_task():
    """Create and return task list."""
    return [
        Task(url='https://example.com/page1'),
        Task(url='https://example.com/page2'),
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


@action()
def fetch_page(context: Context):
    """Fetch page content from task url."""
    url = context.task.get('url')
    if not url:
        raise ValueError("Task must have 'url' field")
    
    response = context.spider.do_url(url)

    # save raw HTML to context['content']
    context['content'] = response.text
    # save metadata to context['result']
    context['result'] = {{{{
        'url': url,
        'status': response.status_code,
        'length': len(response.text)
    }}}}
    return response.text


@parse()
def parse_data(context: Context):
    """Parse HTML content to extract data."""
    content = context.get('content', '')
    
    # TODO: implement parsing logic
    # Example: extract title, links, etc.
    data = {{{{
        'title': 'Example Title',
        'items': []
    }}}}
    
    # save parsed data to context['data']
    context['data'] = data
    return data


@extract()
def save_data(context: Context):
    """Save parsed data to database or file."""
    data = context.get('data', {{}})
    
    # TODO: implement save logic
    # Example: save to database, write to file, etc.
    # db = context.initial.get('db')
    # db.save(data)
    
    return f"Saved {{{{len(data)}}}} items"


# Step lists for each stage
ACTION_LIST = [
    'fetch_page',
]

PARSE_LIST = [
    'parse_data',
]

EXTRACT_LIST = [
    'save_data',
]


if __name__ == '__main__':
    # Default: run action stage only
    run_plan(initial_spider, initial_task, initial_plan, 
             actions=ACTION_LIST, plan_name='{name}')
    
    # Uncomment to run parse stage
    # run_plan(initial_task=initial_task, initial_plan=initial_plan,
    #          parses=PARSE_LIST, plan_name='{name}')
    
    # Uncomment to run extract stage
    # run_plan(initial_task=initial_task, initial_plan=initial_plan,
    #          extracts=EXTRACT_LIST, plan_name='{name}')
'''
