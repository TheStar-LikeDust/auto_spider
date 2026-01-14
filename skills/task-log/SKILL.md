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
Create a log file at the project root (use Chinese for user's language):
```
TASK_{task_name}_log.md
```

Example: `TASK_电商产品数据_log.md`

## Log Format

### File Header (Chinese)
```markdown
# 任务: {任务描述}

- **目标**: {用户想要实现的目标}
- **创建时间**: {YYYY-MM-DD HH:MM}
- **状态**: 进行中 / 已完成 / 失败

## 计划列表
| 计划名称 | 用途 | 状态 |
|---------|------|------|
| plan_scout_xxx | 侦察页面结构 | 完成 |
| plan_xxx | 主爬虫计划 | 进行中 |

---
```

### Step Entry Format (Chinese)
```markdown
## 步骤 {N}: {步骤标题}

- **时间**: {YYYY-MM-DD HH:MM}
- **计划**: {计划名称 或 "无"}
- **阶段**: 侦察 / Action / Parse / Extract / 验证 / 迭代
- **目的**: {这一步要实现什么}
- **预期**: {成功后应该看到什么}

### 执行操作
{描述做了什么}

### 结果
- **状态**: 成功 / 部分成功 / 失败
- **实际**: {实际发生了什么}
- **文件**: {创建/修改的文件列表}

### 备注
{任何观察、问题或决策}

---
```

## Example Log (Chinese)

```markdown
# 任务: 抓取电商产品数据

- **目标**: 从 example-shop.com 提取所有产品信息（名称、价格、链接）
- **创建时间**: 2024-01-15 10:30
- **状态**: 进行中

## 计划列表
| 计划名称 | 用途 | 状态 |
|---------|------|------|
| plan_scout_shop | 侦察产品页面 | 完成 |
| plan_shop | 主爬虫 | 进行中 |

---

## 步骤 1: 侦察目标页面

- **时间**: 2024-01-15 10:32
- **计划**: plan_scout_shop
- **阶段**: 侦察
- **目的**: 了解页面结构，找到产品列表选择器
- **预期**: 获取产品项、价格、标题的 CSS/XPath

### 执行操作
生成单文件侦察计划，headless=False 运行。

### 结果
- **状态**: 成功
- **实际**: 找到 20 个产品项，识别出选择器：
  - 产品容器: `div.product-card`
  - 标题: `h2.product-title`
  - 价格: `span.price`
- **文件**: `plan_scout_shop.py`, `output/scout_shop_action_*/`

### 备注
页面使用懒加载，需要滚动。

---

## 步骤 2: 生成主计划

- **时间**: 2024-01-15 10:40
- **计划**: plan_shop
- **阶段**: 生成
- **目的**: 创建主爬虫计划结构
- **预期**: 带有 action/parse/extract 步骤的计划文件

### 执行操作
`python -m auto_spider generate shop`

### 结果
- **状态**: 成功
- **实际**: 生成了 plan_shop.py 和 steps_shop/
- **文件**: `plan_shop.py`, `steps_shop/`

### 备注
无

---

## 步骤 3: 编写 Action 步骤

- **时间**: 2024-01-15 10:45
- **计划**: plan_shop
- **阶段**: Action
- **目的**: 下载加载所有商品的产品列表页
- **预期**: HTML 文件包含所有 50 个产品

### 执行操作
基于侦察结果，在 action 步骤中添加滚动逻辑。

### 结果
- **状态**: 成功
- **实际**: 滚动后 HTML 包含所有 50 个产品
- **文件**: `steps_shop/action.py`, `output/shop_action_*/task1.html`

### 备注
5 次滚动，每次间隔 500ms 已足够。

---
```

## When to Update Log

| 事件 | 操作 |
|------|------|
| 用户分配任务 | 创建日志文件和头部 |
| 创建新计划 | 添加到计划列表 |
| 每步执行前 | 添加步骤条目，写明目的/预期 |
| 每步执行后 | 填写结果/实际/备注 |
| 任务完成 | 更新头部状态为"已完成" |

## Related Skills
- `scout-webpage` - Scout new webpages
- `complete-workflow` - Overall workflow
- `verify-step-output` - Verify each step
- `iterate-next-step` - Decision making
