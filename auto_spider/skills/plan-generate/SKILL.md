---
name: plan-generate
description: Generate plan template files. Use when starting a new scraping project.
---

# Plan Generate

## When to Use
- Starting a new scraping project
- Need a plan template with `action/parse/extract`
- Want to scaffold a single-file plan for quick experiments

## Core Patterns

### Generate Single-File Plan (Default)
```bash
auto-spider generate myplan
```

Creates:
```
myplan.py
```

### Generate Multi-File Project
```bash
auto-spider generate myplan --module
```

Creates:
```
steps_myplan/
  __init__.py
  action.py
  parse.py
  extract.py
myplan.py
```

## Notes
- `myplan.py` contains `PLAN_CONFIG`, `initial_spider()`, `initial_task()`, `initial_plan()`.
- Choose `PlaywrightSpider` for dynamic pages, `RequestSpider` for static pages.
- Run with: `auto-spider run myplan --action` (`.py` extension optional)

## Related Skills
- `sense-scout` - 侦察页面
- `write-action` - 编写 action
- `exec-run-verify` - 运行和验证
- `analyze-script` - 复杂分析用独立脚本
