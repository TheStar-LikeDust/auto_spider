# Plan Configuration System

## 📋 快速总结

### 配置项清单（明确可见）

```python
from auto_spider.core import PlanConfig

config = PlanConfig(
    plan_name='myplan',      # Plan名称（输出目录命名）
    max_workers=4,           # Worker并发数量
    rate_limit=None,         # 任务间延迟(秒)，None=无限制
    output_dir=None,         # 自定义输出目录，None=自动创建
)
```

### 默认配置（在模块中定义）

```python
from auto_spider.core import DEFAULT_CONFIG

# 默认值
DEFAULT_CONFIG = PlanConfig(
    plan_name=None,
    max_workers=4,
    rate_limit=None,
    output_dir=None,
)
```

---

## 🎯 设计决策：字典 + 属性

### 为什么选择这种方式？

参考了你们的 `Context` 类设计：

```python
# Context 类：继承 dict + 属性访问
class Context(dict):
    def __init__(self, spider=None, task=None, ...):
        self.spider = spider    # 属性
        self.task = task        # 属性
        self['data'] = ...      # 字典

# 用户代码
context.spider.do_url(url)     # 属性访问（系统资源）
context['result'] = data       # 字典访问（业务数据）
```

**PlanConfig 采用相同模式**：

```python
config = PlanConfig(plan_name='test', max_workers=2)

# 属性访问（推荐，有IDE提示）
print(config.plan_name)
config.max_workers = 4

# 字典访问（灵活）
print(config['plan_name'])
config['rate_limit'] = 1.0

# 两种方式自动同步
config.max_workers = 8
print(config['max_workers'])  # 8
```

---

## ✅ 推荐用法

### 在 Plan 文件中

```python
# ============== Configuration ==============

PLAN_CONFIG = {
    'plan_name': 'myplan',
    'max_workers': 2,
    'rate_limit': 1.0,
}

STAGES = {
    'action': ['fetch_page'],
    'parse': ['parse_data'],
    'extract': ['save_data'],
}

# ============== Execution ==============

if __name__ == '__main__':
    # 直接解包字典（最简单）
    run_plan(
        initial_spider, initial_task, initial_plan,
        actions=STAGES['action'],
        **PLAN_CONFIG  # 解包配置
    )
```

### 好处

1. **配置集中**：所有配置在顶部一目了然
2. **易于修改**：只需改字典值
3. **类型清晰**：有注释说明每个配置项
4. **零学习成本**：Python内置字典

---

## 📚 API文档

### PlanConfig 类

```python
class PlanConfig(dict):
    """
    Plan配置，支持属性和字典双重访问。
    
    字段：
        plan_name: Plan名称
        max_workers: Worker数量
        rate_limit: 速率限制(秒)
        output_dir: 输出目录
    """
```

### DEFAULT_CONFIG

```python
DEFAULT_CONFIG: PlanConfig
# 全局默认配置，可以作为基础配置
```

### merge_config()

```python
def merge_config(base: PlanConfig, overrides: dict) -> PlanConfig:
    """
    合并配置，overrides覆盖base。
    
    示例：
        config = merge_config(DEFAULT_CONFIG, {
            'plan_name': 'myplan',
            'max_workers': 2,
        })
    """
```

### load_config_from_module()

```python
def load_config_from_module(module) -> PlanConfig:
    """
    从Plan模块加载PLAN_CONFIG。
    
    示例：
        # plan.py 中定义
        PLAN_CONFIG = {'plan_name': 'test', ...}
        
        # 加载
        config = load_config_from_module(plan_module)
    """
```

---

## 🔄 对比：旧方式 vs 新方式

### 旧方式（分散）

```python
ACTION_LIST = ['fetch_page']
PARSE_LIST = ['parse_data']
EXTRACT_LIST = ['save_data']

if __name__ == '__main__':
    run_plan(initial_spider, initial_task, initial_plan, 
             actions=ACTION_LIST, 
             plan_name='myplan',    # 分散配置
             max_workers=2,         # 分散配置
             rate_limit=3)          # 分散配置
```

**问题**：
- 配置分散在多处
- 每个阶段都要重复写配置
- 容易遗漏某些参数

### 新方式（集中）

```python
PLAN_CONFIG = {
    'plan_name': 'myplan',
    'max_workers': 2,
    'rate_limit': 1.0,
}

STAGES = {
    'action': ['fetch_page'],
    'parse': ['parse_data'],
    'extract': ['save_data'],
}

if __name__ == '__main__':
    run_plan(..., actions=STAGES['action'], **PLAN_CONFIG)
```

**优势**：
- ✅ 配置集中在顶部
- ✅ 一次定义，多处复用
- ✅ 清晰的结构分区

---

## 💡 最佳实践

### 1. 配置在顶部

```python
# ✅ 好：配置在顶部
PLAN_CONFIG = {...}
STAGES = {...}

def initial_spider(): ...
def initial_task(): ...
```

```python
# ❌ 差：配置在底部
def initial_spider(): ...
def initial_task(): ...

PLAN_CONFIG = {...}  # 不直观
```

### 2. 使用字典解包

```python
# ✅ 好：解包传参
run_plan(..., **PLAN_CONFIG)
```

```python
# ❌ 差：手动传参
run_plan(..., 
         plan_name=PLAN_CONFIG['plan_name'],
         max_workers=PLAN_CONFIG['max_workers'],
         rate_limit=PLAN_CONFIG['rate_limit'])
```

### 3. 属性访问读取

```python
config = PlanConfig(**PLAN_CONFIG)

# ✅ 好：属性访问（有提示）
print(config.plan_name)
print(config.max_workers)
```

```python
# ⚠️ 可以但不推荐：纯字典访问
print(config['plan_name'])
print(config['max_workers'])
```

---

## 📖 完整示例

参考文件：
- `examples/plan_with_config.py` - 完整示例
- `tests/test_plan_config.py` - 测试用例
- `auto_spider/core/PLAN_CONFIG_USAGE.md` - 详细用法

---

## 🚀 迁移指南

### 从旧模板迁移

**步骤1：添加PLAN_CONFIG字典**

```python
# 旧
PLAN_NAME = 'myplan'
MAX_WORKERS = 2
RATE_LIMIT = 1.0

# 新
PLAN_CONFIG = {
    'plan_name': 'myplan',
    'max_workers': 2,
    'rate_limit': 1.0,
}
```

**步骤2：合并阶段列表**

```python
# 旧
ACTION_LIST = ['fetch_page']
PARSE_LIST = ['parse_data']
EXTRACT_LIST = ['save_data']

# 新
STAGES = {
    'action': ['fetch_page'],
    'parse': ['parse_data'],
    'extract': ['save_data'],
}
```

**步骤3：更新run_plan调用**

```python
# 旧
run_plan(initial_spider, initial_task, initial_plan,
         actions=ACTION_LIST, plan_name='myplan', 
         max_workers=2, rate_limit=1.0)

# 新
run_plan(initial_spider, initial_task, initial_plan,
         actions=STAGES['action'], **PLAN_CONFIG)
```

---

## 🎓 总结

1. **明确的配置项**：`PlanConfig` 类定义了所有可用字段
2. **默认配置**：`DEFAULT_CONFIG` 提供默认值
3. **双重访问**：属性访问（IDE提示）+ 字典访问（灵活）
4. **简单易用**：字典配置，零学习成本
5. **符合规范**：遵循 KISS 原则，与 Context 设计一致
