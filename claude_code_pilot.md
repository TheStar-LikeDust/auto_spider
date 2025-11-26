# Auto Spider 爬虫指南

## 爬取网站的步骤

### Step 1: 创建项目
```bash
# 在项目根目录创建
mkdir steps_项目名
touch plan_项目名.py steps_项目名/action.py steps_项目名/parse.py
```

### Step 2: 写 plan 入口文件
```python
# plan_项目名.py
from auto_spider.core import Task, run_plan, PlanConfig
from auto_spider.components import RequestSpider  # 静态页面用这个
# from auto_spider.components import PlaywrightSpider  # JS渲染页面用这个

import steps_项目名.action
import steps_项目名.parse

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = '项目名'

def initial_spider():
    return RequestSpider()

def initial_task():
    return [Task(name='task1', url='https://目标网址')]

def initial_plan():
    return {}

if __name__ == '__main__':
    run_plan(initial_spider, initial_task, initial_plan,
             actions=['fetch_page'], config=PLAN_CONFIG)
```

### Step 3: 写 action（下载页面）
```python
# steps_项目名/action.py
from auto_spider import Context, action

@action()
def fetch_page(context: Context):
    url = context.task['url']
    response = context.spider.do_url(url, retry=2)
    context['content'] = response.text
    context['result'] = {'url': url}
```

### Step 4: 写 parse（解析数据）
```python
# steps_项目名/parse.py
from auto_spider import Context, parse

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    # 解析逻辑...
    context['result'] = {'data': parsed_data}
```

### Step 5: 运行
```bash
python plan_项目名.py
```

## 核心API速查

### Context 对象
```python
context.spider          # Spider实例
context.task            # 当前任务 {'url': '...', 'name': '...'}
context.tasks           # 增量任务列表，append新Task实现增量爬取
context['content']      # HTML内容
context['result']       # 设置当前阶段输出
context.get('input')    # 获取上一阶段输出
```

### Spider
```python
# RequestSpider - 静态页面
response = context.spider.do_url(url, retry=2)
html = response.text

# PlaywrightSpider - JS渲染
html = context.spider.do_url(url)
page = context.spider.get_driver()  # 获取playwright page对象
```

### 增量爬取
```python
@action()
def fetch(context: Context):
    # 发现新链接时添加任务
    context.tasks.append(Task(name='new', url='新链接'))
```

## 输出目录

默认自动创建在 `steps_{PLAN_NAME}/output/` 下：
```
steps_项目名/
└── output/
    ├── action_时间戳/
    │   ├── task1.html      # HTML
    │   └── task1_*.json    # 元数据
    └── parse_时间戳/
        └── task1_parse.json
```

## 配置
```python
PLAN_CONFIG.PLAN_NAME = '项目名'      # 必填
PLAN_CONFIG.MAX_WORKERS = 4           # 并发数
PLAN_CONFIG.RATE_LIMIT = 1.0          # 请求间隔(秒)
```
