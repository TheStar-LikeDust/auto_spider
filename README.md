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
# 生成项目
auto-spider generate myplan --single-file

# 编辑 plan_myplan.py，配置 URL 和解析逻辑

# 运行
auto-spider run plan_myplan.py fetch_page --stage action
auto-spider run plan_myplan.py parse_data --stage parse
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

```bash
auto-spider init              # 初始化 skills 和 docs（给 AI 助手用）
auto-spider generate <name>   # 生成项目模板
auto-spider run <file> <step> # 运行指定步骤
```

## 文档

- [使用指南](auto_spider/docs/guide.md)
- [API 参考](auto_spider/docs/api.md)
- [构建打包](auto_spider/docs/build.md)

## License

MIT
