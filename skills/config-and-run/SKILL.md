---
name: config-and-run
description: Configure PlanConfig and run action/parse/extract via CLI or direct run_plan. Keywords: run plan, PlanConfig, workers, rate limit.
allowed-tools: Read, Grep, Glob, Bash
---

# Config and Run

## When to Use
- Ready to execute a plan stage
- Need to tune concurrency / rate limit
- Need to rerun stages or retry failed tasks

## Core Patterns

### Minimal PlanConfig
```python
from auto_spider import PlanConfig

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'
PLAN_CONFIG.OUTPUT_DIR = 'output'
PLAN_CONFIG.MAX_WORKERS = 4
PLAN_CONFIG.RATE_LIMIT = 1.0
PLAN_CONFIG.STORAGE_TIMESTAMP = True
```

### Run via CLI
```bash
python -m auto_spider run plan_myplan.py fetch_page -s action
python -m auto_spider run plan_myplan.py parse_data -s parse
python -m auto_spider run plan_myplan.py save_data -s extract
```

## Related Skills
- `generate-plan`
- `verify-step-output`
- `complete-workflow`
