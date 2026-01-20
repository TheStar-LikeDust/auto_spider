# 构建与发布

## 开发环境安装

```bash
# 克隆项目
git clone https://github.com/TheStar-LikeDust/auto_spider.git
cd auto_spider

# 开发模式安装
pip install -e .

# 安装浏览器依赖
pip install -e .[browser]
playwright install chromium

# 安装开发依赖
pip install -e .[dev]
```

## 构建 Wheel 包

```bash
# 安装构建工具
pip install build

# 构建
python -m build

# 输出在 dist/ 目录
# dist/auto_spider-0.1.0-py3-none-any.whl
# dist/auto_spider-0.1.0.tar.gz
```

## 本地安装测试

```bash
# 从 wheel 安装
pip install dist/auto_spider-0.1.0-py3-none-any.whl

# 验证安装
auto-spider --version
auto-spider --help

# 验证 init 命令
mkdir test_project && cd test_project
auto-spider init
ls .claude/skills/
ls docs/
```

## 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 上传到 PyPI（正式）
twine upload dist/*
```

## 版本更新

1. 更新 `pyproject.toml` 中的 version
2. 更新 `auto_spider/cli/main.py` 中的 version_option
3. 重新构建：`python -m build`

## 清理构建产物

```bash
# Windows
rmdir /s /q build dist auto_spider.egg-info

# Linux/Mac
rm -rf build dist auto_spider.egg-info
```

## 项目结构（打包相关）

```
auto_spider/
├── pyproject.toml          # 项目配置（依赖、入口点）
├── README.md               # PyPI 页面显示
├── LICENSE                 # 许可证
└── auto_spider/            # 源代码包
    ├── skills/             # Skills 文档（package-data）
    ├── docs/               # 文档（package-data）
    └── ...
```

## package-data 配置

`pyproject.toml` 中已配置：

```toml
[tool.setuptools.package-data]
auto_spider = [
    "py.typed",
    "skills/**/*.md",
    "docs/*.md",
]
```

这确保 `skills/` 和 `docs/` 目录中的 `.md` 文件会被包含在 wheel 包中。
