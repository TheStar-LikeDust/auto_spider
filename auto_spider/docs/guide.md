# 使用指南

本文档从简单到复杂介绍如何使用 Auto Spider。

## 快速开始

```bash
# 1. 生成项目模板
python -m auto_spider generate myplan

# 2. 配置 plan_myplan.py

# 3. 运行
python plan_myplan.py
```

## 核心概念

### 三阶段架构

```
Task → action step → 原始数据(.html)
                         ↓
                    TaskResult → parse step → 解析数据(.json)
                                                  ↓
                                             TaskData → extract step → 持久化
```

### 装饰器注册

```python
@action()   # Action阶段：下载页面
@parse()    # Parse阶段：解析HTML
@extract()  # Extract阶段：保存数据
```

### Context 数据传递

| Key | 说明 |
|-----|------|
| `context.task` | 原始Task，永不改变 |
| `context['content']` | HTML内容，Action阶段必须设置 |
| `context['result']` | 当前阶段输出，自动保存为json |
| `context.get('input')` | 上一阶段的result |
| `context.spider` | Spider实例（仅Action阶段） |

## 完整流程

### 1. 配置 Spider 和 Task

```python
from auto_spider import Task, PlanConfig
from auto_spider.components import PlaywrightSpider

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'
PLAN_CONFIG.MAX_WORKERS = 4
PLAN_CONFIG.RATE_LIMIT = 1.0

def initial_spider():
    return PlaywrightSpider(headless=True)

def initial_task():
    return [
        Task(url='https://example.com/page1'),
        Task(url='https://example.com/page2'),
    ]

def initial_plan():
    return {}
```

### 2. 编写步骤函数

**Action（下载）**：
```python
@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    context['content'] = content
    context['result'] = {'url': url}
```

**Parse（解析）**：
```python
@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    data = extract_data(content)
    context['result'] = data
```

**Extract（保存）**：
```python
@extract()
def save_data(context: Context):
    parse_result = context.get('input', {})
    # 数据库写入或其他副作用操作
```

### 3. 运行

```bash
# 推荐：使用 CLI 命令
auto-spider run plan_myplan.py fetch_page --stage action
auto-spider run plan_myplan.py parse_data --stage parse
auto-spider run plan_myplan.py save_data --stage extract

# 重试失败任务
auto-spider run plan_myplan.py fetch_page --stage action --retry-failed
```

## 执行逻辑

### 数据流向

```
initial_task() 获取任务
    ↓
Action阶段（多进程）
  → context['content'] = HTML
  → 保存到 output/action_*/
    ↓ 自动加载
Parse阶段（多线程）
  → context['content'] = HTML（自动加载）
  → context['input'] = action结果（自动加载）
  → 保存到 output/parse_*/
    ↓ 自动加载
Extract阶段（多线程）
  → context['input'] = parse结果（自动加载）
  → 执行副作用操作
```

### 并发模型

| 阶段 | 并发方式 | 原因 |
|------|---------|------|
| Action | 多进程 | Spider需要独立进程 |
| Parse | 多线程 | 纯CPU计算 |
| Extract | 多线程 | IO密集型 |

### 文件结构

```
output/
├── action_20241118_100000/
│   ├── task1.html
│   ├── task1_task.json
│   └── task1_action.json
└── parse_20241118_100100/
    ├── task1.html
    ├── task1_task.json
    ├── task1_action.json
    └── task1_parse.json
```

## 常见场景

### 增量爬取

动态添加新任务：
```python
@action()
def fetch_list(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    detail_urls = extract_links(content)
    for detail_url in detail_urls:
        context.tasks.append(Task(url=detail_url))

    context['content'] = content
```

### 分页

```python
@action()
def fetch_list(context: Context):
    url = context.task.get('url')
    page = context.task.get('page', 1)

    content = context.spider.do_url(f"{url}?page={page}")
    context['content'] = content

    if has_next_page(content) and page < 10:
        context.tasks.append(Task(url=url, page=page + 1))
```

### 登录

```python
@action()
def login_and_fetch(context: Context):
    page = context.spider.get_driver()

    page.goto('https://example.com/login')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')
    page.wait_for_url('**/dashboard')

    url = context.task.get('url')
    content = context.spider.do_url(url)
    context['content'] = content
```

### 懒加载

```python
@action()
def fetch_lazy(context: Context):
    url = context.task.get('url')
    page = context.spider.get_driver()
    page.goto(url)

    for _ in range(5):
        page.evaluate('window.scrollBy(0, 1000)')
        page.wait_for_timeout(500)

    content = page.content()
    context['content'] = content
```

## 调试技巧

### Action 阶段

1. 查看 `.html` 文件确认内容
2. 搜索关键词验证数据存在
3. 检查 `_failed.json` 查看失败原因

### Parse 阶段

1. 查看 `_parse.json` 确认提取结果
2. 在浏览器开发者工具Console测试XPath：`$x('//h1/text()')`
3. 对比文件数和任务数

### 常见问题

**页面内容为空**：添加等待 `page.wait_for_selector('.content')`

**元素找不到**：检查选择器、iframe、可见区域

**被反爬拦截**：降低并发、增加延迟、使用 headless=False 观察

## 最佳实践

- 阶段独立：通过 `context.get('input')` 读取上一阶段数据
- 保持简单：KISS原则，用最少代码实现
- 数据追溯：查看输出目录中的json文件调试
- 单页验证：先测试1个URL，确认逻辑正确后再扩展
