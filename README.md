# auto_spider

基于动作管道和多进程的网页爬虫自动化框架。

## 快速开始

### 1. 简单Spider使用

```python
from auto_spider.components import RequestSpider

spider = RequestSpider()
spider.attach()

response = spider.do_url('https://example.com', retry=3)
html = response.text

spider.detach()
```

### 2. Plan + Actions（多进程）

```python
from auto_spider import Context, active
from auto_spider.core import Task, run_plan
from auto_spider.components import RequestSpider


def initial_spider():
    return RequestSpider()


def initial_task():
    return [
        Task(name='task1', url='https://example.com'),
        Task(name='task2', url='https://example.org'),
    ]


def initial_plan():
    # Return initial resources (optional)
    # Context will auto have: output_dir, save_result
    return {}


@active()
def fetch_page(context: Context):
    url = context.task['url']
    response = context.spider.do_url(url, retry=2)
    context['html'] = response.text
    # Save to context['result'], will be auto-saved
    context['result'] = {'url': url, 'html': response.text}
    return response.text


@active()
def extract_info(context: Context):
    html = context.get('html')
    # 解析逻辑
    return result


# 运行（默认4个进程）
actions = ['fetch_page', 'extract_info']
run_plan(initial_spider, initial_task, initial_plan, 
         actions=actions, plan_name='my_plan')
# 结果自动保存到: output/my_plan_20241111_143000/
```

## 核心概念

### Spider组件

- **RequestSpider**: 基于Session的HTTP请求
- **PlaywrightSpider**: 浏览器自动化

### Context

动作管道的数据载体：
- `context.spider` - Spider实例
- `context.task` - Task字典
- `context['key']` - 业务数据

### Task

轻量级任务定义字典：
```python
task = Task(name='fetch_page', url='https://example.com', retry=3)
url = task['url']
```

### Actions

使用`@action()`、`@parse()`、`@extract()`装饰的函数：
- 自动注册到全局注册表
- 按plan顺序执行
- 从context访问spider和task

### Plan模块

3个固定函数定义执行逻辑：
- `initial_spider()` - 创建spider
- `initial_task()` - 返回任务列表  
- `initial_plan()` - 返回初始资源对象

特性：
- 多进程执行：每个task在独立进程中运行（默认4个worker）
- 自动保存：task结果自动保存到 `output/<plan_name>_<timestamp>/`
- 资源注入：`context.initial` 自动包含 `output_dir` 和 `save_result`

## 命令行工具

### 生成plan模板

```bash
# 默认：生成plan文件和actions包（分离模式）
python -m auto_spider.cli generate my_plan

# 单文件模式：actions内联在plan文件中
python -m auto_spider.cli generate my_plan --single-file
```

**分离模式**（默认）生成：
- `plan_my_plan.py` - Plan文件
- `actions_my_plan/` - Actions包
  - `__init__.py` - 包初始化
  - `actions.py` - Action实现

**单文件模式**生成：
- `plan_my_plan.py` - Plan文件（包含inline actions）

参数：
- `name` - Plan名称（生成plan_{name}.py）
- `-d, --description` - Plan描述（可选）
- `--single-file` - 单文件模式，actions内联（可选）

### 运行plan文件

```bash
# CLI运行
python -m auto_spider.cli run plan_example.py fetch_page,parse_content -w 8

# 或直接运行plan文件
python plan_example.py
```

参数：
- `plan_file` - Plan文件路径
- `actions` - 逗号分隔的action名称
- `-w, --workers` - 进程数（默认4）

## 输出管理

### 自动保存结果

每个task的结果自动保存到带时间戳的目录：

```python
run_plan(initial_spider, initial_task, initial_plan,
         actions=['fetch_page'], plan_name='baidu')
# 保存位置: output/baidu_20241111_143000/task_0.json
```

### Context中的保存功能

```python
# 方式1: 设置context['result']，自动保存
context['result'] = {'url': url, 'html': html}

# 方式2: 手动调用save_result
context.save_result({'custom': 'data'})

# 访问output目录
output_dir = context.initial['output_dir']
print(f"Results in: {output_dir}")
```
