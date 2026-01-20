---
name: exec-run-verify
description: Run stages and verify output. Use when executing action/parse/extract and checking results.
---

# Exec Run Verify

> 运行阶段、验证输出、决策下一步的完整执行流

## When to Use
- 运行 action/parse/extract 阶段
- 检查输出是否正确
- 决定修复还是继续

## 执行流

```
1. 运行阶段
      ↓
2. 验证输出
      ↓
3. 输出正确? 
   YES → 进入下一阶段
   NO  → 修复代码，重新运行
```

---

## Step 1: 运行阶段

### 命令格式（推荐 CLI）
```bash
# 运行 action
auto-spider run plan_xxx.py fetch_page --stage action

# 运行 parse
auto-spider run plan_xxx.py parse_data --stage parse

# 运行 extract
auto-spider run plan_xxx.py save_data --stage extract

# 重试失败任务
auto-spider run plan_xxx.py fetch_page --stage action --retry-failed
```

### 配置参数
```python
from auto_spider import PlanConfig

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'
PLAN_CONFIG.OUTPUT_DIR = 'output'
PLAN_CONFIG.MAX_WORKERS = 4
PLAN_CONFIG.RATE_LIMIT = 1.0
PLAN_CONFIG.STORAGE_TIMESTAMP = True
PLAN_CONFIG.TASK_RETRY_COUNT = 3      # 任务重试次数（1次初始 + 2次重试）
```

---

## Step 2: 验证输出

### Action 输出验证
```bash
# 检查 HTML 文件大小
ls -lh output/myplan_action_*/task1.html

# 搜索目标内容
grep -l "target-keyword" output/myplan_action_*/task1.html
```

**检查点**:
- HTML 文件是否存在且不太小 (>1KB)
- 是否包含目标内容关键词
- 是否有完整的 DOM 结构

### Parse 输出验证
```bash
# 查看 JSON 结果
cat output/myplan_parse_*/task1_parse.json
```

**检查点**:
- JSON 字段是否完整
- 列表长度是否符合预期
- 值是否为空或 null

### Extract 输出验证
- 检查数据库行数
- 检查文件是否生成
- 检查 API 调用是否成功

---

## Step 3: 决策迭代

### 输出正确 → 继续下一阶段
```
Action OK → Parse
Parse OK → Extract
Extract OK → 完成
```

### 输出错误 → 修复代码

| 问题 | 可能原因 | 修复方案 |
|------|---------|---------|
| HTML 太小/为空 | 页面未加载完成 | 添加 `wait_for_selector` |
| 内容不完整 | 懒加载 | 添加滚动逻辑 |
| 需要登录 | 未认证 | 添加登录步骤 |
| JSON 字段为空 | XPath 错误 | 调试选择器 |
| 列表长度为 0 | 选择器不匹配 | 使用 page_info 检查 |

### 调试技巧

**使用 page_info 检查交互元素**:
```python
page_info = context.spider.get_page_info()
print(f"Found {len(page_info.get('elements', []))} elements")
```

**使用 clean_html 简化分析**:
```python
from auto_spider.tools.html_cleaner import clean_html
cleaned = clean_html(content)
# 查看 cleaned['body'] 分析结构
```

**XPath 调试**:
```python
# 尝试不同变体
titles = xpath_extract(content, '//h1/text()')      # 直接文本
titles = xpath_extract(content, '//h1//text()')     # 嵌套文本
titles = xpath_extract(content, '//h1')             # 整个元素
```

---

## 完整示例

```markdown
## 步骤 4: 运行并验证 Action

- **时间**: 2024-01-15 11:00
- **计划**: plan_shop
- **阶段**: Action + 验证
- **目的**: 下载产品列表页并验证

### 执行操作
1. 运行: `python plan_shop.py`
2. 检查: `ls -lh output/shop_action_*/task1.html`

### 结果
- **状态**: 失败
- **实际**: HTML 只有 5KB，缺少产品内容
- **原因**: 页面使用懒加载

### 修复
添加滚动逻辑到 action 步骤，重新运行

---

## 步骤 5: 重新运行 Action

### 执行操作
1. 修改 action.py 添加滚动
2. 运行: `python plan_shop.py`
3. 检查: `grep "product-card" output/shop_action_*/task1.html | wc -l`

### 结果
- **状态**: 成功
- **实际**: 找到 50 个 product-card
```

---

## Related Skills
- `write-action` - 编写 action 代码
- `write-parse` - 编写 parse 代码
- `write-extract` - 编写 extract 代码
- `sense-page-info` - 调试时分析交互元素
- `sense-clean-html` - 调试时分析 HTML
- `log-task` - 记录执行结果
