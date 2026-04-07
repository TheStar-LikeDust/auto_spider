# Auto Spider 项目结构

## 整体架构

```
auto_spider/
├── step/                    # Step数据结构 - 统一的执行单元定义
│   ├── __init__.py         # 导出所有step相关类型
│   ├── context.py          # Context - 所有step共用的上下文对象
│   ├── schemas.py          # 数据模式定义（Task, TaskResult, TaskData）
│   └── runner.py           # Step执行器 - 执行step函数序列
│
├── core/                    # 核心逻辑 - Step的注册、执行、调度
│   ├── __init__.py         # 导出核心API
│   ├── plan_config.py      # 计划配置 - PlanConfig类
│   ├── step_registry.py    # Step注册器 - 装饰器和注册管理
│   ├── plan_scheduler.py   # Plan调度器 - 多进程/线程调度
│   ├── stage.py            # Stage管理器 - 阶段任务和结果管理
│   ├── plan_worker.py      # Plan Worker - 单个worker执行逻辑
│   └── operations.py       # 操作工具 - 资源初始化、存储设置
│
├── cli/                     # CLI命令 - 基于Click的命令行工具
│   ├── __init__.py         # 导出命令函数
│   ├── main.py             # Click group和命令注册
│   ├── cmd_init.py         # init命令 - 初始化项目
│   ├── cmd_generate.py     # generate命令 - 生成模板
│   └── cmd_run.py          # run命令 - 运行plan
│
├── template/                # 模板生成 - Plan模板文件生成
│   ├── __init__.py         # 导出 generate_plan, generate_steps
│   ├── generator.py        # 模板生成逻辑
│   └── template_files/     # 模板文件目录
│       ├── action.py.txt
│       ├── extract.py.txt
│       ├── parse.py.txt
│       ├── plan.py.txt
│       ├── plan_single.py.txt
│       └── step_init.py.txt
│
├── storage/                 # 存储管理 - 输出目录和文件管理
│   ├── __init__.py         # 导出存储接口
│   ├── interface.py        # 存储接口定义
│   └── file_backend.py     # 文件存储后端实现
│
├── components/              # 组件库 - 可复用的功能组件
│   ├── __init__.py         # 延迟导入入口，避免依赖错误
│   └── spider/             # Spider子包 - 爬虫组件
│       ├── __init__.py
│       ├── base_spider.py      # BaseSpider - Spider基类
│       ├── request_spider.py   # RequestSpider - 基于requests的HTTP爬虫
│       ├── playwright_spider.py # PlaywrightSpider - 基于Playwright的浏览器爬虫
│       ├── cdp.py              # CDP相关定义
│       ├── cdp_spider.py       # CDPSpider - 基于CDP的调试爬虫
│       └── cdp_tools.py        # CDP工具函数
│
├── tools/                   # 工具集 - 常用工具函数
│   ├── __init__.py         # 导出工具函数
│   ├── xpath.py            # XPath提取工具
│   ├── html_cleaner.py     # HTML清洗工具
│   └── dedup.py           # 任务去重工具
│
├── docs/                    # 文档
│   ├── api.md              # API参考（用户文档）
│   ├── guide.md            # 使用指南（用户文档）
│   ├── build.md            # 构建打包（用户文档）
│   └── ai/                 # AI助手专用文档
│       ├── ai-assistant-guide.md   # AI助手规范
│       ├── skills_index.md         # Skills索引
│       └── project_structure.md    # 项目结构（本文件）
│
├── skills/                  # AI Skills定义
│   ├── sense-scout/        # 侦察页面
│   ├── sense-page-info/    # 分析交互元素
│   ├── sense-clean-html/   # 分析HTML结构
│   ├── plan-generate/      # 生成plan模板
│   ├── write-action/       # 编写action步骤
│   ├── write-parse/        # 编写parse步骤
│   ├── write-extract/      # 编写extract步骤
│   ├── exec-run-verify/    # 运行和验证
│   └── analyze-script/     # 复杂分析脚本
│
├── __init__.py             # 包入口 - 导出公共API
├── __main__.py             # CLI入口 - python -m auto_spider
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

#### `schemas.py` - 数据模式定义
- **作用**: 定义Task、TaskResult、TaskData等数据结构
- **包含**:
  - `Task` - action step的输入数据结构
  - `TaskResult` - parse step的输入数据结构
  - `TaskData` - extract step的输入数据结构
- **特点**:
  - 统一的数据类型定义
  - 支持字段验证和序列化

---

### 2. core/ - 核心逻辑

Step的生命周期管理，从注册到执行的完整流程。

#### `plan_config.py` - 计划配置
- **作用**: 定义PlanConfig类
- **配置项**:
  - `PLAN_NAME` - 计划名称
  - `OUTPUT_DIR` - 基础输出目录（最终: `<OUTPUT_DIR>/<PLAN_NAME>/action_xxx`）
  - `MAX_WORKERS` - Worker数量
  - `RATE_LIMIT` - 速率限制
  - `STORAGE_TIMESTAMP` - 是否带时间戳
  - `TASK_RETRY_COUNT` - 任务重试次数（默认3：1次初始 + 2次重试）

#### `step_registry.py` - Step注册器
- **作用**: 管理step函数的注册和获取
- **功能**:
  - 装饰器: `@action()`, `@parse()`, `@extract()`, `@active()`
  - 获取函数: `get_step()`, `get_all_steps()`, `get_all_actions()`, `get_all_parses()`, `get_all_extracts()`
- **特点**:
  - 装饰器自动注册函数
  - 支持优先级设置
  - 向后兼容: `@active()` 等同于 `@action()`

#### `plan_scheduler.py` - Plan调度器
- **作用**: 多进程/线程任务调度
- **功能**:
  - `run_plan()` - 主调度函数，传入 stage 参数执行指定阶段
  - `run_plan_with_file()` - 从文件加载并运行plan
  - `_run_single_stage()` - 单阶段执行逻辑
- **特点**:
  - 纯逻辑编排，无副作用代码
  - 参数验证在prepare阶段
  - 统一的stage_name和plan_config参数命名
  - 支持action/parse/extract三个阶段

#### `stage.py` - Stage管理器
- **作用**: 管理各阶段的任务获取和结果保存
- **功能**:
  - `get_tasks_for_stage()` - 获取指定阶段的任务列表
  - `save_stage_result()` - 保存阶段执行结果
- **特点**:
  - action阶段: 调用initial_task()获取任务
  - parse阶段: 自动加载action输出
  - extract阶段: 自动加载action和parse输出

#### `worker_core.py` - Worker核心
- **作用**: Worker的完整生命周期管理
- **功能**:
  - `dispatch_workers()` - 分发任务到workers
  - `_worker_loop()` - Worker主循环
  - `_process_result()` - 处理任务结果，增量任务写回 pending queue
- **特点**:
  - 统一使用 multiprocessing.Process
  - 资源延迟初始化（在prepare中）
  - 支持增量任务（context.tasks）

#### `worker_support.py` - Worker支持
- **作用**: feeder/collector线程、barrier同步、关闭助手
- **架构**:
  - `task_pending_queue` <- 初始任务 + 增量任务
  - `feeder_thread` -> 统一编号(_index) + 限速 -> `task_feeder_queue`
  - `collector_thread` <- result_queue -> storage
- **特点**:
  - feeder 通过 active_count 追踪任务完成，自动退出
  - 支持 rate limiting

---

### 3. cli/ - CLI命令

命令行工具实现，基于 Click 框架，与核心逻辑分离。

#### `main.py` - CLI入口和命令注册
- **作用**: Click group 定义和命令注册
- **命令**:
  - `init` (别名: i) - 初始化项目，复制 skills/docs
  - `generate` (别名: gen, g) - 生成plan和steps模板
  - `run` (别名: r) - 运行plan文件

#### `cmd_init.py` - init命令
- **作用**: 复制 skills 到 `.claude/skills/`，docs 到 `docs/`
- **选项**: `--skills-only`, `--docs-only`

#### `cmd_generate.py` - generate命令
- **作用**: 生成plan模板文件
- **参数**: `name` (plan名称)
- **选项**: `--module` (生成多文件模式，默认单文件)

#### `cmd_run.py` - run命令
- **作用**: 运行plan文件的指定阶段
- **选项**:
  - `--action/--parse/--extract` 指定执行阶段
  - `--retry-failed` 重试失败任务
  - step名称由plan文件中的 `ACTION_STEPS/PARSE_STEPS/EXTRACT_STEPS` 列表配置

---

### 4. template/ - 模板生成

Plan和Step模板文件生成。

#### `generator.py` - 模板生成器
- **作用**: 根据模板生成实际文件
- **函数**:
  - `generate_steps(name, description)` - 生成steps包
  - `generate_plan(name, description, single_file)` - 生成plan文件
- **生成结构**:
  ```
  steps_{name}/
    __init__.py
    action.py      # Action步骤
    parse.py       # Parse步骤
    extract.py     # Extract步骤
  ```

---

### 5. storage/ - 存储管理

输出目录和文件的管理，采用后端模式设计。

#### `interface.py` - 存储接口
- **作用**: 定义存储后端接口
- **特点**:
  - 抽象接口定义
  - 支持多种存储后端扩展

#### `file_backend.py` - 文件存储后端
- **作用**: 文件系统存储实现
- **功能**:
  - `create_output_dir()` - 创建带时间戳的输出目录
  - `save_task_result()` - 保存任务结果（html/json）
  - `find_latest_output_dir()` - 查找最新输出目录
  - `load_task_result()` - 加载任务结果
- **目录格式**: `<OUTPUT_DIR>/<PLAN_NAME>/{stage}_{timestamp}/`
- **文件格式**:
  - `{task_name}.html` - HTML内容（context['content']）
  - `{task_name}_task.json` - 原始Task（context.task）
  - `{task_name}_action.json` - action结果（context['result']）
  - `{task_name}_parse.json` - parse结果（仅parse阶段）

---

### 6. components/ - 组件库

可复用的功能组件，主要是各类Spider实现。

#### `__init__.py` - 组件入口
- **作用**: 导出spider组件
- **特点**:
  - 延迟导入，第三方库在使用时才加载
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
- **适用场景**: 静态页面、API请求

##### `playwright_spider.py` - PlaywrightSpider
- **作用**: 基于Playwright的浏览器爬虫
- **依赖**: `playwright>=1.40.0` (可选)
- **功能**:
  - 无头/有头浏览器
  - JavaScript渲染
  - 页面截图和PDF
- **适用场景**: 动态网页、需要JS执行的页面

##### `cdp_spider.py` - CDPSpider
- **作用**: 基于CDP的调试爬虫
- **依赖**: `playwright>=1.40.0` (可选)
- **功能**:
  - CDP协议调试
  - 页面元素分析
  - 可视化调试
- **适用场景**: 页面调试、元素分析

##### `cdp.py` & `cdp_tools.py` - CDP工具
- **作用**: CDP协议相关定义和工具函数
- **功能**:
  - CDP消息定义
  - 元素信息提取
  - 可交互元素检测

---

### 7. tools/ - 工具集

常用工具函数集合。

#### `xpath.py` - XPath提取工具
- **作用**: XPath表达式提取
- **函数**:
  - `xpath_extract(html, xpath)` - 提取匹配元素

#### `html_cleaner.py` - HTML清洗工具
- **作用**: 清洗HTML内容
- **函数**:
  - `clean_html(html)` - 清洗HTML，移除无用标签和属性
- **特点**:
  - 移除: script, style, meta, link, noscript, svg, iframe, comment
  - 保留: id, class, href, src, alt, title, name, type, value, placeholder

#### `dedup.py` - 任务去重工具
- **作用**: 任务去重
- **函数**:
  - `create_duplicate_checker(file_path)` - 创建去重器
  - `is_duplicate(checker, task)` - 检查任务是否重复
- **支持**: 内存模式、持久化文件模式

---

### 8. 顶层模块

#### `__main__.py` - CLI入口
- **作用**: 主CLI入口，支持 `python -m auto_spider`
- **实现**: 调用 `cli.main()`
- **使用**:
  ```bash
  python -m auto_spider generate myplan
  python -m auto_spider run myplan --action
  ```

#### `__init__.py` - 包入口
- **作用**: 导出公共API，提供统一的import接口
- **导出内容**:
  - Step数据结构: Context, Task, TaskResult, TaskData
  - 装饰器: action, parse, extract, active
  - 配置: PlanConfig
  - 函数: run_plan, generate_plan, generate_steps
  - 子模块: core, cli, template, storage, components, tools

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
                    TaskResult → parse step → 解析数据(.json)
                                                  ↓
                                             TaskData → extract step → 持久化确认
```

---

## 执行流程

```
1. 用户定义step函数
   @action() def fetch() ...
   @parse() def parse() ...

2. 装饰器自动注册
   step_registry.py 注册到全局表

3. 调用run_plan()
   plan_scheduler.py 准备并执行各阶段

4. 分配任务到worker
   plan_worker.py 分发任务到多进程/多线程

5. Worker执行step函数
   TaskWorker 预初始化资源后执行step

6. 自动保存结果
   stage.py + storage 保存到输出目录

7. 下一阶段自动加载
   stage.py 加载上一阶段输出
```

---

## 设计原则

1. **统一抽象**: 所有执行单元统一为Step概念
2. **职责分离**: 注册、执行、调度、存储各司其职
3. **扁平化结构**: cli、template、storage独立，不在core下
4. **后端模式**: storage支持多种后端扩展
5. **自动化**: 数据加载和保存全自动，用户只需关注业务逻辑
6. **可扩展**: 易于添加新的step类型和组件
7. **简洁优先**: KISS原则，代码简单易懂
8. **向后兼容**: 保留@active()等旧接口