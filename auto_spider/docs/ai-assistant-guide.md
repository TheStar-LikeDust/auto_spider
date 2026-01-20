# AI Assistant Guide for Auto Spider

> **核心规范文档 - AI 助手在使用 Auto Spider 前必读**

## 禁止事项

### 不要写独立爬虫脚本
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

### 数据文件读取优先级
```
1. 先用 sense skill 感知数据存在性
2. 再用 analyze-script 生成分析脚本
3. 最后才考虑直接读取文件（作为最后手段）
```

**原因**: 数据文件可能很大，直接读取会超出 token 限制

---

## 正确做法

### 使用 Auto Spider 框架
```python
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

## 可用工具

### Spider 类型
```python
# 静态页面 (快)
from auto_spider.components import RequestSpider

# 动态页面 (JS 渲染)
from auto_spider.components import PlaywrightSpider
```

### 解析工具
```python
from auto_spider.tools.xpath import xpath_extract
from auto_spider.tools.html_cleaner import clean_html
from auto_spider.tools.html_to_markdown import html_to_markdown
```

### 页面信息 (仅 PlaywrightSpider)
```python
page_info = context.spider.get_page_info()
```

---

## 决策流程

```
用户分配任务
      ↓
创建 TASK_xxx_log.md (log-task skill)
      ↓
感知页面数据 (sense skill)
      ↓
输出数据存在性报告
      ↓
制定采集策略 (strategy skill)
      ↓
生成 plan (plan-generate skill)
      ↓
实现 action/parse/extract (write-* skills)
      ↓
运行并验证 (exec-run-verify skill)
      ↓
失败？调整策略，重试
```

---

## Skills 列表

| Skill | 用途 | 何时使用 |
|-------|------|----------|
| `sense` | 感知数据存在性 | 新页面，了解数据在哪 |
| `strategy` | 制定采集策略 | sense 后，决定方案 |
| `plan-generate` | 生成 plan 结构 | 准备开始写代码 |
| `write-action` | 写 action 步骤 | 下载 HTML |
| `write-parse` | 写 parse 步骤 | 提取数据 |
| `write-extract` | 写 extract 步骤 | 保存数据 |
| `exec-run-verify` | 运行和验证 | 执行并检查结果 |
| `log-task` | 记录任务日志 | 全程记录 |
| `analyze-script` | 复杂分析用独立脚本 | 需要复杂 Python 操作 |

---

## 核心原则

1. **先感知后编码**: 新页面先用 sense 了解数据存在性
2. **从简单开始**: RequestSpider + XPath 优先，失败再升级
3. **感知与决策分离**: sense 只报告数据存在，strategy 制定方案
4. **一个 Plan 干一件事**: 每个 plan 只完成一个明确目标
5. **记录每一步**: 用 log-task 记录所有操作

---

## 任务日志规范

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
{用户原话}

## Sense 结论
{数据存在性报告}

## 采集策略
{方案 A/B/C}
```

### 步骤格式
```markdown
## 步骤 {N}: {标题}

- **时间**: {YYYY-MM-DD HH:MM}
- **阶段**: Sense / Strategy / Action / Parse / Extract / 验证

### 执行
{操作内容}

### 结果
- **状态**: 成功 / 失败
- **备注**: {观察}
```
