---
name: sense-page-info
description: Analyze page_info data to understand interactive elements. Use after scout or action to find buttons, links, selectors.
---

# Sense Page Info

> Analyze `page_info` from scout output to understand interactive elements on the page.

## When to Use
- After `sense-scout` to understand what buttons/links/forms exist
- Need to find CSS/XPath selectors for interactive elements
- Deciding whether Playwright interactions are needed

---

## Input

Read `page_info` from scout output:

```python
import json
from pathlib import Path

# find latest action output
action_dir = sorted(Path('output/scout_xxx').glob('action_*'))[-1]
data = json.loads((action_dir / 'task1_action.json').read_text(encoding='utf-8'))
page_info = data.get('page_info', {})
```

## What page_info Contains

```python
{
    'title': 'Page Title',
    'url': 'https://...',
    'elements': [
        {
            'index': 0,
            'tag': 'a',
            'text': 'Link Text',
            'css': 'a.nav-link',
            'xpath': '//a[@class="nav-link"]',
            'position': {'x': 100, 'y': 200}
        },
        # ...
    ]
}
```

## Analysis Script

```python
# scripts/analyze_page_info.py
"""Analyze page_info from scout output."""
import json
from pathlib import Path

def analyze(action_json_path):
    data = json.loads(Path(action_json_path).read_text(encoding='utf-8'))
    page_info = data.get('page_info', {})
    elements = page_info.get('elements', [])

    # group by tag
    tags = {}
    for el in elements:
        tag = el.get('tag', 'unknown')
        tags.setdefault(tag, []).append(el)

    print(f"Title: {page_info.get('title')}")
    print(f"URL: {page_info.get('url')}")
    print(f"Total elements: {len(elements)}")
    print()
    for tag, items in sorted(tags.items(), key=lambda x: -len(x[1])):
        print(f"  <{tag}>: {len(items)}")
        for item in items[:3]:
            print(f"    - {item.get('text', '')[:60]}  |  css: {item.get('css', '')}")

if __name__ == '__main__':
    analyze('output/scout_xxx/action_xxx/task1_action.json')
```

## Key Decisions from page_info

| Finding | Implication |
|---------|------------|
| No interactive elements | Static page, use RequestSpider |
| Load More button exists | May need click, but check HTML first |
| Form inputs found | May need login or search interaction |
| Many `<a>` links | Good for incremental crawl |

**Remember**: Finding a button does NOT mean you need to click it. Always check if the data is already in the static HTML first.

## Related Skills
- `sense-scout` — Scout page first
- `sense-clean-html` — Analyze HTML structure
- `write-action` — Write action steps
