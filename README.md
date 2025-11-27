# Auto Spider

三阶段爬虫框架：Action（下载）→ Parse（解析）→ Extract（保存）

## 简介

Auto Spider 是一个简单高效的爬虫框架，将爬虫流程分为三个独立阶段，每个阶段可以独立运行和调试。使用装饰器注册步骤函数，框架自动处理并发、数据传递和存储。

核心特性：三阶段分离、自动并发调度、数据自动追溯、装饰器注册、零依赖核心

## 安装

```bash
pip install -e .                    # 核心框架
pip install requests                # HTTP爬虫（可选）
pip install playwright              # 浏览器自动化（可选）
playwright install chromium
```

## CLI 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `python -m auto_spider generate <plan>` | 生成项目模板 | `python -m auto_spider generate myplan` |
| `python -m auto_spider run <file> <step> -s <stage>` | 运行指定阶段 | `python -m auto_spider run plan_myplan.py fetch_page -s action` |
| `python -m auto_spider run <file> <step> -w <num>` | 指定worker数量 | `python -m auto_spider run plan_myplan.py fetch_page -w 8` |
| `python <plan_file>.py` | 直接运行计划文件 | `python plan_myplan.py` |

## 完整爬虫开发流程

### 一、生成项目模板

```bash
python -m auto_spider generate myplan
```

生成的目录结构：
```
plan_myplan.py          # 主程序文件
steps_myplan/           # 步骤包
  ├── __init__.py
  ├── action.py         # Action阶段（下载）
  ├── parse.py          # Parse阶段（解析）
  └── extract.py        # Extract阶段（保存）
```

### 二、配置 Spider 和 Task

编辑 `plan_myplan.py`，配置爬虫和任务：

```python
from auto_spider import Task, PlanConfig
from auto_spider.components import PlaywrightSpider

# 1. 配置参数
PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'
PLAN_CONFIG.OUTPUT_DIR = 'steps_myplan/output'
PLAN_CONFIG.MAX_WORKERS = 4
PLAN_CONFIG.RATE_LIMIT = 1.0  # 每个任务间隔1秒

# 2. 初始化 Spider
def initial_spider():
    return PlaywrightSpider(headless=True)

# 3. 定义任务列表
def initial_task():
    return [
        Task(url='https://example.com/page1', page_type='list'),
        Task(url='https://example.com/page2', retry=3),
        Task(url='https://example.com/page3', category='tech'),
    ]

# Task说明：
# Task本质是dict，可传入任意参数
# 在action阶段通过 context.task.get('key') 获取
# url是常用参数，其他参数根据需求自定义

# 4. 初始化资源（可选，如数据库连接）
def initial_plan():
    return {}
```

### 三、编写三个阶段的步骤函数

#### 1. Action 阶段 - 下载页面

编辑 `steps_myplan/action.py`：

```python
from auto_spider import action, Context, Task

@action()
def fetch_page(context: Context):
    """下载页面"""
    url = context.task.get('url')
    content = context.spider.do_url(url)
    
    context['content'] = content
    context['result'] = {'url': url}

# 增量爬取：动态添加新任务到队列
@action()
def fetch_list(context: Context):
    """列表页提取详情页链接"""
    url = context.task.get('url')
    content = context.spider.do_url(url)
    
    detail_urls = extract_links(content)
    
    # 添加新任务到队列
    for detail_url in detail_urls:
        context.tasks.append(Task(url=detail_url))
    
    context['content'] = content
```

> context['content'] 必须设置，用于传递HTML给后续阶段
>
> context['result'] 会自动保存为 task1_action.json
>
> 使用 context.tasks.append() 添加新任务，框架自动加入队列

#### 2. Parse 阶段 - 解析数据

编辑 `steps_myplan/parse.py`：

```python
from auto_spider import parse, Context
from auto_spider.tools.xpath import xpath_extract

@parse()
def parse_data(context: Context):
    """解析HTML"""
    content = context.get('content', '')
    action_result = context.get('input', {})
    
    data = {
        'title': xpath_extract(content, '//h1/text()'),
        'links': xpath_extract(content, '//a/@href'),
        'source_url': action_result.get('url')
    }
    
    context['result'] = data
```

> context['content'] 来自Action阶段的HTML
>
> context['input'] 来自Action阶段的result
>
> context['result'] 会传递给Extract阶段

#### 3. Extract 阶段 - 保存数据

编辑 `steps_myplan/extract.py`：

```python
from auto_spider import extract, Context

@extract()
def save_data(context: Context):
    """数据库入库操作"""
    parse_result = context.get('input', {})
    
    # 从initial_plan获取数据库连接
    # db = context.initial.get('db')
    # 
    # 执行数据库写入操作
    # db.insert('articles', {
    #     'title': parse_result.get('title'),
    #     'content': parse_result.get('content'),
    #     'links': parse_result.get('links')
    # })
    # 
    # 或执行其他副作用操作：发送通知、更新缓存等
```

> Extract阶段用于执行副作用操作（数据库写入、API调用等）
>
> 此阶段不保存文件，只读取Parse结果进行处理

### 四、运行三个阶段

#### 方式一：修改主文件运行

编辑 `plan_myplan.py` 底部：

```python
if __name__ == '__main__':
    from auto_spider import run_plan
    
    # 1. 运行 Action 阶段
    run_plan(initial_spider, initial_task, initial_plan,
             actions=['fetch_page'], config=PLAN_CONFIG)
    
    # 2. 运行 Parse 阶段
    # run_plan(None, initial_task, initial_plan,
    #          parses=['parse_data'], config=PLAN_CONFIG)
    
    # 3. 运行 Extract 阶段
    # run_plan(None, initial_task, initial_plan,
    #          extracts=['save_data'], config=PLAN_CONFIG)
```

运行：
```bash
# 注释掉parse和extract，运行action
python plan_myplan.py

# 注释掉action和extract，取消注释parse，运行parse  
python plan_myplan.py

# 注释掉action和parse，取消注释extract，运行extract
python plan_myplan.py
```

#### 方式二：使用CLI命令

```bash
# 运行 Action 阶段
python -m auto_spider run plan_myplan.py fetch_page -s action

# 运行 Parse 阶段
python -m auto_spider run plan_myplan.py parse_data -s parse

# 运行 Extract 阶段
python -m auto_spider run plan_myplan.py save_data -s extract
```

### 五、理解执行流程

#### 执行流程图

```
初始化阶段
├── 加载配置 (PLAN_CONFIG)
├── 调用 initial_spider() → 创建Spider实例
├── 调用 initial_task() → 生成任务列表
└── 调用 initial_plan() → 初始化资源

Action阶段 (多进程)
├── Scheduler: 分发任务到Queue
├── Worker-1..N: 从Queue获取任务
│   ├── 执行 @action() 装饰的函数
│   ├── Spider下载数据 → context['content']
│   └── 保存结果 → output/myplan_action_*/task1.html
└── 等待所有任务完成

Parse阶段 (多线程)
├── Stage: 自动加载Action阶段输出
├── Worker-1..N: 读取任务数据
│   ├── 执行 @parse() 装饰的函数
│   ├── 解析HTML → context['result']
│   └── 保存结果 → output/myplan_parse_*/task1_parse.json
└── 等待所有任务完成

Extract阶段 (多线程)
├── Stage: 自动加载Parse阶段输出
├── Worker-1..N: 读取任务数据
│   ├── 执行 @extract() 装饰的函数
│   └── 执行副作用（数据库写入等）
└── 等待所有任务完成
```

#### Context 数据传递

| Context Key | Action | Parse | Extract | 说明 |
|------------|--------|-------|---------|------|
| `context.task` | 原始Task | 原始Task | 原始Task | 永不改变 |
| `context['input']` | 原始Task | action的result | parse的result | 当前阶段输入 |
| `context['content']` | HTML | HTML | HTML | 在所有阶段存在 |
| `context['result']` | 设置 | 设置 | - | 当前阶段输出 |
| `context.spider` | Spider实例 | None | None | 仅Action阶段 |
| `context.initial` | 资源字典 | 资源字典 | 资源字典 | 共享资源 |

#### 文件保存结构

```
steps_myplan/
└── output/
    ├── action_20241118_100000/
    │   ├── task1_task.json      # 原始Task
    │   ├── task1_action.json    # action结果
    │   └── task1.html           # HTML内容
    │
    └── parse_20241118_100100/
        ├── task1_task.json      # 原始Task
        ├── task1_action.json    # action结果
        ├── task1_parse.json     # parse结果
        └── task1.html           # HTML内容
```

## 核心概念

### 装饰器系统

框架通过装饰器自动注册步骤函数：

```python
@action()   # 注册到Action阶段
@parse()    # 注册到Parse阶段  
@extract()  # 注册到Extract阶段
```

Registry会自动跟踪这些函数，Scheduler调用时从Registry获取。

### 并发模型

| 阶段 | 并发方式 | 原因 |
|------|---------|------|
| Action | 多进程 (Process) | Spider需要独立进程，避免资源冲突 |
| Parse | 多线程 (Thread) | 纯CPU计算，线程效率更高 |
| Extract | 多线程 (Thread) | IO密集型（数据库写入），线程即可 |

### 速率限制

通过 `RATE_LIMIT` 控制任务间延迟：

```python
PLAN_CONFIG.RATE_LIMIT = 1.0  # 每秒1个任务
PLAN_CONFIG.RATE_LIMIT = 0.5  # 每秒2个任务
PLAN_CONFIG.RATE_LIMIT = None # 无限制
```

### Spider 说明

两种Spider的`do_url()`都返回`str`（HTML内容）。详细API请参考`cc_reference.md`。

| Spider | 适用场景 | 特点 |
|--------|----------|------|
| PlaywrightSpider | JS渲染页面（默认） | 浏览器自动化，支持交互 |
| RequestSpider | 静态页面/API | 轻量快速 |

### 工具函数

#### XPath提取

```python
from auto_spider.tools.xpath import xpath_extract

titles = xpath_extract(html, '//h1/text()')
links = xpath_extract(html, '//a/@href')
```

#### 任务去重

去重机制：基于Task对象的hash值检查整个Task（所有字段）

```python
from auto_spider.tools.dedup import create_duplicate_checker, is_duplicate
from auto_spider import Task

# 创建去重器（内存模式）
checker = create_duplicate_checker()

# 或持久化到文件（跨进程共享）
checker = create_duplicate_checker('seen_tasks.json')

# 检查去重
task1 = Task(url='https://example.com/page1')
is_duplicate(checker, task1)  # False （第一次）
is_duplicate(checker, task1)  # True  （重复）

# 实际使用
for url in collected_urls:
    new_task = Task(url=url)
    if not is_duplicate(checker, new_task):
        context.tasks.append(new_task)
```

> 检查范围：Task的所有字段，不同字段组合会被视为不同Task

自定义去重逻辑：

```python
# 方法1：只根据url去重
# 保证Task只包含url字段
task = Task(url='https://example.com')  # 只设置url

# 方法2：自定义去重键
# 使用特殊字段作为去重标识
task = Task(dedup_key='page1', url='https://example.com', extra='data')
# 只有dedup_key不同才不重复

# 方法3：手动管理去重集合
seen_urls = set()
for url in collected_urls:
    if url not in seen_urls:
        seen_urls.add(url)
        context.tasks.append(Task(url=url))
```

## 最佳实践

### 阶段独立性

每个阶段通过Context读取数据：

```python
action_result = context.get('input', {})
```

### 保持简单

遵循KISS原则，用最简单的代码实现功能：

```python
@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    data = extract_data(content)
    context['result'] = data
```

### 数据追溯

每个阶段的输出目录包含完整数据链：

```bash
# 查看Action结果
cat output/myplan_action_*/task1_action.json

# 查看Parse结果（包含action数据）
cat output/myplan_parse_*/task1_parse.json
```

## 架构说明

框架核心模块：

- registry.py - 装饰器注册中心，管理所有步骤函数
- scheduler.py - 任务调度器，分发任务到Worker
- worker.py - 工作单元，执行具体步骤函数
- stage.py - 阶段管理，处理数据加载和保存
- Context - 数据传递载体，在阶段间传递数据

执行流程：装饰器注册 → Scheduler分发 → Worker执行 → Stage保存

## 配置说明

### PlanConfig 配置项

```python
PLAN_CONFIG = PlanConfig()

# 计划名称（用于输出目录命名）
PLAN_CONFIG.PLAN_NAME = 'myplan'

# Worker数量（并发执行任务的进程/线程数）
PLAN_CONFIG.MAX_WORKERS = 4  # 默认4

# 速率限制（任务间延迟秒数）
PLAN_CONFIG.RATE_LIMIT = 1.0  # 1.0 = 每秒1个任务
PLAN_CONFIG.RATE_LIMIT = 0.5  # 0.5 = 每秒2个任务
PLAN_CONFIG.RATE_LIMIT = None  # None = 无限制

# 自定义输出目录
PLAN_CONFIG.OUTPUT_DIR = 'steps_myplan/output'  # 推荐放在steps包下
```

---

## TODO

### 框架优化

- [ ] 任务去重机制：避免重复执行已完成任务
- [ ] 进度恢复机制：从检查点恢复执行
- [ ] 更好的进度反馈和错误提示

### 数据提取

- [ ] 多模式XPath提取：fallback机制提高成功率
- [ ] 数据质量评估：自动评估提取结果完整性

### 错误处理

- [ ] 详细错误日志
- [ ] 更好的异常提示信息

---

## License

MIT