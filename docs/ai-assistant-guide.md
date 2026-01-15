# AI Assistant Guide for Auto Spider

> **核心规范文档 - AI 助手在使用 Auto Spider 前必读**

## 🚫 禁止事项

### 不要写独立脚本
```python
# ❌ 错误 - 不要这样写
from bs4 import BeautifulSoup
import requests

def scrape_page():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
```

**原因**: 忽略框架、不可维护、浪费时间

### 不要使用 requirements.txt 之外的依赖
```python
# ❌ 错误
from bs4 import BeautifulSoup  # 不在 requirements.txt
import scrapy                   # 不在 requirements.txt
```

### 不要跳过 Skills
开始任务前必须阅读相关 skills。

---

## ✅ 正确做法

### 使用 Auto Spider 框架
```python
# ✅ 正确
from auto_spider import action, parse, extract, Context

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    context['content'] = content
    context['result'] = {'url': url}

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    context['result'] = parsed_data

@extract()
def save_data(context: Context):
    data = context.get('input', {})
    # 保存到数据库/文件
```

---

## 🔧 可用工具

### Spider 类型
```python
# 静态页面 (快)
from auto_spider.components import RequestSpider

# 动态页面 (JS 渲染)
from auto_spider.components import PlaywrightSpider
```

### 解析工具
```python
# XPath 提取
from auto_spider.tools.xpath import xpath_extract

# HTML 清洗
from auto_spider.tools.html_cleaner import clean_html
```

### 页面信息 (仅 PlaywrightSpider)
```python
# 获取交互元素、选择器、位置
page_info = context.spider.get_page_info()
```

---

## 📝 任务日志规范

### 文件位置
```
TASK_{task_name}_log.md
```

### 头部格式
```markdown
# 任务: {任务描述}

- **目标**: {详细目标}
- **创建时间**: {YYYY-MM-DD HH:MM}
- **状态**: 进行中 / 已完成 / 失败

## 原始需求
{用户原话，一字不改}

## 计划列表
| 计划名称 | 用途 | 状态 |
|---------|------|------|
| plan_xxx | xxx | 待执行 |
```

### 步骤格式
```markdown
## 步骤 {N}: {标题}

- **时间**: {YYYY-MM-DD HH:MM}
- **计划**: {计划名称}
- **阶段**: 侦察 / Action / Parse / Extract / 验证
- **目的**: {目标}
- **预期**: {成功标志}

### 执行操作
{命令/修改的文件}

### 结果
- **状态**: 成功 / 失败
- **实际**: {实际发生}
- **文件**: {文件列表}

### 备注
{观察/问题/决策}
```

---

## 🎯 决策树

```
用户分配任务
    ↓
新任务? → 创建 TASK_xxx_log.md
    ↓
侦察过页面? → 否 → scout-webpage skill
    ↓
有 plan? → 否 → generate-plan skill
    ↓
执行哪个步骤?
    Action → action-step skill
    Parse → parse-step skill
    Extract → extract-step skill
    ↓
每步操作后更新日志
```

---

## 📚 Skills 阅读顺序

1. **本文档** (ai-assistant-guide)
2. **scout-webpage** - 侦察新页面
3. **generate-plan** - 生成项目结构
4. **action-step** - 下载 HTML
5. **parse-step** - 提取数据
6. **extract-step** - 保存数据
7. **run-and-verify** - 运行和验证

---

## ⚠️ 核心原则

1. **一个 Plan 干一件事**: 每个 plan 只完成一个明确的目标
2. **先侦察后编码**: 新页面必须先 scout
3. **渐进式实现**: 从最简单的 action 开始，按需添加复杂度
4. **记录每一步**: 日志中记录所有原子操作
