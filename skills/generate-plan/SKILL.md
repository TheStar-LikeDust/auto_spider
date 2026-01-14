---
name: generate-plan
description: Generate an Auto Spider plan template (single-file or multi-file). Keywords: generate plan, scaffold, template, start project.
allowed-tools: Read, Grep, Glob, Bash
---

# Generate Plan

## When to Use
- Starting a new scraping project
- Need a plan template with `action/parse/extract`
- Want to scaffold a single-file plan for quick experiments

## Core Patterns

### Generate Multi-File Project
```bash
python -m auto_spider generate myplan
```

Creates:
```
steps_myplan/
  __init__.py
  action.py
  parse.py
  extract.py
plan_myplan.py
```

### Generate Single-File Plan
```bash
python -m auto_spider generate myplan --single-file
```

Creates:
```
plan_myplan.py
```

## Notes
- `plan_myplan.py` contains `PLAN_CONFIG`, `initial_spider()`, `initial_task()`, `initial_plan()`.
- Choose `PlaywrightSpider` for dynamic pages, `RequestSpider` for static pages.

## Related Skills
- `scout-webpage`
- `action-step`
- `config-and-run`
