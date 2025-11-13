# Auto Spider

简单高效的三阶段网页爬虫框架：下载（Action）→ 解析（Parse）→ 保存（Extract）

## 特性

- ✅ **三阶段分离**：下载、解析、保存独立运行，便于调试和迭代
- ✅ **自动化调度**：多进程下载、多线程解析，自动管理并发
- ✅ **数据追溯**：每个阶段保存完整数据链，便于查看和回溯
- ✅ **零依赖核心**：核心框架无第三方依赖，Spider 按需安装
- ✅ **简单直观**：装饰器定义步骤，Context 传递数据，一目了然

## 安装

```bash
# 安装核心框架
pip install -e .

# 可选：HTTP 爬虫支持
pip install requests

# 可选：浏览器自动化支持
pip install playwright
playwright install chromium
```

## 快速开始

### 1. 创建项目

```bash
# 生成项目模板
python -m auto_spider generate myplan

# 生成后的目录结构：
# plan_myplan.py         - 主程序文件
# steps_myplan/          - 步骤包
#   action.py            - Action 阶段（下载）
#   parse.py             - Parse 阶段（解析）
#   extract.py           - Extract 阶段（保存）
```

### 2. 编写三个阶段

**Action 阶段** - 下载页面：

```python
# steps_myplan/action.py
from auto_spider import action, Context

@action()
def fetch_page(context: Context):
    """下载页面内容"""
    url = context.task.get('url')
    response = context.spider.do_url(url)
    
    # 保存 HTML 内容
    context['content'] = response.text
    
    # 保存元数据
    context['result'] = {
        'url': url,
        'status': response.status_code,
        'length': len(response.text)
    }
    
    return response.text
```

**Parse 阶段** - 解析数据：

```python
# steps_myplan/parse.py
from auto_spider import parse, Context
from auto_spider.tools.xpath import xpath_extract

@parse()
def parse_data(context: Context):
    """解析页面数据"""
    # 读取 action 阶段的结果
    action_result = context.get('input', {})
    content = context.get('content', '')
    
    # 解析数据
    data = {
        'title': xpath_extract(content, '//h1/text()'),
        'links': xpath_extract(content, '//a/@href'),
        'source_url': action_result.get('url', '')
    }
    
    # 保存解析结果
    context['result'] = data
    return data
```

**Extract 阶段** - 保存数据：

```python
# steps_myplan/extract.py
from auto_spider import extract, Context

@extract()
def save_data(context: Context):
    """保存数据到数据库"""
    # 读取 parse 阶段的结果
    parse_result = context.get('input', {})
    
    # 保存到数据库
    # db = context.initial.get('db')
    # db.save(parse_result)
    
    print(f"Saved: {parse_result.get('title')}")
    return "saved"
```

### 3. 运行三个阶段

```bash
# 1. Action 阶段：下载页面
python plan_myplan.py

# 2. 修改 plan_myplan.py，注释掉 action，取消注释 parse
# 3. Parse 阶段：解析数据
python plan_myplan.py

# 4. 修改 plan_myplan.py，注释掉 parse，取消注释 extract
# 5. Extract 阶段：保存数据
python plan_myplan.py
```

## 数据流向

### Context Keys 规范

所有阶段共享统一的 Context 结构，但 key 的含义在不同阶段有所不同：

| Context Key | Action 阶段 | Parse 阶段 | Extract 阶段 |
|------------|-----------|----------|------------|
| `context.task` | 原始 Task | 原始 Task | 原始 Task |
| `context['input']` | 原始 Task | action 结果 | parse 结果 |
| `context['content']` | HTML 内容 | HTML 内容 | HTML 内容 |
| `context['result']` | action 结果 | parse 结果 | - |

**关键原则**：
- `context.task` 在所有阶段都是**原始 Task**，永不改变
- `context['input']` 是**当前阶段的输入**，每个阶段不同
- `context['content']` 是 **HTML 内容**，在所有阶段都存在

### 文件保存结构

每个阶段自动保存完整的数据链条：

```
output/
├── myplan_action_20241113_100000/
│   ├── task1_task.json      # 原始 Task
│   ├── task1_action.json    # action 结果
│   └── task1.html           # HTML 内容
│
├── myplan_parse_20241113_100100/
│   ├── task1_task.json      # 原始 Task（复制）
│   ├── task1_action.json    # action 结果（复制）
│   ├── task1_parse.json     # parse 结果
│   └── task1.html           # HTML 内容（复制）
│
└── myplan_extract_20241113_100200/
    # extract 阶段不保存文件，只读取数据用于副作用操作
```

**数据流转示意**：

```python
# Action 阶段：生成数据
context.task = Task(url='https://example.com')
context['input'] = Task(url='https://example.com')
context['content'] = '<html>...</html>'          # 用户设置
context['result'] = {'url': '...', 'status': 200} # 用户设置

# Parse 阶段：读取 action 结果
context.task = Task(url='https://example.com')    # 原始 Task
context['input'] = {'url': '...', 'status': 200}  # action 结果
context['content'] = '<html>...</html>'           # HTML 内容
context['result'] = {'title': '...', 'items': []} # 用户设置

# Extract 阶段：读取 parse 结果
context.task = Task(url='https://example.com')    # 原始 Task
context['input'] = {'title': '...', 'items': []}  # parse 结果
context['content'] = '<html>...</html>'           # HTML 内容
# 通常不设置 result，直接保存到数据库
```

## 重要特性

### 1. Spider 组件

框架提供两种 Spider 实现：

**RequestSpider** - 轻量级 HTTP 请求：
```python
from auto_spider.components import RequestSpider

def initial_spider():
    return RequestSpider()
```

**PlaywrightSpider** - 浏览器自动化：
```python
from auto_spider.components import PlaywrightSpider

def initial_spider():
    return PlaywrightSpider(headless=True)
```

### 2. 任务定义

使用 `Task` 定义爬取任务：

```python
from auto_spider import Task

def initial_task():
    return [
        Task(url='https://example.com/page1'),
        Task(url='https://example.com/page2'),
        Task(url='https://example.com/page3'),
    ]
```

### 3. 并发控制

```python
def initial_plan():
    return {
        'task_delay': 2,  # action 阶段任务间延迟（秒）
        'db': db,         # 自定义资源
    }
```

**并发说明**：
- **Action 阶段**：多进程 + Spider，支持 `task_delay` 延迟
- **Parse 阶段**：多线程，无延迟
- **Extract 阶段**：多线程，无延迟

### 4. CLI 命令

```bash
# 生成项目模板
python -m auto_spider generate myplan

# 直接运行指定阶段（无需修改文件）
python -m auto_spider run plan_myplan.py fetch_page -s action
python -m auto_spider run plan_myplan.py parse_data -s parse
python -m auto_spider run plan_myplan.py save_data -s extract

# 指定 worker 数量
python -m auto_spider run plan_myplan.py fetch_page -w 8
```

### 5. 工具函数

**XPath 提取**：
```python
from auto_spider.tools.xpath import xpath_extract

titles = xpath_extract(html, '//h1/text()')
links = xpath_extract(html, '//a/@href')
```

**去重检查**：
```python
from auto_spider.tools.dedup import create_duplicate_checker

checker = create_duplicate_checker()
if not checker(task):
    # 处理任务
    pass
```

## 最佳实践

### 1. 阶段独立性

每个阶段应该独立运行，不依赖其他阶段：

```python
# ✅ 好的做法：从 context 读取
action_result = context.get('input', {})

# ❌ 不好的做法：直接导入其他阶段函数
from steps_myplan.action import fetch_page
```

### 2. 数据完整性

每个阶段保存完整的数据链条，便于查看和回溯：

```bash
# 查看 action 阶段结果
cat output/myplan_action_*/task1_action.json

# 查看 parse 阶段结果（包含 action 数据）
cat output/myplan_parse_*/task1_parse.json
```

### 3. 简单直观

遵循 KISS 原则，保持代码简单：

```python
# ✅ 简单直接
@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    data = extract_data(content)
    context['result'] = data
    return data

# ❌ 过度设计
@parse()
def parse_data(context: Context):
    validator = DataValidator()
    processor = DataProcessor()
    # 过多的抽象和验证...
```

## License

MIT