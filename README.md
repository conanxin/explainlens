# ExplainLens

**Turn papers and complex texts into visual explainer cards and cartoon storyboards.**

中文名：图解复杂内容的 AI 教学导演

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

---

## 简介

ExplainLens 是一个开源工具，它像一位 AI 教学导演，能够：

1. 解析论文、长文、技术文档等复杂内容
2. 自动提取核心概念和关键论点
3. 生成符合人类认知顺序的教学路径
4. 为每个概念匹配生动的卡通视觉隐喻
5. 生成图片提示词（可后续接入图像生成 API）
6. 输出可视化 HTML 卡片预览

核心体验：**复杂内容 → 8 张图解卡片**

每张卡片包含：标题、简明解释、视觉隐喻、卡通画面描述、图片 prompt、takeaway、原文来源片段。

## 功能特性

- 📖 **文本解析** — 支持 `.txt` 和 `.md` 文件
- 🔪 **智能分块** — 按段落切分，保留字符偏移
- 🔍 **关键词分析** — 启发式提取核心问题、概念、方法、证据、局限
- 🎓 **教学路径** — 8 步固定教学计划
- 🎨 **卡通隐喻** — 迷宫、放大镜、侦探板、知识树等 8 种视觉隐喻
- 🖼️ **图片 Prompt** — 生成英文 prompt，适配 Stable Diffusion / DALL-E
- 📄 **多格式导出** — JSON / Markdown / HTML
- 🧩 **SVG 占位图** — 无外部 API 依赖，纯本地运行

## 安装

```bash
git clone https://github.com/explainlens/explainlens.git
cd explainlens
pip install -e .
```

或仅安装运行依赖：

```bash
pip install jinja2 pydantic
```

## 快速开始

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/sample_run
```

然后用浏览器打开 `outputs/sample_run/cards.html` 预览结果。

## 输出文件

运行后，输出目录包含：

| 文件 | 说明 |
|------|------|
| `source_chunks.json` | 原文分块结果 |
| `concept_map.json` | 核心概念提取 |
| `teaching_plan.json` | 8 步教学计划 |
| `storyboard.json` | 卡通分镜脚本 |
| `image_prompts.json` | 图片生成提示词 |
| `cards.json` | 最终卡片数据 |
| `cards.md` | Markdown 格式卡片 |
| `cards.html` | 浏览器可预览的 HTML 卡片 |
| `run_summary.json` | 运行摘要 |

## 运行测试

```bash
pip install pytest
python -m pytest
```

## 项目架构

```
explainlens/
├── src/explainlens/    # 核心源码
│   ├── parser.py       # 文档解析
│   ├── chunker.py      # 文本分块
│   ├── analyzer.py     # 关键词分析
│   ├── prompts.py      # 提示词模板
│   ├── planner.py      # 教学计划生成
│   ├── storyboard.py   # 卡通分镜生成
│   ├── renderer.py     # HTML 渲染
│   ├── exporters.py    # 多格式导出
│   ├── schemas.py      # 数据模型
│   └── cli.py          # CLI 入口
├── tests/              # 测试
├── examples/           # 示例输入
├── docs/               # 文档
└── outputs/            # 输出目录
```

## 路线图

详见 [ROADMAP.md](docs/ROADMAP.md)：

- **Phase 1** ✅ 本地文本 → 解释卡（当前版本）
- **Phase 2** PDF 解析
- **Phase 3** LLM 插件接口
- **Phase 4** 真实图片生成适配器
- **Phase 5** Web UI
- **Phase 6** 长图/PPT/视频导出

## 贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

## License

MIT License — 详见 [LICENSE](LICENSE)。
