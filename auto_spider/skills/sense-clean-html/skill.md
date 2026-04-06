---
name: sense-clean-html
description: Analyze cleaned HTML to understand DOM structure. Use after action to find XPath patterns for parse step.
---

# Sense Clean HTML

> Analyze `cleaned_html` from scout output to understand DOM structure and derive XPath selectors.

## When to Use
- After `sense-scout` to understand HTML structure
- Need to derive XPath selectors for parse step
- Want to verify target data exists in static HTML

---

## Input

Read `cleaned_html` from scout output:

```python
import json
from pathlib import Path

action_dir = sorted(Path('output/scout_xxx').glob('action_*'))[-1]
data = json.loads((action_dir / 'task1_action.json').read_text(encoding='utf-8'))
cleaned_html = data.get('cleaned_html', '')
```

## What cleaned_html Contains

HTML with these removed:
- `<script>`, `<style>`, `<meta>`, `<link>`, `<noscript>`, `<svg>`, `<iframe>`, comments

Preserved attributes: `id`, `class`, `href`, `src`, `alt`, `title`, `name`, `type`, `value`, `placeholder`

## Analysis: Check Data Existence

```python
# scripts/analyze_html.py
"""Analyze cleaned HTML for target data."""
from pathlib import Path
import json
import re

def check_data(action_json_path, keywords):
    data = json.loads(Path(action_json_path).read_text(encoding='utf-8'))
    html = data.get('cleaned_html', '')

    print(f"HTML length: {len(html)} chars")
    print()
    for kw in keywords:
        count = html.lower().count(kw.lower())
        print(f"  '{kw}': {count} occurrences")

    # check links
    links = re.findall(r'href="([^"]+)"', html)
    print(f"\nTotal links: {len(links)}")
    for link in links[:5]:
        print(f"  {link}")

if __name__ == '__main__':
    check_data(
        'output/scout_xxx/action_xxx/task1_action.json',
        keywords=['product', 'price', 'title']
    )
```

## Analysis: Test XPath

```python
# scripts/test_xpath.py
"""Test XPath selectors on cleaned HTML."""
from pathlib import Path
import json
from auto_spider.tools.xpath import xpath_extract

def test(action_json_path, xpaths):
    data = json.loads(Path(action_json_path).read_text(encoding='utf-8'))
    html = data.get('cleaned_html', '')

    for xpath, desc in xpaths:
        results = xpath_extract(html, xpath)
        print(f"{desc}: {len(results)} matches")
        for r in results[:3]:
            text = str(r)[:80]
            print(f"  {text}")
        print()

if __name__ == '__main__':
    test('output/scout_xxx/action_xxx/task1_action.json', [
        ('//h1//text()', 'Title'),
        ('//a/@href', 'Links'),
        ('//div[@class="item"]', 'Items'),
    ])
```

## Key Decisions from cleaned_html

| Finding | Implication |
|---------|------------|
| Target data found in HTML | Static page, RequestSpider sufficient |
| Data count matches expectation | No need for scroll/click |
| Data missing from HTML | May need Playwright for JS rendering |
| HTML has CSS-hidden sections | Data exists but hidden — still extractable |

**Remember**: CSS `display:none` does NOT mean data is missing. The HTML still contains it.

## Related Skills
- `sense-scout` — Scout page first
- `sense-page-info` — Analyze interactive elements
- `write-parse` — Write parse steps with XPath
- `analyze-script` — Complex analysis scripts
