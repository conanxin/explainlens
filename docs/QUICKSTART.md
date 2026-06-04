# Quick Start Guide

从克隆仓库到浏览器预览，完整步骤。

---

## 前置要求

- Python 3.10 或更高版本
- Git

## 1. 克隆仓库

```bash
git clone https://github.com/conanxin/explainlens.git
cd explainlens
```

## 2. 创建虚拟环境（推荐）

**Linux / macOS：**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows：**

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 3. 安装依赖

```bash
pip install -e ".[dev]"
```

这会将 ExplainLens 安装为可编辑包，同时安装 pytest 等开发依赖。

## 4. 运行测试

```bash
python -m pytest
```

预期输出：33 passed。

## 5. 运行示例

```bash
# 方式 A：模块方式（推荐）
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/sample_run

# 方式 B：CLI 命令（安装后可用）
explainlens analyze \
  --input examples/sample_article.txt \
  --output outputs/sample_run
```

## 6. 预览结果

在浏览器中打开：

```bash
# Windows
start outputs/sample_run/cards.html

# macOS
open outputs/sample_run/cards.html

# Linux
xdg-open outputs/sample_run/cards.html
```

你将看到 8 张图解卡片，每张卡片包含：
- 标题
- 简明解释
- 视觉隐喻 SVG 占位图
- 图片生成 prompt
- takeaway 要点
- 原文来源摘录

## 7. 用自己的文件

```bash
python -m explainlens.cli analyze \
  --input path/to/your/document.md \
  --output outputs/my_run
```

支持 `.txt` 和 `.md` 格式。

---

## 了解更多

- [README.md](../README.md) — 项目概述
- [FAQ.md](FAQ.md) — 常见问题
- [ARCHITECTURE.md](ARCHITECTURE.md) — 系统架构
- [ROADMAP.md](ROADMAP.md) — 路线图
- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献指南
