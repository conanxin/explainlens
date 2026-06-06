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

预期输出：All tests passed (418 tests)。

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

打开 `cards.html` 后，可以点击卡片的 source citation 链接，跳转到页面底部的 Source Appendix，查看完整的原文摘录和引用关系。

## 7. 用自己的文件

```bash
python -m explainlens.cli analyze \
  --input path/to/your/document.md \
  --output outputs/my_run
```

支持 `.txt`、`.md` 和 `.pdf`（可搜索 PDF）格式。

## 8. 分析 PDF 文件

```bash
# 生成示例 PDF
python scripts/create_sample_pdf.py

# 分析 PDF，输出包含页码信息
python -m explainlens.cli analyze \
  --input examples/sample_paper.pdf \
  --output outputs/pdf_demo

# 预览结果
start outputs/pdf_demo/cards.html
```

PDF 输出会额外包含 `source_pages.json`，且每张卡片会显示来源页码和可点击的 citations。打开 `cards.html` 并点击 source citation 即可跳转到页面底部的 Source Appendix。

## 9. 试用不同 Provider

ExplainLens 支持多个分析后端：

```bash
# 查看所有可用的 provider
python -m explainlens.cli providers

# 使用 mock-llm provider（模拟 LLM 输出，不调用 API）
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/mock_run \
  --provider mock-llm

# 使用 local-fixture provider（离线协议测试）
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/local_fixture_demo \
  --provider local-fixture

# 使用 local-http provider fixture 模式（离线）
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/local_http_fixture \
  --provider local-http --local-http-protocol fixture

# 运行离线诊断
python -m explainlens.cli doctor

# 验证 loopback 端点
python -m explainlens.cli validate-endpoint http://localhost:11434/api/chat
```

mock-llm provider 使用更自然的叙事语言生成教学计划和概念分析，但完全不调用外部 API。local-fixture 和 local-http (fixture 模式) 均为完全离线运行。

---

## 了解更多

- [README.md](../README.md) — 项目概述
- [FAQ.md](FAQ.md) — 常见问题
- [ARCHITECTURE.md](ARCHITECTURE.md) — 系统架构
- [ROADMAP.md](ROADMAP.md) — 路线图
- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献指南
