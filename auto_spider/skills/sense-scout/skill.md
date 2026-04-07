---
name: sense-scout
description: Scout a new webpage to get selectors and structure. Use before writing action/parse steps.
---

# Sense Scout

> Use auto_spider's default plan template to scout a new page. This is always the FIRST step.

## When to Use
- Starting a new scraping task
- Need to understand page structure before writing code
- Want to check if target data exists in static HTML

---

## Steps

### 1. Generate a scout plan

```bash
auto-spider generate scout_<target>
```

This creates `scout_<target>.py` — a single-file plan with built-in scout action.

### 2. Edit the plan

Only change `initial_task()` to point to your target URL:

```python
def initial_task():
    return [
        Task(url='https://target-site.com/page'),
    ]
```

### 3. Run scout

```bash
auto-spider run scout_<target> --action
```

### 4. Check output

Output directory: `output/scout_<target>/action_<timestamp>/`

Files:
- `task1.html` — raw HTML
- `task1_action.json` — contains `markdown`, `cleaned_html`, `page_info`
- `task1_task.json` — original task

---

## What the Default Template Collects

The default `fetch_page` action in the template automatically collects:

| Key | Content | Purpose |
|-----|---------|---------|
| `markdown` | trafilatura extracted content | Quick view of page structure |
| `cleaned_html` | Cleaned HTML (scripts/styles removed) | XPath selector derivation |
| `page_info` | CDP interactive elements | Buttons, links, forms |

---

## After Scout

Use the other sense skills to analyze the output:
- `sense-page-info` — Analyze interactive elements from `page_info`
- `sense-clean-html` — Analyze DOM structure from `cleaned_html`

Then proceed to write action/parse/extract steps.

## Related Skills
- `sense-page-info` — Analyze page_info data
- `sense-clean-html` — Analyze cleaned HTML
- `plan-generate` — Generate plan template
- `write-action` — Write action steps
