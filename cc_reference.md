# Auto Spider 参考手册

---

## 1. CLI 命令

### generate - 生成项目模板

```bash
python -m auto_spider generate <name> [--single-file] [-d <description>]
```

| 参数 | 说明 |
|------|------|
| `<name>` | 计划名称，生成 `plan_{name}.py` 和 `steps_{name}/` |
| `--single-file` | 生成单文件模板（内联steps） |
| `-d, --description` | 计划描述 |

### run - 运行指定阶段

```bash
python -m auto_spider run <plan_file> <steps> [-s <stage>] [-w <workers>] [--retry-failed]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<plan_file>` | plan文件路径 | 必填 |
| `<steps>` | 步骤名（逗号分隔） | 必填 |
| `-s, --stage` | 阶段：action/parse/extract | 自动检测 |
| `-w, --workers` | 并发数 | `4` |
| `--retry-failed` | 重试失败任务 | `False` |

**stage自动检测规则**：
- 步骤名包含 `parse` → parse阶段
- 步骤名包含 `extract` 或 `save` → extract阶段
- 其他 → action阶段

### 直接运行

```bash
python plan_mysite.py
```

---

## 2. 项目结构

执行 `python -m auto_spider generate mysite` 后生成：

| 文件/目录 | 说明 |
|-----------|------|
| `plan_mysite.py` | 主入口文件，配置Spider、Task、运行参数 |
| `steps_mysite/` | 步骤包目录 |
| `steps_mysite/__init__.py` | 包初始化，自动导入action/parse/extract |
| `steps_mysite/action.py` | Action阶段步骤函数 |
| `steps_mysite/parse.py` | Parse阶段步骤函数 |
| `steps_mysite/extract.py` | Extract阶段步骤函数 |

---

## 3. 三阶段说明

### Action 阶段

**职责**：网络请求，获取原始数据

| 项目 | 说明 |
|------|------|
| **执行方式** | 多进程 |
| **输入** | `context.task` - 任务字典（包含url等） |
| **操作** | 使用Spider发起HTTP请求或浏览器访问 |
| **输出** | `context['content']` - HTML内容（必须设置） |
| **保存** | `context['result']` - 保存为 `task_action.json` |
| **增量** | `context.tasks.append(Task(...))` - 添加新任务 |

### Parse 阶段

**职责**：解析HTML，提取结构化数据

| 项目 | 说明 |
|------|------|
| **执行方式** | 多线程 |
| **输入** | `context['content']` - HTML内容 |
| **输入** | `context.get('input')` - Action阶段的result |
| **操作** | 使用XPath/CSS选择器解析HTML |
| **输出** | `context['result']` - 保存为 `task_parse.json` |

### Extract 阶段

**职责**：数据持久化，执行副作用操作

| 项目 | 说明 |
|------|------|
| **执行方式** | 多线程 |
| **输入** | `context.get('input')` - Parse阶段的result |
| **操作** | 数据库写入、API调用、文件保存等 |
| **输出** | 无文件输出 |

---

## 4. 配置项（PlanConfig）

在 `plan_mysite.py` 中设置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PLAN_NAME` | 计划名称，用于输出目录命名 | 必填 |
| `OUTPUT_DIR` | 输出目录路径 | `None`（自动为`output`） |
| `MAX_WORKERS` | 并发Worker数量 | `4` |
| `RATE_LIMIT` | 任务间隔（秒） | `None`（无限制） |
| `STORAGE_TIMESTAMP` | 目录名是否带时间戳 | `True` |

---

## 5. run_plan 参数

```python
run_plan(initial_spider, initial_task, initial_plan,
         actions=[], parses=[], extracts=[],
         config=PLAN_CONFIG)
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `initial_spider` | Spider工厂函数 | Action阶段必填 |
| `initial_task` | Task列表工厂函数 | 是（除非retry_failed） |
| `initial_plan` | 资源工厂函数 | 否 |
| `actions` | Action阶段函数名列表 | 三选一 |
| `parses` | Parse阶段函数名列表 | 三选一 |
| `extracts` | Extract阶段函数名列表 | 三选一 |
| `config` | PlanConfig实例 | 否 |
| `retry_failed` | 重试失败任务 | 否 |

---

## 6. Context API

### 属性

| 属性 | 阶段 | 说明 |
|------|------|------|
| `context.task` | 全部 | 原始Task字典，永不改变 |
| `context.spider` | Action | Spider实例 |
| `context.tasks` | Action | 增量任务列表 |
| `context.initial` | 全部 | `initial_plan()` 返回的资源字典 |

### 键值

| 键 | 读/写 | 说明 |
|----|-------|------|
| `context['content']` | 读写 | HTML内容 |
| `context['result']` | 写 | 当前阶段输出，自动保存 |
| `context.get('input')` | 读 | 上一阶段的result |

---

## 7. Spider

两种Spider的 `do_url()` 都返回 `str`（HTML内容）。

### PlaywrightSpider（默认）

浏览器自动化，支持JS渲染。

| 方法 | 说明 |
|------|------|
| `do_url(url)` | 访问URL，返回HTML字符串 |
| `get_driver()` | 获取 `playwright.Page` 对象 |

**Page常用操作**：

| 操作 | 说明 |
|------|------|
| `page.click(selector)` | 点击元素 |
| `page.fill(selector, text)` | 填写输入框 |
| `page.wait_for_selector(selector)` | 等待元素出现 |
| `page.screenshot(path='x.png')` | 截图 |

### RequestSpider

HTTP请求，适合静态页面，更轻量。

| 方法 | 说明 |
|------|------|
| `do_url(url, retry=1)` | 发起HTTP请求，返回HTML字符串 |
| `get_driver()` | 获取 `requests.Session` 对象 |

---

## 8. 工具函数

### XPath提取

| 函数 | 说明 |
|------|------|
| `xpath_extract(html, xpath)` | 提取匹配XPath的内容列表 |

导入：`from auto_spider.tools.xpath import xpath_extract`

---

## 9. 输出文件

### 目录结构

**STORAGE_TIMESTAMP=True**（默认，带时间戳）：
```
steps_mysite/output/
├── action_20241127_140000/
└── parse_20241127_140100/
```

**STORAGE_TIMESTAMP=False**（无时间戳，覆盖模式）：
```
steps_mysite/output/
├── action/
└── parse/
```

### 文件说明

| 文件 | 说明 |
|------|------|
| `task1.html` | HTML内容 |
| `task1_task.json` | 原始Task |
| `task1_action.json` | Action阶段result |
| `task1_parse.json` | Parse阶段result |
| `task1_failed.json` | 失败任务信息（如果有） |

---

## 10. 代码规范

### import语句

**必须放在文件顶部**，不要放在函数或条件块内。

```python
# 正确
import re
import json
from auto_spider import action, Context

@action()
def fetch_page(context: Context):
    text = re.sub(r'\s+', ' ', content)  # re可用
```

```python
# 错误 - 会导致 "cannot access local variable 're'"
@action()
def fetch_page(context: Context):
    if need_clean:
        import re  # 不要在条件块内import
        text = re.sub(r'\s+', ' ', content)
```

### URL处理

注意区分相对路径和完整URL：

```python
def normalize_url(uri: str, base_url: str) -> str:
    if uri.startswith('/'):
        return base_url + uri
    elif uri.startswith('http'):
        return uri
    else:
        return f"{base_url}/{uri}"
```

### 数据清洗

提取后清洗空白字符：

```python
def clean_text(text: str) -> str:
    if text:
        return ' '.join(text.split())
    return ''
```

---

## 11. 代码示例

### plan_mysite.py

```python
from auto_spider import Task, PlanConfig, run_plan
from auto_spider.components import PlaywrightSpider

import steps_mysite.action
import steps_mysite.parse

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'mysite'
PLAN_CONFIG.OUTPUT_DIR = 'steps_mysite/output'

def initial_spider():
    return PlaywrightSpider(headless=True)

def initial_task():
    return [Task(url='https://example.com')]

def initial_plan():
    return {}

if __name__ == '__main__':
    run_plan(initial_spider, initial_task, initial_plan,
             actions=['fetch_page'], config=PLAN_CONFIG)
```

### action.py

```python
from auto_spider import action, Context, Task

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    context['content'] = content
    context['result'] = {'url': url}

# 增量爬取示例
@action()
def fetch_list(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    
    # 添加新任务
    for link in extract_links(content):
        context.tasks.append(Task(url=link))
    
    context['content'] = content
```

### parse.py

```python
from auto_spider import parse, Context
from auto_spider.tools.xpath import xpath_extract

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    data = {
        'title': xpath_extract(content, '//h1/text()'),
        'links': xpath_extract(content, '//a/@href'),
    }
    context['result'] = data
```

### extract.py

```python
from auto_spider import extract, Context

@extract()
def save_data(context: Context):
    parse_result = context.get('input', {})
    # 执行数据库写入等操作
```

### Spider初始化示例

```python
# PlaywrightSpider（默认，支持JS）
def initial_spider():
    return PlaywrightSpider(headless=True, enable_cdp=True)

# RequestSpider（轻量，静态页面）
def initial_spider():
    return RequestSpider(timeout=10)
```
