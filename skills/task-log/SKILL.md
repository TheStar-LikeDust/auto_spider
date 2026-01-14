---
name: task-log
description: Create and maintain a markdown progress log for user tasks. One task may involve multiple plans. Records each step with timestamp, purpose, expected result, and actual result. Keywords: log, progress, record, timeline, history, markdown log, task.
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Task Log

> Record every step of a user task as a markdown log file. One task may involve multiple plans (e.g., scout plan + main plan).

## When to Use
- When user assigns a scraping task
- Need to track progress across multiple plans
- Want a history of what was tried and what worked
- Debugging issues by reviewing past attempts

## Log File Location
Create a log file at the project root:
```
TASK_{task_name}_log.md
```

Example: `TASK_ecommerce_scraper_log.md`

## Log Format

### File Header
```markdown
# Task: {Task Description}

- **Goal**: {What user wants to achieve}
- **Created**: {YYYY-MM-DD HH:MM}
- **Status**: In Progress / Completed / Failed

## Plans
| Plan | Purpose | Status |
|------|---------|--------|
| plan_scout_xxx | Scout page structure | Done |
| plan_xxx | Main scraping plan | In Progress |

---
```

### Step Entry Format
```markdown
## Step {N}: {Step Title}

- **Time**: {YYYY-MM-DD HH:MM}
- **Plan**: {plan name or "N/A"}
- **Stage**: Scout / Action / Parse / Extract / Verify / Iterate
- **Purpose**: {What this step aims to achieve}
- **Expected**: {What we expect to see if successful}

### Actions Taken
{Description of what was done}

### Result
- **Status**: Success / Partial / Failed
- **Actual**: {What actually happened}
- **Files**: {List of files created/modified}

### Notes
{Any observations, issues, or decisions made}

---
```

## Example Log

```markdown
# Task: Scrape E-commerce Product Data

- **Goal**: Extract all product info (name, price, url) from example-shop.com
- **Created**: 2024-01-15 10:30
- **Status**: In Progress

## Plans
| Plan | Purpose | Status |
|------|---------|--------|
| plan_scout_shop | Scout product page | Done |
| plan_shop | Main scraping | In Progress |

---

## Step 1: Scout Target Page

- **Time**: 2024-01-15 10:32
- **Plan**: plan_scout_shop
- **Stage**: Scout
- **Purpose**: Understand page structure, find product list selectors
- **Expected**: Get CSS/XPath for product items, prices, titles

### Actions Taken
Generated single-file scout plan, ran with headless=False.

### Result
- **Status**: Success
- **Actual**: Found 20 product items, identified selectors:
  - Product container: `div.product-card`
  - Title: `h2.product-title`
  - Price: `span.price`
- **Files**: `plan_scout_shop.py`, `output/scout_shop_action_*/`

### Notes
Page uses lazy loading, need to scroll.

---

## Step 2: Generate Main Plan

- **Time**: 2024-01-15 10:40
- **Plan**: plan_shop
- **Stage**: Generate
- **Purpose**: Create main scraping plan structure
- **Expected**: Plan files with action/parse/extract steps

### Actions Taken
`python -m auto_spider generate shop`

### Result
- **Status**: Success
- **Actual**: Generated plan_shop.py and steps_shop/
- **Files**: `plan_shop.py`, `steps_shop/`

### Notes
N/A

---

## Step 3: Write Action Step

- **Time**: 2024-01-15 10:45
- **Plan**: plan_shop
- **Stage**: Action
- **Purpose**: Download product listing page with all items loaded
- **Expected**: HTML file with all 50 products visible

### Actions Taken
Added scroll logic to action step based on scout findings.

### Result
- **Status**: Success
- **Actual**: HTML contains all 50 products after scrolling
- **Files**: `steps_shop/action.py`, `output/shop_action_*/task0.html`

### Notes
5 scroll iterations with 500ms delay was sufficient.

---
```

## When to Update Log

| Event | Action |
|-------|--------|
| User assigns task | Create log file with header |
| Create new plan | Add to Plans table |
| Before each step | Add step entry with Purpose/Expected |
| After each step | Fill in Result/Actual/Notes |
| Task complete | Update Status in header to "Completed" |

## Related Skills
- `scout-webpage` - Scout new webpages
- `complete-workflow` - Overall workflow
- `verify-step-output` - Verify each step
- `iterate-next-step` - Decision making
