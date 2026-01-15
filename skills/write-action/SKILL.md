---
name: write-action
description: Write action steps to download HTML. Use when implementing fetch, login, pagination, or lazy load.
---

# Write Action

## When to Use
- Need to download HTML content
- Page requires JS rendering / login / scrolling
- Need to enqueue more tasks (incremental crawl)

## File Location

After `python -m auto_spider generate myplan`:
- Multi-file: `steps_myplan/action.py`
- Single-file: `plan_myplan.py` (inline `@action()` function)

## Progressive Approach

**⚠️ Always start simple, add complexity only when needed.**

### Level 1: Basic Fetch (Start Here)
```python
from auto_spider import action, Context

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    context['content'] = content
    context['result'] = {'url': url}
```

**Use this first.** Verify output before adding more features.

### Level 2: Wait for Content (if Level 1 fails)
Only add if basic fetch returns empty/incomplete HTML.

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

### Level 3: Lazy Loading (if content loads progressively)
```python
@action()
def fetch_lazy_load(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task['url'])

    # Scroll to trigger lazy loading
    for _ in range(5):
        page.evaluate('window.scrollBy(0, 1000)')
        page.wait_for_timeout(500)

    context['content'] = page.content()
```

### Level 4: Click Actions (if interactive elements required)
```python
@action()
def fetch_with_click(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task['url'])

    # Click "Load More" button
    page.click('.load-more-btn')
    page.wait_for_timeout(1000)

    context['content'] = page.content()
```

### Level 5: Login/Complex Interactions
```python
@action()
def fetch_with_login(context: Context):
    page = context.spider.get_driver()

    # Login first
    page.goto('https://example.com/login')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')
    page.wait_for_url('**/dashboard')

    # Then fetch target page
    page.goto(context.task['url'])
    context['content'] = page.content()
```

## Advanced Patterns

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

## Decision Tree

```
1. Start with Level 1 (basic fetch)
   ↓
2. Run and verify output
   ↓
3. Is HTML complete?
   YES → Done, move to parse
   NO  → Continue
   ↓
4. Is content delayed (AJAX)?
   YES → Add Level 2 (wait for selector)
   NO  → Continue
   ↓
5. Is content lazy-loaded (scroll)?
   YES → Add Level 3 (scroll)
   NO  → Continue
   ↓
6. Need click interactions?
   YES → Add Level 4 (click)
   NO  → Continue
   ↓
7. Need login/complex flow?
   YES → Add Level 5 (login)
```

**Never skip levels.** Build incrementally.

## Output
- `context['content']` -> `taskX.html`
- `context['result']` -> `taskX_action.json`

## Related Skills
- `exec-run-verify` - 运行和验证
- `write-parse` - 编写 parse
- `sense-scout` - 侦察页面
- `log-task` - 记录任务
