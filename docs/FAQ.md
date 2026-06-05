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

## 为什么 OpenAI provider 被禁用了？

OpenAI provider 在 Phase 3.1 中是 **disabled（禁用）** 状态。

原因：
- Phase 3 的重点是 provider 契约硬化和安全边界，而非接入真实外部 API
- `openai` provider 的代码骨架已存在于 `src/explainlens/providers/openai_draft.py`
- 但它是 **draft 状态**，调用任何方法都会抛出清晰的 `RuntimeError`
- 当您尝试 `--provider openai` 时，会立即失败并提示可用的 providers

后续 Phase 3.x 会实现真实的 OpenAI adapter，并正确设置 `uses_external_api=true`。

---

## 什么是 provider_manifest.json？

每次运行都会输出 `provider_manifest.json`，记录 provider 的安全和行为声明。

内容示例：
```json
{
  "provider": "mock-llm",
  "provider_version": "mock-llm-v0.1",
  "provider_status": "available",
  "uses_external_api": false,
  "requires_api_key": false,
  "capabilities": {
    "supports_pdf": true,
    "supports_text": true,
    "preserves_source_chunk_ids": true
  },
  "safety": {
    "uploads_documents": false,
    "reads_api_key": false,
    "writes_secrets": false
  }
}
```

`provider_manifest.json` 用于：
- 审计 provider 行为（是否调用外部 API）
- CI 检查（`grep -q '"uses_external_api": false'`）
- 用户确认当前 provider 的安全属性

---

## Provider 可以移除 source citations 吗？

**不可以。** 保持 source_chunk_ids 完整是 provider contract 的硬性要求。

任何 provider 都必须：
- 每张卡片包含非空的 `source_chunk_ids`
- 每个 `source_chunk_id` 都必须存在于原始 chunks 中
- HTML 输出必须包含可点击的 citation 和 Source Appendix

如果 provider 移除了 source citations，契约验证（`validate_provider_output()`）会返回错误。

---

## mock-llm 会调用 LLM 吗？

**不会。** `mock-llm` provider 完全不调用任何外部 LLM。

它的输出虽然使用了更自然的叙事语言（"The core tension here is...", "Here's the thing..."），但：
- 完全基于原文 chunks 生成
- 不联网
- 不读取 API key
- 不编造数据或论文结论
- 类比明确标记 `⚠ Teaching metaphor:` 前缀

`mock-llm` 的作用是：
1. 测试 provider 接口的设计
2. 为未来接入真实 LLM 提供测试框架
3. 验证所有 provider 都能保持 source traceability

---

## 什么是 local-fixture？

`local-fixture` 是一个**实验性（experimental）**的离线 provider，用于测试未来本地模型 provider 的请求/响应协议。

它的工作方式：
1. `prompt_contract.py` 构建结构化的 prompt pack
2. `fixture_transport.py` 模拟本地模型返回结构化响应
3. `response_contract.py` 验证响应符合契约

**重要**：`local-fixture` 是完全离线的——不调用任何模型、HTTP 端点或子进程。它只是模拟协议流程。

---

## local-fixture 会调用 Ollama 吗？

**不会。** `local-fixture` 完全离线，不调用任何本地模型（Ollama、LM Studio、llama.cpp 等），也不发起任何 HTTP 请求。

它使用了 fixture transport（fixture_transport.py）来模拟响应，不依赖任何外部进程。未来 Phase 3.2B 才会接入真实的本地 HTTP provider。

---

## 什么是 provider_prompt_pack.json？

`provider_prompt_pack.json` 是一个可选的调试输出文件，使用 `--dump-provider-prompt` 参数生成。

它展示了如果接入真实 LLM，系统会发送什么样的结构化 prompt，包括：
- 源文本 chunks（带 chunk_id 和页码信息）
- 输出格式约定（output contract，要求 8 张卡片及其必需字段）
- 安全规则（safety rules，如"保持 source_chunk_ids""不要编造说法"）

这个文件**不包含任何 secrets、API key 或环境变量**。

运行命令：
```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/debug \
  --provider local-fixture \
  --dump-provider-prompt
```

---

## 可以预览将发送给模型的内容吗？

**可以。** 使用 `--dump-provider-prompt` 参数运行 `local-fixture` provider，即可在输出目录找到 `provider_prompt_pack.json`。

这个文件包含了完整结构化的 prompt pack——source chunks、output contract 和 safety rules——就是将来真实 LLM provider 会接收的内容。

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/debug \
  --provider local-fixture \
  --dump-provider-prompt
```

然后查看 `outputs/debug/provider_prompt_pack.json`。

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
