# Auto Spider

基于统一Step概念的网页爬虫自动化框架。

**核心特性**：
- 🎯 统一的Step抽象（action/parse/extract三阶段）
- 🚀 多进程/线程自动调度
- 💾 自动结果保存和加载
- 🔌 第三方库按需导入，核心框架零依赖
- 📦 模块化设计，易于扩展

## 安装

```bash
# 核心框架（无额外依赖）
pip install -e .

# 可选：RequestSpider支持
pip install requests

# 可选：PlaywrightSpider支持
pip install playwright
playwright install chromium
```

## 快速开始

### 1. 生成项目模板

```bash
# 生成plan和actions包
python -m auto_spider.cli generate myplan

# 或使用单文件模式
python -m auto_spider.cli generate myplan --single-file
```

### 2. 三阶段执行示例

```python
from auto_spider import Context, Task, action, parse, extract
from auto_spider.core import run_plan
from auto_spider.components import RequestSpider

# Action阶段：下载HTML
@action()
def fetch_page(context: Context):
    url = context.task['url']
    response = context.spider.do_url(url, retry=2)
    context['result'] = response.text  # 自动保存为.html
    return response.text

# Parse阶段：解析数据
@parse()
def parse_html(context: Context):
    html = context['result']  # 自动加载action结果
    # 解析逻辑...
    title = extract_title(html)
    context['result'] = f"Title: {title}"  # 自动保存
    return title

# Extract阶段：保存数据
@extract()
def save_to_db(context: Context):
    data = context['result']  # 自动加载parse结果
    # 保存到数据库...
    context['result'] = "saved"
    return "saved"

# 定义tasks和资源
def initial_spider():
    return RequestSpider()

def initial_task():
    return [
        Task(url='https://example.com/page1'),
        Task(url='https://example.com/page2'),
    ]

def initial_plan():
    return {}  # 可以返回db等资源

# 执行三个阶段
if __name__ == '__main__':
    # Action阶段
    run_plan(initial_spider, initial_task, initial_plan,
             actions=['fetch_page'], plan_name='demo')
    
    # Parse阶段（自动加载action结果）
    run_plan(initial_task=initial_task, initial_plan=initial_plan,
             parses=['parse_html'], plan_name='demo')
    
    # Extract阶段（自动加载parse结果）
    run_plan(initial_task=initial_task, initial_plan=initial_plan,
             extracts=['save_to_db'], plan_name='demo')
```

## 核心概念

### Step（统一抽象）

所有执行单元都是Step，有三种类型：

| Step类型 | 装饰器 | 输入 | 输出 | 执行方式 |
|---------|--------|------|------|----------|
| **Action** | `@action()` | Task | 原始数据 | 多进程+Spider |
| **Parse** | `@parse()` | TaskResult | 解析数据 | 多线程+文件 |
| **Extract** | `@extract()` | TaskData | 持久化确认 | 多线程+数据库 |

### Context（数据容器）

所有Step共用的上下文：
```python
context.spider    # Spider实例（action专用）
context.task      # Task字典
context.initial   # 初始资源（db, cache等）
context['result'] # 当前阶段结果
context['key']    # 自定义数据
```

### Task（任务定义）

```python
Task(url='https://example.com', retry=3)
# name字段可选，自动从URL生成
```

### Spider（爬虫组件）

```python
# RequestSpider - 简单HTTP请求
from auto_spider.components import RequestSpider
spider = RequestSpider()
spider.attach()
response = spider.do_url('https://example.com')

# PlaywrightSpider - 浏览器自动化
from auto_spider.components import PlaywrightSpider
spider = PlaywrightSpider(headless=True)
spider.attach()
content = spider.do_url('https://example.com')
```

## CLI命令

### 生成模板

```bash
# 生成plan和actions包（推荐）
python -m auto_spider.cli generate myplan
# 或简写
python -m auto_spider.cli gen myplan
python -m auto_spider.cli g myplan

# 单文件模式
python -m auto_spider.cli generate myplan --single-file
```

### 运行Plan

```bash
# 运行action阶段
python -m auto_spider.cli run plan_myplan.py fetch_page --stage action

# 运行parse阶段
python -m auto_spider.cli run plan_myplan.py parse_html --stage parse

# 运行extract阶段
python -m auto_spider.cli run plan_myplan.py save_to_db --stage extract

# 指定worker数量
python -m auto_spider.cli run plan_myplan.py fetch_page -w 8

# 或直接运行plan文件
python plan_myplan.py
```

### CLI参数

**generate命令**:
- `name` - Plan名称
- `-d, --description` - Plan描述
- `--single-file` - 单文件模式

**run命令**:
- `plan_file` - Plan文件路径
- `steps` - 逗号分隔的step名称
- `-s, --stage` - 执行阶段（action/parse/extract）
- `-w, --workers` - Worker数量（默认4）

## 输出管理

### 自动保存

每个阶段的结果自动保存：

```
output/
├── demo_action_20241112_100000/
│   ├── example_com.html  # context['result']内容
│   └── example_com.json  # context其他数据（调试用）
├── demo_parse_20241112_100100/
│   ├── example_com.html  # 解析结果
│   └── example_com.json  # 元数据
└── demo_extract_20241112_100200/
    ├── example_com.html  # 持久化确认
    └── example_com.json  # 元数据
```

### 自动加载

- Parse阶段自动加载最新action输出
- Extract阶段自动加载最新parse输出
- 无需手动指定文件路径

## 项目结构

详见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 文档

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 完整项目结构说明
- [SPIDER_REFACTOR.md](SPIDER_REFACTOR.md) - Spider包重构说明

## License

MIT
