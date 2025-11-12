# Auto Spider 项目结构

## 整体架构

```
auto_spider/
├── step/                    # Step数据结构 - 统一的执行单元定义
│   ├── __init__.py         # 导出所有step相关类型
│   ├── context.py          # Context - 所有step共用的上下文对象
│   ├── task.py             # Task - action step的输入数据结构
│   ├── task_result.py      # TaskResult - parse step的输入数据结构
│   └── task_data.py        # TaskData - extract step的输入数据结构
│
├── core/                    # 核心逻辑 - Step的注册、执行、调度
│   ├── __init__.py         # 导出核心API
│   ├── registry.py         # Step注册器 - 装饰器和注册管理
│   ├── executor.py         # Step执行器 - 统一的执行逻辑
│   ├── scheduler.py        # Step调度器 - 多进程/线程调度
│   ├── loader.py           # Step加载器 - 动态加载step函数
│   └── storage.py          # 存储管理 - 输出目录和文件管理
│
├── components/              # 组件库 - 可复用的功能组件
│   ├── __init__.py         # 延迟导入入口，避免依赖错误
│   └── spider/             # Spider子包 - 爬虫组件
│       ├── __init__.py         # Spider包入口，延迟导入
│       ├── base_spider.py      # BaseSpider - Spider基类
│       ├── request_spider.py   # RequestSpider - 基于requests的HTTP爬虫
│       └── playwright_spider.py # PlaywrightSpider - 基于Playwright的浏览器爬虫
│
├── tools/                   # 工具集 - 辅助开发工具
│   ├── __init__.py         # 导出工具函数
│   └── templates.py        # 代码模板生成器
│
├── __init__.py             # 包入口 - 导出公共API
├── cli.py                  # CLI命令行工具（统一入口）
├── logger.py               # 日志系统
└── settings.py             # 全局配置
```

---

## 模块详细说明

### 1. step/ - Step数据结构

统一的执行单元数据结构定义，所有阶段共享相同的概念模型。

#### `context.py` - Context上下文
- **作用**: 所有step函数共用的数据容器
- **特点**: 
  - 继承自dict，支持字典操作
  - 提供spider、task、db等系统资源的属性访问
  - 业务数据通过dict接口存取
- **使用场景**: 在action/parse/extract函数中传递数据

#### `task.py` - Task任务
- **作用**: action step的输入数据结构
- **字段**: url、retry等任务配置
- **特点**: 
  - name字段可选，自动从URL生成
  - 支持任意自定义字段
- **函数**: `generate_task_name()` - 自动生成任务名

#### `task_result.py` - TaskResult结果
- **作用**: parse step的输入数据结构
- **字段**: task_name、content、source_dir等
- **特点**: 
  - 由scheduler自动从action输出加载
  - 包含原始内容和元数据
- **使用场景**: parse阶段自动接收

#### `task_data.py` - TaskData数据
- **作用**: extract step的输入数据结构
- **字段**: task_name、parsed_data、source_dir等
- **特点**: 
  - 由scheduler自动从parse输出加载
  - 包含结构化数据和元数据
- **使用场景**: extract阶段自动接收

---

### 2. core/ - 核心逻辑

Step的生命周期管理，从注册到执行的完整流程。

#### `registry.py` - Step注册器
- **作用**: 管理step函数的注册和获取
- **功能**:
  - 装饰器: `@action()`, `@parse()`, `@extract()`, `@active()`
  - 注册函数: `register_action()`, `register_parse()`, `register_extract()`
  - 获取函数: `get_action()`, `get_parse()`, `get_extract()`
  - 清理函数: `clear_actions()`, `clear_parses()`, `clear_extracts()`
  - 执行接口: `execute_plan()`, `execute_parse()`, `execute_extract()`
- **全局注册表**: `_ACTION_REGISTRY`, `_PARSE_REGISTRY`, `_EXTRACT_REGISTRY`

#### `executor.py` - Step执行器
- **作用**: 统一的step函数执行逻辑
- **功能**:
  - `execute_functions()` - 顺序执行多个函数
  - `execute_plan()` - 通用的执行计划接口
- **特点**: 
  - 自动创建和管理Context
  - 记录执行结果到context['results']
  - 详细的日志输出

#### `scheduler.py` - Step调度器
- **作用**: 多进程/线程任务调度
- **功能**:
  - `run_plan()` - 主调度函数，支持三种阶段
  - `_worker_process_tasks()` - action阶段多进程worker
  - `_worker_thread_parse()` - parse阶段线程worker
  - `_worker_thread_extract()` - extract阶段线程worker
- **特点**:
  - action阶段: 多进程 + Spider池化
  - parse阶段: 多线程 + 自动加载action输出
  - extract阶段: 多线程 + 自动加载parse输出
  - 自动结果保存和日志记录

#### `loader.py` - Step加载器
- **作用**: 动态加载Python文件中的step函数
- **功能**:
  - `load_actions_from_file()` - 加载单个文件
  - `load_actions_from_directory()` - 扫描目录加载
- **特点**: 
  - 自动导入并执行装饰器注册
  - 支持递归扫描
  - 跳过非Python文件

#### `storage.py` - 存储管理
- **作用**: 管理输出目录和文件的读写
- **功能**:
  - `create_output_dir()` - 创建带时间戳的输出目录
  - `save_task_result()` - 保存任务结果（html/json）
  - `find_latest_output_dir()` - 查找最新输出目录
  - `load_task_result()` - 加载任务结果
- **目录格式**: `output/{plan}_{stage}_{timestamp}/`
- **文件格式**: 
  - 主文件: `{task_name}.html` - context['result']内容
  - 调试文件: `{task_name}.json` - context其他数据

---

### 3. components/ - 组件库

可复用的功能组件，主要是各类Spider实现。

#### `__init__.py` - 组件入口
- **作用**: 导出spider组件
- **特点**:
  - 正常导入内部spider类
  - 第三方库（requests, playwright）在spider方法内导入
  - 导入不报错，使用时才检查依赖
- **别名**: `Spider` = `BaseSpider`

#### `spider/` - Spider子包

##### `base_spider.py` - Spider基类
- **作用**: 定义Spider的标准接口
- **生命周期**: attach() → use → detach()
- **接口**:
  - `attach()` - 创建连接
  - `detach()` - 关闭连接
  - `do_url()` - 访问URL
  - `get_driver()` - 获取底层驱动
- **特点**: 抽象基类，无外部依赖

##### `request_spider.py` - RequestSpider
- **作用**: 基于requests库的HTTP爬虫
- **依赖**: `requests>=2.31.0` (可选)
- **功能**:
  - 自动重试机制
  - Session会话管理
  - 自定义headers
  - 支持GET/POST/PUT/DELETE等方法
- **第三方库导入**: `from requests import Session` 在 `_do_attach()` 方法内
- **适用场景**: 静态页面、API请求

##### `playwright_spider.py` - PlaywrightSpider
- **作用**: 基于Playwright的浏览器爬虫
- **依赖**: `playwright>=1.40.0` (可选)
- **功能**:
  - 无头/有头浏览器
  - JavaScript渲染
  - 页面截图和PDF
  - 支持Chromium/Firefox/WebKit
- **第三方库导入**: `from playwright.sync_api import sync_playwright` 在 `_do_attach()` 方法内
- **适用场景**: 动态网页、需要JS执行的页面

---

### 4. tools/ - 工具集

辅助开发的工具函数。

#### `templates.py` - 代码模板生成器
- **作用**: 生成标准化的代码模板
- **模板类型**:
  - `ACTION_MODULE_TEMPLATE` - actions.py模板
  - `PLAN_TEMPLATE` - plan文件模板
  - `PLAN_SINGLE_FILE_TEMPLATE` - 单文件plan模板
- **函数**:
  - `generate_plan()` - 生成plan文件
  - `generate_actions()` - 生成actions包

---

### 5. 顶层模块

#### `cli.py` - CLI命令行工具
- **作用**: 统一的命令行接口
- **命令**:
  - `generate` (别名: gen, g) - 生成plan和actions模板
  - `run` (别名: r) - 运行plan文件
- **功能**:
  - 自动stage检测（从step名称推断action/parse/extract）
  - 友好的命令别名支持
  - 详细的帮助信息和示例
- **使用**: 
  ```bash
  python -m auto_spider.cli generate myplan
  python -m auto_spider.cli run plan_myplan.py fetch_page -s action -w 8
  ```

#### `__init__.py` - 包入口
- **作用**: 导出公共API，提供统一的import接口
- **导出内容**:
  - Step数据结构: Context, Task, TaskResult, TaskData
  - 装饰器: action, parse, extract, active
  - 子模块: core, tools, components, step

#### `logger.py` - 日志系统
- **作用**: 统一的日志管理
- **功能**:
  - `build_logger()` - 创建模块日志器
  - 文件和控制台双输出
  - 彩色日志支持
- **日志级别**: DEBUG, INFO, WARNING, ERROR

#### `settings.py` - 全局配置
- **作用**: 存储全局配置参数
- **配置项**: 
  - 输出目录路径
  - 默认worker数量
  - 日志级别等

---

## 数据流向

```
Task → action step → 原始数据(.html) 
                         ↓
                    TaskResult → parse step → 解析数据(.html)
                                                  ↓
                                             TaskData → extract step → 持久化确认(.html)
```

## 执行流程

```
1. 用户定义step函数
   @action() def fetch() ...
   @parse() def parse() ...

2. 装饰器自动注册
   registry.py 注册到全局表

3. 调用run_plan()
   scheduler.py 创建输出目录

4. 分配任务到worker
   多进程(action) / 多线程(parse/extract)

5. 执行step函数
   executor.py 顺序执行

6. 自动保存结果
   storage.py 保存到输出目录

7. 下一阶段自动加载
   scheduler.py 加载上一阶段输出
```

---

## 设计原则

1. **统一抽象**: 所有执行单元统一为Step概念
2. **职责分离**: 注册、执行、调度、存储各司其职
3. **自动化**: 数据加载和保存全自动，用户只需关注业务逻辑
4. **可扩展**: 易于添加新的step类型和组件
5. **简洁优先**: KISS原则，代码简单易懂
6. **向后兼容**: 保留@active()等旧接口
