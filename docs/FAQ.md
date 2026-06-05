# FAQ — 常见问题

---

## ExplainLens 是什么？

ExplainLens 是一个开源工具，它像一位 AI 教学导演。输入论文、长文或技术文档，它会自动：

1. 提取核心概念
2. 生成 8 步教学路径
3. 为每个概念匹配卡通视觉隐喻
4. 生成图片提示词
5. 输出可在浏览器预览的 HTML 图解卡片

一句话：**把复杂内容变成 8 张生动易懂的卡通图解解释卡。**

---

## 当前版本能处理 PDF 吗？

**可以！** Phase 2 已支持可搜索 PDF 的文本提取。

注意限制：

- **不支持扫描版 PDF**（无 OCR 功能）
- **不解析表格、公式和图形**
- 仅提取文本层，保留页码信息

使用方法：

```bash
python scripts/create_sample_pdf.py
python -m explainlens.cli analyze --input examples/sample_paper.pdf --output outputs/pdf_demo
```

---

## Source citations 是怎么工作的？

每张 ExplainLens 卡片都关联了原文片段（source chunk）。在 `cards.html` 中：

1. 每张卡片的 Source 区域显示可点击的 citation 链接，例如 `[chunk_001 · page 1]`
2. 点击 citation 会跳转到页面底部的 **Source Appendix**
3. Source Appendix 列出每个 source chunk 的完整摘录、页码、以及引用它的卡片列表
4. 每个卡片 ID 也可点击，返回对应卡片

说明：当前版本**不会**打开原始 PDF 页面，只会跳转到 HTML 页面内的 Source Appendix。后续可支持 PDF page viewer。

---

## 可以跳转回原始 PDF 吗？

**目前不可以。** Source Appendix 是 HTML 页面内的引用附录，不提供原始 PDF 文件跳转。

后续版本（Phase 2.2+）计划支持：
- PDF page viewer（在浏览器中逐页查看原 PDF）
- 从 citation 直接跳转到 PDF 对应页面

---

## ExplainLens 会引用精确的原文摘录吗？

**会。** 每张卡片都包含 `source_excerpt`（来源摘录），直接取自原文分块。Source Appendix 中显示完整的 chunk text（截断至 500 字符，保留核心内容）。

Source chunks 保留：
- 字符偏移（start_char / end_char）
- 页码信息（page_start / page_end，仅 PDF）
- 关联的卡片列表

---

## 当前版本会调用外部 AI API 吗？

**不会。** 当前版本使用启发式规则（关键词匹配、固定模板）完成所有分析。

ExplainLens 的 default provider (`rule-based`) 和 mock provider (`mock-llm`) 都不会发起任何网络请求。

Phase 3 已实现 provider 适配器接口（`--provider mock-llm`），但仍不调用真实 AI API。真实 LLM adapter（OpenAI、Ollama 等）将在后续版本接入。

---

## 什么是 mock-llm？

mock-llm 是一个本地 mock provider，用于测试 provider 接口的设计。它的输出比 rule-based 更像"LLM 风格"——使用更自然的叙事语言、对话式的教学解释——但完全不调用外部 API。

mock-llm 不会：
- 编造具体数据或论文结论
- 上传文档到外部服务
- 读取 API key

它会：
- 基于原文 chunks 生成结构化分析
- 为类比明确标记 `⚠ Teaching metaphor:` 前缀
- 保持每张卡片的 source_chunk_ids 完整可追溯

使用方法：
```bash
python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/mock_run --provider mock-llm
```

---

## 现在可以用 OpenAI 了吗？

**不可以。** 当前版本（v0.1.x）暂不提供 OpenAI provider。

Phase 3 已实现 provider 适配器接口的框架（base class + registry），但 `openai` provider 尚未实现。真实的 OpenAI / Anthropic / Ollama / 本地模型 adapter 将在后续 Phase 3.x 中接入。

届时，source citations 和 source_chunk_ids 仍然会保持完整——这是 provider contract 的硬性要求。

---

## 当前版本会生成真实图片吗？

**不会。** 当前版本只生成：

- **SVG 占位图**：在 HTML 卡片中展示构图概念
- **Image prompts**：英文文本提示词，可后续喂给 Stable Diffusion / DALL-E

Phase 4 将提供真实图片生成适配器。

---

## Image prompt 有什么用？

Image prompt 是设计给图像生成模型（如 Stable Diffusion、DALL-E）的英文提示词。

例如：

> bright clean cartoon explainer style, a detective examining clues on a corkboard with red strings connecting evidence, magnifying glass in hand, modern simple background, soft lighting, educational visual metaphor

你可以直接把这个 prompt 复制到 Midjourney、Stable Diffusion WebUI 或其他图片生成工具来生成实际配图。

---

## 为什么要保留 source chunk？

每个卡片都关联了原文片段（source chunk），这是 ExplainLens 的核心设计原则之一：

- **可追溯性**：你知道每张卡的解释来自原文的哪一段
- **可验证性**：可以自己对照原文确认总结是否准确
- **信任**：防止 AI 幻觉——每个结论都有出处

---

## 后续如何接入 LLM？

Phase 3 已实现 provider 适配器接口，当前提供两种 provider：

- `rule-based` — 当前规则引擎（默认）
- `mock-llm` — 模拟 LLM 输出的本地 mock provider

Provider 接口定义如下：

```python
class ExplainProvider(ABC):
    @abstractmethod
    def build_concept_map(self, chunks: list[SourceChunk]) -> ConceptMap: ...
    @abstractmethod
    def build_teaching_plan(self, chunks, concept_map) -> TeachingPlan: ...
    @abstractmethod
    def build_storyboard(self, chunks, concept_map, teaching_plan) -> Storyboard: ...
    @abstractmethod
    def build_cards(self, storyboard) -> list[ImageCard]: ...
```

后续将提供具体实现：

- `OpenAIProvider` — 调用 OpenAI API
- `LocalProvider` — 调用本地 Ollama / llama.cpp 模型
- `CustomProvider` — 用户自定义 API endpoint

用户可通过 CLI 参数选择 provider：

```bash
python -m explainlens.cli analyze --input doc.txt --output out/ --provider mock-llm
```

所有 provider 都必须遵守 provider contract：

- 保持 source_chunk_ids 完整
- 不编造数据或结论
- 正确设置 uses_external_api 标志
- 不向输出写入 secrets

---

## 后续如何接入图片生成？

Phase 4 将提供图片生成适配器，结构类似：

```python
class ImageGenAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> bytes: ...
```

适配器实现：

- `StableDiffusionAdapter` — 调用本地 SD WebUI API
- `DALLEAdapter` — 调用 OpenAI DALL-E API
- `PlaceholderAdapter` — 当前 SVG 占位图（默认）

---

## 为什么不用 Web UI？

第一版以 CLI 优先，原因：

- **简单**：CLI 更容易开发和维护
- **可组合**：CLI 输出 JSON/Markdown/HTML，可以轻松集成到其他工具
- **离线**：不依赖服务器，不需要 Docker

Phase 5 会添加可选的 Web UI。

---

## 可以用在中文内容上吗？

可以。虽然图片 prompt 目前生成为英文（因为主流图像模型对英文 prompt 效果更好），但分析逻辑支持中文输入。HTML 卡片界面也是中文的。

---

## 如何贡献？

欢迎！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

简单的开始方式：

1. Fork 项目
2. 给 `examples/` 添加一个有趣的示例文件
3. 提 PR
