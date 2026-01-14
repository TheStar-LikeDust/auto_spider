---
name: parse-step
description: Write parse steps to extract structured data from HTML using XPath/BS4/regex. Keywords: parse step, xpath, extract fields, clean html.
allowed-tools: Read, Grep, Glob, Bash
---

# Parse Step

## When to Use
- Convert HTML into structured data (dict/list)
- Need XPath extraction or alternative parsers
- Need to validate completeness (fields not empty)

## File Location

After `python -m auto_spider generate myplan`:
- Multi-file: `steps_myplan/parse.py`
- Single-file: `plan_myplan.py` (inline `@parse()` function)

## Core Patterns

### Default Template (generated)
```python
from auto_spider import parse, Context

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    action_result = context.get('input', {})

    data = extract_from_html(content)
    context['result'] = data
```

### XPath Extraction
```python
from auto_spider.tools.xpath import xpath_extract

@parse()
def parse_article(context: Context):
    content = context.get('content', '')

    title = xpath_extract(content, '//h1//text()')
    context['result'] = {'title': title[0] if title else ''}
```

### Clean HTML Before Parse
```python
from auto_spider.tools.html_cleaner import clean_html
from auto_spider.tools.xpath import xpath_extract

@parse()
def parse_clean(context: Context):
    content = context.get('content', '')
    cleaned = clean_html(content)

    titles = xpath_extract(cleaned['html'], '//h1//text()')
    context['result'] = {'title': titles[0] if titles else ''}
```

## Output
- `context['result']` -> `taskX_parse.json`

## Related Skills
- `verify-step-output`
- `iterate-next-step`
- `extract-step`
