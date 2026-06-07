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

**默认不会。** 当前版本的默认 provider（`rule-based`）和 mock provider（`mock-llm`）都不会发起任何网络请求。

Phase 3.3 已实现 `openai` provider（experimental），但**默认 fail-closed**——必须显式传递 `--allow-external-api` 并设置 `OPENAI_API_KEY` 环境变量才会实际调用 OpenAI API。

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

**可以，但需要显式 opt-in。** Phase 3.3 已实现 `openai` provider（experimental 状态）。

使用前提：
1. 设置环境变量 `OPENAI_API_KEY="sk-..."`
2. 传递 `--allow-external-api` 标志
3. 默认行为：**fail closed**（无此标志则拒绝调用，不创建输出文件）

```bash
# 设置 API key（不要提交到版本控制）
export OPENAI_API_KEY="sk-..."

# 运行 openai provider
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/openai_run \
  --provider openai \
  --allow-external-api
```

**重要**：
- 所有 81 个 OpenAI 测试都使用 mock fixture，CI 不调用真实 API
- Provider manifest 会披露 `uses_external_api: true`
- 无 `--allow-external-api` 时 fail-closed：不会创建任何输出文件

---

## 为什么需要 fail-closed？

`openai` provider 调用外部 API（api.openai.com），涉及网络请求和数据传输。fail-closed 设计确保：

1. **安全默认**：不显式 opt-in 就不会调用外部 API
2. **避免意外费用**：不设置 API key 就不会产生账单
3. **CI 兼容**：CI 环境无需 API key 即可运行 fail-closed 测试
4. **无残留输出**：fail-closed 时不会创建任何输出文件或目录

## 什么是 --allow-external-api？

`--allow-external-api` 是 Phase 3.3 引入的 CLI 参数，用于**显式 opt-in** 外部 API 调用。

**Fail-closed 行为：**

```bash
# 1. 不传 --allow-external-api（应该失败）
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/test \
  --provider openai
# 输出: Provider error: openai is fail-closed by default.
# No request was sent.

# 2. 传 --allow-external-api 但无 API key（应该失败）
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/test \
  --provider openai \
  --allow-external-api
# 输出: Provider error: OPENAI_API_KEY is not set.
# No request was sent.
```

## 为什么 OpenAI provider 曾经被禁用？

Phase 3.1 中 OpenAI provider 是 **disabled（禁用）** 的草案骨架。Phase 3.3 已将其从 `DISABLED_PROVIDERS` 移至 `AVAILABLE_PROVIDERS`，状态变为 `experimental`。

现在它可以实际调用 OpenAI Responses API（需 `--allow-external-api` + `OPENAI_API_KEY`），但仍保持 fail-closed 默认行为。

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

## local-http 会访问互联网吗？

**不会。** `local-http` provider 只向 **loopback 地址**（localhost / 127.0.0.1 / ::1）发送 HTTP 请求。

它**不会**：
- 访问 `https://...`（任何 HTTPS）
- 访问任何远程 HTTP 服务器
- 访问局域网地址（`192.168.x.x`、`10.x.x.x`、`172.16.x.x`）
- 发送 Authorization header 或 API key

---

## 为什么 local-http 需要 --allow-local-http？

`local-http` provider 默认 **fail closed**（关闭失败）——如果不显式允许，不会发送任何 HTTP 请求。

这样设计的原因：
1. **安全默认**：防止意外向本地服务发送文档内容
2. **显式选择**：用户必须明确理解并同意网络调用
3. **CI 兼容**：`protocol=fixture` 模式不需要 `--allow-local-http`，CI 可以安全运行

如果需要调用本地模型（如 Ollama），必须同时指定：
```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/ollama_local \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --allow-local-http
```

---

## 可以使用 Ollama 吗？

**可以，但需要显式 opt-in。**

`local-http` provider 支持 Ollama API 协议（`--local-http-protocol ollama-chat`）。

先确保 Ollama 在本地运行：
```bash
# 启动 Ollama（默认 http://localhost:11434）
ollama serve
# 另一个终端：拉取模型
ollama pull llama3.2
```

然后运行 ExplainLens：
```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/ollama_local \
  --provider local-http \
  --local-http-protocol ollama-chat \
  --local-http-endpoint http://localhost:11434/api/chat \
  --local-http-model llama3.2 \
  --allow-local-http
```

**重要**：当前版本 `local-http` 是 **experimental**——仅支持 loopback 地址，且需要显式允许。

---

## 可以使用 LM Studio 吗？

**可以，通过 OpenAI-compatible 协议。**

LM Studio 可以启动一个兼容 OpenAI API 的本地服务器。

在 LM Studio 中：
1. 加载一个模型
2. 点击 "Local API Server"
3. 启动服务器（默认 `http://localhost:1234/v1/chat/completions`）

然后运行 ExplainLens：
```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/lm_studio_local \
  --provider local-http \
  --local-http-protocol openai-compatible-chat \
  --local-http-endpoint http://localhost:1234/v1/chat/completions \
  --local-http-model local-model \
  --allow-local-http
```

---

## 允许哪些 endpoint？

`local-http` provider 只允许 **loopback** endpoint：

**✅ 允许：**
```
http://localhost:...
http://127.0.0.1:...
http://[::1]:...
```

**❌ 拒绝：**
```
https://...                    (任何 HTTPS)
http://example.com/...          (任何远程主机)
http://192.168.x.x/...       (私有局域网)
http://10.x.x.x/...           (私有局域网)
http://172.16.x.x/...        (私有局域网)
```

---

## 当前版本会生成真实图片吗？

**不会。** ExplainLens 当前版本的图片适配器都是纯本地 SVG 渲染器：

- **`placeholder`** — 生成本地 SVG 插图（教育风格，支持 4 种视觉样式）
- **`fixture`** — 确定性 SVG 用于 CI/测试

所有图片均为本地生成，不调用 DALL-E、Stable Diffusion、Midjourney 或任何外部图片 API。

---

## 什么是 image styles？

Image styles 是视觉样式预设，控制生成的 SVG 图片的外观：

- **`clean-cartoon-explainer`** — 干净的卡通风格，蓝色调（默认）
- **`whiteboard`** — 白板手绘风格，深灰色标记
- **`storybook`** — 温暖的绘本风格，琥珀色/橙色调
- **`technical-diagram`** — 精密的技术图表风格，绿色调

查看所有可用样式：

```bash
python -m explainlens.cli image-styles
```

选择样式：

```bash
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/demo \
  --image-style storybook
```

---

## 可以在演示文稿中使用 SVG 图片吗？

**可以。** 所有生成的 SVG 文件都是独立的矢量图形，可以直接：

- 拖入 PowerPoint / Keynote / Google Slides
- 嵌入 Notion / Obsidian / 其他 Markdown 编辑器
- 在浏览器中直接打开查看

SVG 文件不包含外部资源、不依赖外部字体、不引用网络 URL。

---

## 图片生成会上传我的文本吗？

**不会。** 当前所有图片适配器（`placeholder`、`fixture`）都是纯本地 SVG 渲染器：

- 不发送任何网络请求
- 不上传文档内容
- 不读取或使用 API key
- 所有处理都在本地完成

`image_manifest.json` 中明确标注 `"external_image_api": false`。

---

## 为什么图片是 SVG 占位图？

当前版本使用 SVG 占位图是因为：

1. **离线优先** — 不依赖外部 API，保护隐私
2. **确定性输出** — 每次运行结果一致，适合 CI/测试
3. **教育表达** — 视觉隐喻（迷宫、放大镜、桥梁等）比抽象 AI 图片更有教学意义

Phase 4B 已对 SVG 视觉质量进行了大幅优化：统一 16:9 画幅（960x540）、4 种视觉样式预设、
改进的卡片布局和构图。未来版本会在此接口基础上添加真实图片生成适配器。

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

Phase 4A 已建立图片生成适配器接口（`src/explainlens/images/`），目前实现：

- **`placeholder`** — 生成本地 SVG 占位图（默认，available）
- **`fixture`** — 确定性 SVG 用于 CI/测试（experimental）

可以通过 CLI 控制：

```bash
# 使用默认 placeholder 适配器
python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/demo

# 列出所有图片适配器
python -m explainlens.cli image-adapters

# 跳过图片生成（回退到 inline SVG）
python -m explainlens.cli analyze --input examples/sample_article.txt --output outputs/nopic --skip-images
```

Phase 4 将在此接口基础上添加真实图片生成适配器：

- `StableDiffusionAdapter` — 调用本地 SD WebUI API
- `DALLEAdapter` — 调用 OpenAI DALL-E API

当前所有 adapters 均为纯本地 SVG 生成，不调用外部图片 API。

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

---

## 如何检查我的本地 endpoint 是否被允许？

使用 `validate-endpoint` 命令进行**静态检查**（不发送任何网络请求）：

```bash
python -m explainlens.cli validate-endpoint http://localhost:11434/api/chat
# 输出：
# Endpoint: http://localhost:11434/api/chat
# Allowed: yes
# Reason: loopback endpoint

python -m explainlens.cli validate-endpoint https://api.openai.com/v1/chat/completions
# 输出：
# Endpoint: https://api.openai.com/v1/chat/completions
# Allowed: no
# Reason: only loopback endpoints (localhost, 127.0.0.1, ::1) are allowed for local-http
```

**此命令不会**：
- 连接到 endpoint
- 发送任何网络流量
- 执行 DNS 解析
- 读取任何 API key

它只做**静态验证**（检查 URL 是否符合 loopback-only 策略）。

---

## `doctor` 命令会调用我的模型吗？

**不会。** `doctor` 命令完全是离线的：

```bash
python -m explainlens.cli doctor
```

输出：
```
ExplainLens Doctor

Python: 3.x
Package import: OK
Providers:
  - rule-based: available
  - mock-llm: available
  - local-fixture: experimental
  - local-http: experimental
  - openai: disabled

Local HTTP:
  - Default network access: disabled
  - Allowed endpoint policy: loopback only
  - Remote endpoints: rejected
  - Authorization headers: never sent
  - Real local model check: skipped by default
```

**此命令不会**：
- 连接到任何网络 endpoint
- 读取 API key
- 执行任何外部命令
- 修改任何文件

它只做**离线诊断**，帮助您确认 ExplainLens 的安装状态。

---

## `validate-endpoint` 会发送请求吗？

**不会。** `validate-endpoint` 只做**静态 URL 验证**：

```bash
python -m explainlens.cli validate-endpoint http://localhost:11434/api/chat
```

验证逻辑：
1. 检查 URL scheme（只允许 `http://`，拒绝 `https://`）
2. 提取 hostname
3. 检查 hostname 是否在允许列表中（`localhost`、`127.0.0.1`、`::1`）
4. 返回结果

**整个过程不发送任何网络请求**，不进行 DNS 解析，不连接任何服务器。

---

## 本地 provider 配置示例在哪里？

配置模板在 `examples/configs/` 目录中：

```bash
examples/configs/
├── local-http-ollama.example.json       # Ollama 配置模板
├── local-http-lmstudio.example.json  # LM Studio 配置模板
└── local-http-llamacpp.example.json  # llama.cpp 配置模板
```

**注意**：这些只是**参考模板**，当前版本 CLI 不会自动读取这些 JSON 文件。它们用于：
- 文档说明
- 用户手动参考配置
- 理解 expected JSON 结构

详见 [Local Providers Guide](LOCAL_PROVIDERS.md)。

---

## 什么是 openai-image adapter？

`openai-image` 是一个**实验性**图片生成适配器，调用 OpenAI DALL-E API 生成真实图片。

**当前状态**：experimental（体验阶段）。

**安全设计**（follow OpenAI provider 的 fail-closed 模式）：
1. **默认关闭** — `allow_external_images = False`
2. **需要显式 opt-in** — 传递 `--allow-external-images` 并设置 `OPENAI_API_KEY`
3. **API key 永不打印、记录或写入任何文件**
4. **图片 prompt 不写入日志**
5. **Transport 可 mock 注入** — CI 和测试使用 mock transport，零真实 API 调用

---

## 如何启用 openai-image 图片生成？

**前提条件**：
1. 设置环境变量 `OPENAI_API_KEY="sk-..."`
2. 传递 `--allow-external-images` 标志
3. 选择 `--image-adapter openai-image`

```bash
# 设置 API key（不要提交到版本控制）
export OPENAI_API_KEY="sk-..."

# 运行 openai-image adapter
python -m explainlens.cli analyze \
  --input examples/sample_article.txt \
  --output outputs/openai_image_demo \
  --image-adapter openai-image \
  --allow-external-images
```

**重要**：
- 无 `--allow-external-images` 时 fail-closed：不会创建任何输出文件
- 无 `OPENAI_API_KEY` 时 fail-closed：不会发送任何请求
- 所有 测试都使用 mock transport — CI 不调用真实 API

---

## openai-image 安全吗？

**默认安全**。不设 `--allow-external-images` 就不会调用任何外部 API。

安全保障：
1. **默认 fail-closed** — 不显式 opt-in 就不会调用 API
2. **API key 受保护** — 仅从 `os.environ` 读取，永不缓存，永不记录
3. **Prompt 不泄漏** — 图片 prompt 不写入日志、stdout 或文件
4. **Transport 可 mock** — 所有 CI 测试使用 mock transport
5. **Manifest 透明** — `image_manifest.json` 始终披露 `uses_external_api: true`
6. **错误不泄漏数据** — 错误消息经过净化，不含 API key 或 prompt

---

## openai-image 生成的是真实图片吗？

**是的**——当您显式启用时。`openai-image` 调用 OpenAI DALL-E API 生成真实图片。

但默认情况下（无 `--allow-external-images`），它**不会**生成真实图片，而是 fail-closed 并报错。

如果您不想使用真实图片生成：
- 使用默认 `placeholder` adapter（本地 SVG 占位图）
- 或使用 `fixture` adapter（确定性 SVG，用于测试）

---
