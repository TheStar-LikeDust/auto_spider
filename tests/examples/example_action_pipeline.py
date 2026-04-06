"""
Complete plan example.

Shows plan module with 3 fixed functions + actions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auto_spider import Context, action, parse
from auto_spider.core import Task, run_plan, PlanConfig
from auto_spider.components import RequestSpider

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'example_pipeline'
PLAN_CONFIG.MAX_WORKERS = 2
PLAN_CONFIG._action_steps = ['fetch_page']
PLAN_CONFIG._parse_steps = ['parse_html']
PLAN_CONFIG._extract_steps = []


def initial_spider():
    """Create and return spider instance."""
    return RequestSpider()


def initial_task():
    """Create and return task list."""
    urls = [
        'https://example.com',
        'https://example.org',
    ]
    
    return [Task(name=f'task_{i}', url=url) for i, url in enumerate(urls)]


def initial_plan():
    """Initialize and return resources object."""
    return {}


@action()
def fetch_page(context: Context):
    """Fetch page from task url."""
    url = context.task['url']
    response = context.spider.do_url(url, retry=2)
    context['result'] = response.text
    return response.text


@parse()
def parse_html(context: Context):
    """Parse HTML and extract info."""
    html = context['result']
    
    start = html.find('<title>')
    end = html.find('</title>')
    title = html[start + 7:end] if start != -1 else 'No title'
    
    link_count = html.count('<a ')
    
    result = {'title': title, 'link_count': link_count}
    context['result'] = result
    return result


def action_pipeline_main():
    # Step 1: Action stage (download)
    print("=== Action Stage: Download ===")
    run_plan(initial_spider, initial_task, initial_plan,
             plan_config=PLAN_CONFIG, action=True)
    
    # Step 2: Parse stage (parse HTML)
    print("\n=== Parse Stage: Parse HTML ===")
    run_plan(initial_spider, initial_task, initial_plan,
             plan_config=PLAN_CONFIG, parse=True)
    
    print("\nPipeline completed! Check output/example_pipeline_*/ for results")


if __name__ == '__main__':
    action_pipeline_main()
