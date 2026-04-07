---
name: write-action
description: Write action steps to download HTML. Use when implementing fetch, login, pagination, or lazy load.
---

# Write Action

## When to Use
- Need to download HTML content
- Page requires JS rendering / login / scrolling
- Need to enqueue more tasks (incremental crawl)

## ⚠️ 核心原则

**写代码前先思考：是否有更简单的方案？**

| 场景 | 错误做法 | 正确做法 |
|------|---------|----------|
| 看到折叠按钮 | 直接写点击代码 | 先检查 HTML 是否已包含数据 |
| 页面有动效 | 使用 Playwright | 先试 RequestSpider |
| 看到分页 | 写循环点击 | 先检查 API 是否有分页参数 |

**关键思维**：CSS 隐藏 ≠ JS 加载，不要被页面表象迷惑！

## File Location

After `auto-spider generate myplan`:
- Single-file (default): `myplan.py` (inline `@action()` function)
- Multi-file (`--module`): `steps_myplan/action.py`

## Progressive Approach

**⚠️ Always start simple, add complexity only when needed.**

### Level 0: 验证静态数据（必须先做！）

scout 后，先用分析脚本验证数据：

```bash
# 检查 HTML 是否已包含目标数据
grep -c "major\|product" output/action_*/task1.html

# 如果 > 0，说明静态数据已足够，使用 RequestSpider
```

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
0. Scout 后先验证静态数据
   ↓
1. 静态 HTML 包含目标数据？
   YES → 使用 RequestSpider + Level 1
   NO  → 继续
   ↓
2. Start with Level 1 (basic fetch)
   ↓
3. Run and verify output
   ↓
4. Is HTML complete?
   YES → Done, move to parse
   NO  → Continue
   ↓
5. Is content delayed (AJAX)?
   YES → Add Level 2 (wait for selector)
   NO  → Continue
   ↓
6. Is content lazy-loaded (scroll)?
   YES → Add Level 3 (scroll)
   NO  → Continue
   ↓
7. Need click interactions?
   YES → Add Level 4 (click)
   NO  → Continue
   ↓
8. Need login/complex flow?
   YES → Add Level 5 (login)
```

**Never skip levels.** Build incrementally.

## 每步思考检查列表

写代码前问自己：

- [ ] **静态数据检查**：HTML 是否已包含目标数据？
- [ ] **最简方案**：RequestSpider 是否足够？
- [ ] **必要性**：真的需要 Playwright 吗？
- [ ] **验证假设**：我的假设是否正确？

**核心思维**：看到交互元素不代表需要交互！

## Output
- `context['content']` -> `taskX.html`
- `context['result']` -> `taskX_action.json`

## Related Skills
- `sense-scout` - 侦察页面
- `sense-clean-html` - 分析 HTML 结构
- `exec-run-verify` - 运行和验证
- `write-parse` - 编写 parse
