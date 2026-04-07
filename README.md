# Auto Spider

三阶段爬虫框架：**Action**（下载）→ **Parse**（解析）→ **Extract**（保存）

## 安装

```bash
git clone https://github.com/TheStar-LikeDust/auto_spider.git
cd auto_spider
pip install -e .
```

浏览器自动化（可选）：
```bash
pip install -e .[browser]
playwright install chromium
```

## 快速开始

```bash
# 生成项目模板
auto-spider generate myplan

# 编辑 myplan.py，配置 URL 和解析逻辑

# 运行（.py 扩展名可选）
auto-spider run myplan --action
auto-spider run myplan --parse
```

## 代码示例

```python
from auto_spider import action, parse, extract, Context

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    context['content'] = context.spider.do_url(url)

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    context['result'] = {'title': '...', 'data': [...]}

@extract()
def save_data(context: Context):
    data = context.get('input', {})
    # 保存到数据库
```

## CLI 命令

### init

```bash
auto-spider init [TARGET]          # 复制 skills 和 docs 到目标目录（默认当前目录）
auto-spider init --skills-only     # 只复制 skills
auto-spider init --docs-only       # 只复制 docs
```

### generate

```bash
auto-spider generate <name>            # 生成单文件 {name}.py
auto-spider generate <name> --module   # 生成 {name}.py + steps_{name}/ 模块结构
auto-spider generate <name> -d "描述"  # 附加 plan 描述
```

### run

```bash
auto-spider run <name> --action                  # 运行 action 阶段（下载）
auto-spider run <name> --parse                   # 运行 parse 阶段（解析）
auto-spider run <name> --extract                 # 运行 extract 阶段（保存）
auto-spider run <name> --action --parse          # 连续运行多个阶段
auto-spider run <name> --action --retry-failed   # 重跑上次失败的任务
auto-spider run <name> --action -i key=value     # 传参给 initial_task 控制 task 生成
auto-spider run <name> --action -t key=value     # 向每个 task 注入额外参数
auto-spider run <name> --action -t a=1 -t b=2    # 可重复 -t 传多个参数
```

执行哪些 step 由 plan 文件中的 `ACTION_STEPS` / `PARSE_STEPS` / `EXTRACT_STEPS` 列表决定。

## 文档

- [使用指南](auto_spider/docs/guide.md)
- [API 参考](auto_spider/docs/api.md)
- [Context 详解](auto_spider/docs/context.md)
- [构建打包](auto_spider/docs/build.md)

## License

MIT