"""
Simple spider usage example.

Minimal code to fetch and save page content.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_tools import load, save
from auto_spider.components import RequestSpider


def spider_simple_main():
    input_data = load()
    
    # Step 1: Create spider
    spider = RequestSpider()
    spider.attach()
    
    # Step 2: Fetch URL
    url = input_data.get('url')
    response = spider.do_url(url, retry=2)
    
    # Step 3: Extract basic info
    html = response.text
    title_start = html.find('<title>')
    title_end = html.find('</title>')
    title = html[title_start + 7:title_end] if title_start != -1 else 'No title'
    
    # Step 4: Cleanup
    spider.detach()
    
    # Step 5: Save
    save({
        'url': url,
        'title': title,
        'html_length': len(html),
        'status_code': response.status_code
    })


if __name__ == "__main__":
    spider_simple_main()
