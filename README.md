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

## 快速开始

```bash
# 1. 生成项目模板
python -m auto_spider generate myplan

# 2. 配置 plan_myplan.py 和步骤函数

# 3. 运行
python plan_myplan.py
```

详细开发流程请查看 [使用指南](docs/guide.md)

## CLI 命令

| 命令 | 说明 |
|------|------|
| `python -m auto_spider generate <plan>` | 生成项目模板 |
| `python -m auto_spider run <file> <step> -s <stage>` | 运行指定阶段 |
| `python -m auto_spider run <file> <step> -w <num>` | 指定worker数量 |

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
@action()   # 注册到Action阶段
@parse()    # 注册到Parse阶段
@extract()  # 注册到Extract阶段
```

### 并发模型

| 阶段 | 并发方式 |
|------|---------|
| Action | 多进程 |
| Parse | 多线程 |
| Extract | 多线程 |

## 文档

- [使用指南](docs/guide.md) - 快速开始、核心概念、常见场景
- [API 参考](docs/api.md) - CLI、Config、Context、Spider、工具函数
- [项目结构](docs/project_structure.md) - 架构设计、模块说明

## License

MIT
