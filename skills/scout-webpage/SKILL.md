---
name: scout-webpage
description: Scout any new webpage using a reusable single-file plan. Uses PlaywrightSpider CDP to get interactive elements, selectors, and page structure. Keywords: scout, reconnaissance, selectors, xpath, css, new page, explore.
allowed-tools: Read, Grep, Glob, Bash
---

# Scout Webpage

> Use this skill to scout **every new webpage** before writing scraping code.

## When to Use
- **Any new webpage** that needs to be scraped
- Before writing `action/parse` steps
- Need CSS/XPath selectors for target data
- Debugging why a page is empty / missing content

## Usage

### 1. Generate Scout Plan (once per project)
```bash
python -m auto_spider generate scout --single-file
```

Creates `plan_scout.py` with default template.

### 2. Modify for Scouting

Edit `plan_scout.py`:

```python
# Change initial_task() to target URL
def initial_task():
    return [Task(url='https://target-site.com/page')]

# Modify fetch_page() to add screenshot and get_page_info()
@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    page = context.spider.get_driver()

    page.goto(url)
    page.wait_for_load_state('networkidle')

    # Get interactive elements via CDP
    page_info = context.spider.get_page_info()

    # Take screenshot
    page.screenshot(path='output/scout_screenshot.png', full_page=True)

    context['content'] = page.content()
    context['result'] = {
        'url': url,
        'title': page_info.get('title'),
        'elements': page_info.get('elements', []),
    }
```

### 3. Run Scout
```bash
python plan_scout.py
```

### 4. Analyze page_info Output

**First, read and analyze the page_info JSON:**
```bash
cat output/scout_action_*/task1_action.json
```

**Key analysis points:**
- **Element count**: How many interactive elements found?
- **Element roles**: What types? (button, link, textbox, etc.)
- **Selectors**: Are CSS/XPath selectors specific enough?
- **Naming**: Do element names match visual content?

**Example analysis:**
```json
{
  "title": "Product List",
  "elements": [
    {"index": 1, "role": "button", "name": "Load More", "css": ".load-more"},
    {"index": 2, "role": "link", "name": "Product A", "css": "a.product-link"},
    ...
  ]
}
```

✅ Found "Load More" button → need to click in action step
✅ Product links use `.product-link` → use in parse step

### 5. Check Visual Output
```bash
# View screenshot to verify element positions
output/scout_screenshot.png

# View HTML structure
output/scout_action_*/task1.html
```

## Output: get_page_info() Structure

```json
{
  "title": "Page Title",
  "url": "https://example.com",
  "elements": [
    {
      "index": 1,
      "role": "button",
      "name": "Submit",
      "tag": "button",
      "attributes": {"id": "submit-btn", "class": "btn primary"},
      "position": {"x": 100, "y": 200, "width": 80, "height": 40, "center_x": 140, "center_y": 220},
      "css": "#submit-btn",
      "xpath": "//*[@id=\"submit-btn\"]"
    },
    {
      "index": 2,
      "role": "link",
      "name": "Learn More",
      "tag": "a",
      "attributes": {"href": "/about", "class": "nav-link"},
      "position": {"x": 50, "y": 100, "width": 100, "height": 30, "center_x": 100, "center_y": 115},
      "css": "a.nav-link",
      "xpath": "//a"
    }
  ],
  "analysis_info": {
    "method": "cdp_accessibility_tree",
    "viewport": true,
    "processing_time_ms": 45.2,
    "interactive_elements_found": 25
  }
}
```

## Key Info to Extract from Scout

| Info | Where to Find | Use For |
|------|---------------|---------|
| Interactive elements | `elements[]` | Click targets, form inputs |
| CSS selectors | `elements[].css` | Parse step XPath/CSS |
| Element positions | `elements[].position` | Scroll targets |
| Page structure | `task0.html` | XPath patterns |
| Visual layout | `scout_screenshot.png` | Understanding page |

## Variations

### Scout with Scroll (Lazy Loading)
```python
@action()
def scout_page(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task['url'])

    # Scroll to trigger lazy loading
    for _ in range(5):
        page.evaluate('window.scrollBy(0, 1000)')
        page.wait_for_timeout(500)

    page_info = context.spider.get_page_info()
    page.screenshot(path='output/scout_screenshot.png', full_page=True)

    context['content'] = page.content()
    context['result'] = {
        'url': context.task['url'],
        'title': page_info.get('title'),
        'elements': page_info.get('elements', [])
    }
```

### Scout with Login
```python
@action()
def scout_page(context: Context):
    page = context.spider.get_driver()

    # Login first
    page.goto('https://example.com/login')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')
    page.wait_for_url('**/dashboard')

    # Then scout target page
    page.goto(context.task['url'])
    page.wait_for_load_state('networkidle')

    page_info = context.spider.get_page_info()
    context['content'] = page.content()
    context['result'] = {'elements': page_info.get('elements', [])}
```

## Related Skills
- `task-log` - Record scout results in task log
- `action-step` - Write action based on scout
- `verify-step-output` - Verify scout output
