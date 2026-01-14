---
name: action-step
description: Write Auto Spider action steps to download HTML (PlaywrightSpider/RequestSpider). Keywords: action step, download, fetch, login, pagination, lazy load.
allowed-tools: Read, Grep, Glob, Bash
---

# Action Step

## When to Use
- Need to download HTML content
- Page requires JS rendering / login / scrolling
- Need to enqueue more tasks (incremental crawl)

## File Location

After `python -m auto_spider generate myplan`:
- Multi-file: `steps_myplan/action.py`
- Single-file: `plan_myplan.py` (inline `@action()` function)

## Core Patterns

### Default Template (generated)
```python
from auto_spider import action, Context

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    context['content'] = content
    context['result'] = {'url': url, 'status': 'success'}
```

### Wait for Element (dynamic page)
```python
@action()
def fetch_with_wait(context: Context):
    url = context.task.get('url')
    page = context.spider.get_driver()

    page.goto(url)
    page.wait_for_selector('.content', timeout=10000)

    context['content'] = page.content()
    context['result'] = {'url': url}
```

### Lazy Loading (scroll)
```python
@action()
def fetch_lazy_load(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task['url'])

    for _ in range(5):
        page.evaluate('window.scrollBy(0, 1000)')
        page.wait_for_timeout(500)

    context['content'] = page.content()
```

### Incremental Crawl (append tasks)
```python
@action()
def fetch_list_and_enqueue(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    detail_urls = extract_detail_urls(content)
    for detail_url in detail_urls:
        context.tasks.append({'url': detail_url, 'type': 'detail'})

    context['content'] = content
    context['result'] = {'detail_count': len(detail_urls)}
```

## Output
- `context['content']` -> `taskX.html`
- `context['result']` -> `taskX_action.json`

## Related Skills
- `verify-step-output`
- `iterate-next-step`
- `parse-step`
