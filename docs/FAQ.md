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

## 当前版本会调用外部 AI API 吗？

**不会。** 当前版本使用启发式规则（关键词匹配、固定模板）完成所有分析。

Phase 3 将提供 LLM 插件接口，届时可接入 OpenAI、Ollama 或本地模型来提升分析质量。

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

Phase 3 将设计一个抽象的 LLM 接口层：

```python
class LLMBackend(ABC):
    @abstractmethod
    def analyze(self, chunks: list[SourceChunk]) -> ConceptMap: ...
    @abstractmethod
    def plan_teaching(self, concept_map: ConceptMap) -> TeachingPlan: ...
```

然后提供具体实现：

- `OpenAIBackend` — 调用 OpenAI API
- `OllamaBackend` — 调用本地 Ollama 模型
- `HeuristicBackend` — 当前规则引擎（默认）

用户可通过配置文件或 CLI 参数选择后端。

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
