# NexDR (Nex Deep Research) - 修改版

<div align="center">

**NexDR** 是一个基于 [Nex-N1](https://huggingface.co/nex-agi/DeepSeek-V3.1-Nex-N1) 智能体模型和 [NexAU](https://github.com/nex-agi/nexau) 智能体框架构建的深度研究智能体。它能够自主分解研究任务、进行并行调查，并生成结构化的研究报告。

**这是一个增强修改版本**，具备以下新功能：
- 📚 **学术搜索** - 集成 Semantic Scholar API 用于学术研究
- 🔄 **交互式反馈循环** - 通过用户 - 智能体协作用户修改报告
- 📎 **多格式输入** - 支持 PDF、图片等多种文档类型

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

</div>

---

## 🆕 版本新增内容

### 1. Semantic Scholar 学术搜索 🔬

新增 Semantic Scholar API 作为替代搜索源，专用于学术研究：

- **学术聚焦** - 搜索同行评审论文，含引用指标
- **高级过滤** - 按年份筛选，按引用数/影响力/出版日期排序
- **丰富元数据** - 作者、摘要、期刊、引用数、参考文献
- **免费额度** - 无需 API Key 即可使用（100 次/天）

```python
# Agent 会自动选择合适的搜索源
# 或在查询中指定："搜索关于 transformer 模型的学术论文"
```

**实现文件**：`nexdr/agents/deep_research/semantic_scholar_search.py`

---

### 2. 交互式 Markdown 反馈循环 🔄

通过与用户协作迭代生成报告：

- **用户编辑** - 修改生成的 Markdown 报告
- **自动检测** - 系统检测你的修改（新增/修改/删除的章节）
- **意图分析** - Agent 理解你的编辑意图
- **智能修订** - Agent 基于你的修改继续完善
- **不覆盖** - 你的修改始终被保留

```bash
# 启用反馈循环
python quick_start.py \
  --query "人工智能在医疗领域的应用" \
  --report_format markdown \
  --use_feedback_loop \
  --max_iterations=3
```

**工作流程**：
```
Agent 生成初稿 → 你编辑 → Agent 检测变更 → 
Agent 分析意图 → Agent 修订 → 重复直到满意
```

**实现文件**：
- `nexdr/agents/markdown_report_writer/detect_user_changes.py`
- `nexdr/agents/markdown_report_writer/detect_user_changes.py::infer_user_intent()`

---

### 3. 多格式输入支持 📎

与研究查询一起处理各种输入格式：

- **PDF 文档** - 使用 pypdf 提取文本
- **图片** - 使用多模态 LLM 生成描述或 OCR 识别
- **文本文件** - .txt, .md, .csv, .json, .yaml 等
- **自动处理** - 所有文件解析后整合到研究中

```bash
# 处理 PDF、图片和文本文件
python quick_start.py \
  --query "总结这些研究论文" \
  --report_format markdown \
  --input_files paper1.pdf paper2.pdf chart.png notes.md
```

**实现文件**：`nexdr/agents/doc_reader/file_parser.py`（扩展）

---

## 📦 安装说明

### 前置要求

- Python 3.12 或更高版本
- pip 或 uv 包管理器

### 使用 uv（推荐）

```bash
# 克隆仓库
git clone https://github.com/Bamboovan/deep-researcher.git
cd deep-researcher

# 使用 uv 安装
uv sync
```

### 使用 pip

```bash
# 克隆仓库
git clone https://github.com/Bamboovan/deep-researcher.git
cd deep-researcher

# 安装依赖
pip install -e .

# 可选：额外格式支持
pip install pypdf        # PDF 解析
pip install pytesseract  # 图片 OCR
pip install Pillow       # 图片处理
```

### 环境配置

在项目根目录创建 `.env` 文件：

```bash
# LLM 调用（必需）
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 网络搜索（必需）
SERPER_API_KEY=your_serper_api_key

# 可选：Semantic Scholar（有免费额度）
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# 可选：文档解析（至少选择一个）
JINA_API_KEY=your_jina_api_key
DOC_READER_PROVIDERS=jina,serper

# 可选：多模态图片描述
MULTI_MODAL_LLM_API_KEY=sk-xxxxx
MULTI_MODAL_LLM_BASE_URL=https://api.openai.com/v1
MULTI_MODAL_LLM_MODEL=gpt-4-vision-preview

# 可选：Langfuse 追踪
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

**获取 API Key**：
- Serper API: https://serper.dev/ (每月 100 次免费)
- Semantic Scholar: https://www.semanticscholar.org/product/api (每天 100 次免费)
- OpenAI: https://platform.openai.com/api-keys

---

## 🚀 快速开始

### 基础用法

运行研究任务并生成 Markdown 报告：

```bash
python quick_start.py \
  --query "量子计算的最新进展是什么？" \
  --report_format markdown \
  --output_dir workspaces/my_research
```

### 启用交互式反馈循环 ⭐

```bash
python quick_start.py \
  --query "人工智能在金融领域的应用" \
  --report_format markdown \
  --use_feedback_loop \
  --max_iterations=3 \
  --output_dir workspaces/finance_research
```

**交互流程**：
1. Agent 生成初始报告
2. 使用你喜欢的编辑器编辑 `markdown_report.md`
3. 在终端按 Enter
4. 系统检测你的修改并分析意图
5. Agent 基于你的修改进行修订
6. 重复直到你输入 `done`

### 处理输入文件 📎

```bash
python quick_start.py \
  --query "总结这些论文的关键发现" \
  --report_format markdown \
  --input_files paper1.pdf paper2.pdf data.csv \
  --output_dir workspaces/paper_review
```

### 学术研究模式 🔬

```bash
python quick_start.py \
  --query "大语言模型推理能力研究综述" \
  --report_format markdown \
  --use_feedback_loop \
  --output_dir workspaces/llm_survey
```

Agent 会优先使用 Semantic Scholar 进行学术搜索。

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--query` | 研究问题（必需） | - |
| `--report_format` | 输出格式：`markdown`, `html`, `markdown+html` | `markdown` |
| `--output_dir` | 保存结果的目录 | `workspaces/workspace_时间戳` |
| `--use_feedback_loop` | 启用交互式修订模式 | `False` |
| `--max_iterations` | 最大反馈迭代次数 | `3` |
| `--input_files` | 要处理的输入文件（PDF、图片等） | `None` |

---

## 📊 输出结构

运行研究任务后：

```
workspaces/my_research/
├── logs_时间戳.log           # 详细执行日志
├── markdown_report.md           # 最终研究报告
├── citations.json               # 引用参考文献
├── final_state.json            # 执行元数据和统计信息
├── *.extracted.txt             # 从输入文件提取的文本
└── (过程文件已清理)             # 临时文件自动删除
```

**启用反馈循环时**：
- 过程文件（`markdown_report.original.md`、`markdown_report.user.md`）在完成后自动删除
- 仅保留最终的 `markdown_report.md`

---

## 🔧 高级功能

### 1. 变更检测与意图分析

系统自动检测并分析你的修改：

**检测的变更**：
- 新增章节（你编写的新内容）
- 修改章节（你编辑的内容）
- 删除章节（你移除的内容）
- 行级差异统计

**意图分析**：
- 识别你是在添加结论、方法论还是一般内容
- 识别对引言或现有章节的完善
- 识别简化操作（删除）
- 为 Agent 提供合适的后续建议

**输出示例**：
```
✓ 检测到变更：
  +50 行添加；-20 行删除；2 个新章节
  新增章节：伦理考量、未来展望
  修改章节：引言、诊断应用

意图分析：
  - 用户新增了总结/展望部分，可能需要补充完整的结论
  - 用户修改了引言，可能希望调整文章的基调或重点
  - 请保留用户的所有修改，不要覆盖
```

### 2. 多格式文件解析

**支持的格式**：

| 类型 | 扩展名 | 处理方式 |
|------|--------|----------|
| 文本 | .txt, .md, .py, .json, .csv, .yaml, .html | 直接读取 |
| PDF | .pdf | pypdf 提取 |
| 图片 | .jpg, .png, .gif, .bmp, .webp | 多模态 LLM 描述 或 OCR |

**图片处理策略**：
1. **优先**：多模态 LLM 生成详细描述
2. **降级**：OCR 提取可见文本
3. **优雅降级**：即使没有 API Key 也能工作（功能受限）

### 3. 学术搜索能力

**Semantic Scholar 功能**：
- 按关键词搜索，聚焦学术领域
- 按出版年份范围过滤
- 按相关性、引用数、出版日期、影响力排序
- 获取：标题、摘要、作者、期刊、引用数、参考文献、PDF 链接

**查询示例**：
```
"查找关于图神经网络在欺诈检测中应用的最新论文（2023-2025 年）"
```

Agent 将：
- 使用 Semantic Scholar API
- 过滤 2023-2025 年
- 按引用数排序
- 提取关键发现和方法论

---

## 🎯 使用场景

### 1. 学术文献综述

```bash
python quick_start.py \
  --query "NLP 中 transformer 架构研究综述" \
  --report_format markdown \
  --use_feedback_loop \
  --input_files related_papers.pdf \
  --output_dir workspaces/lit_review
```

### 2. 市场研究与数据分析

```bash
python quick_start.py \
  --query "分析电动汽车市场趋势和竞争格局" \
  --report_format markdown \
  --use_feedback_loop \
  --input_files market_data.csv competitor_analysis.pdf \
  --output_dir workspaces/ev_market
```

### 3. 从论文生成技术文档

```bash
python quick_start.py \
  --query "解释这些论文的方法和结果" \
  --report_format markdown \
  --input_files paper1.pdf paper2.pdf architecture.png \
  --output_dir workspaces/tech_doc
```

### 4. 迭代式报告完善

```bash
# 开始研究
python quick_start.py \
  --query "气候变化对农业的影响" \
  --report_format markdown \
  --use_feedback_loop \
  --max_iterations=5

# 然后：
# 1. 编辑报告添加区域焦点
# 2. Agent 检测并扩展你的添加内容
# 3. 再次编辑完善结论
# 4. Agent 润色并添加支持证据
# 5. 满意后输入 'done'
```

---

## 🏗️ 架构说明

### 修改的组件

```
NexDR (修改版)
├── nexdr/agents/deep_research/
│   ├── search.py                    # 扩展：添加 semantic_scholar 搜索源
│   ├── semantic_scholar_search.py   # 新增：学术搜索实现
│   ├── web_search.py                # 原有网络搜索
│   └── arxiv_search.py              # 原有 Arxiv 搜索
│
├── nexdr/agents/markdown_report_writer/
│   ├── detect_user_changes.py       # 新增：变更检测与意图分析
│   └── __init__.py                  # 新增：模块初始化
│
├── nexdr/agents/doc_reader/
│   └── file_parser.py               # 扩展：PDF 和图片解析
│
├── configs/deep_research/tools/
│   └── Search.tool.yaml             # 扩展：semantic_scholar 选项
│
├── configs/markdown_report_writer/tools/
│   └── DetectUserChanges.tool.yaml  # 新增：工具配置
│
└── quick_start.py                   # 扩展：反馈循环和文件处理
```

### 关键修改

| 文件 | 修改内容 | 目的 |
|------|---------|------|
| `search.py` | 添加 `semantic_scholar` 搜索源 | 学术搜索支持 |
| `semantic_scholar_search.py` | 新增 | Semantic Scholar API 集成 |
| `file_parser.py` | 添加 PDF 和图片解析 | 多格式输入支持 |
| `detect_user_changes.py` | 新增 | 变更检测与意图分析 |
| `quick_start.py` | 添加反馈循环 | 交互式修订 |
| `Search.tool.yaml` | 扩展模式 | 新搜索源选项 |

---

## 🧪 测试方法

### 测试 Semantic Scholar 搜索

```bash
cd NexDR
source .venv/bin/activate

python -c "
from nexdr.agents.deep_research.semantic_scholar_search import search_papers
result = search_papers('transformer attention', num_results=3)
if isinstance(result, list):
    print(f'✓ 搜索成功：{len(result)} 条结果')
    print(f'第一篇论文：{result[0][\"title\"]}')
"
```

### 测试变更检测

```bash
python -c "
from nexdr.agents.markdown_report_writer.detect_user_changes import detect_user_changes
import tempfile

# 创建测试文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f1:
    f1.write('# Report\n\n## Intro\n\nOriginal\n')
    original = f1.name

with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f2:
    f2.write('# Report\n\n## Intro\n\nModified\n\n## New\n\nAdded\n')
    modified = f2.name

result = detect_user_changes(original, modified, None)
data = result['data'] if isinstance(result, dict) and 'data' in result else result.data

print(f'✓ 变更检测成功：{data.get(\"has_changes\")}')
print(f'  变更摘要：{data.get(\"changes_summary\")}')
print(f'  意图：{data.get(\"intent\", {}).get(\"primary_intent\")}')
"
```

### 测试文件解析器

```bash
python -c "
from nexdr.agents.doc_reader.file_parser import FileParser
import asyncio

parser = FileParser()

# 测试 PDF
success, content, suffix = asyncio.run(parser.parse('test.pdf'))
print(f'PDF: success={success}, chars={len(content) if success else 0}')

# 测试图片
success, content, suffix = asyncio.run(parser.parse('test.png'))
print(f'图片：success={success}, chars={len(content) if success else 0}')
"
```

---

## 📝 实现细节

### 任务一：Semantic Scholar 替代搜索

**修改/新增的文件**：
- `nexdr/agents/deep_research/semantic_scholar_search.py`（新增，508 行）
- `nexdr/agents/deep_research/search.py`（修改）
- `configs/deep_research/tools/Search.tool.yaml`（修改）

**核心功能**：
- 完整的 Semantic Scholar API 实现
- 支持论文搜索、引用分析、参考文献获取
- 年份过滤、多种排序方式
- 重试机制和错误处理

### 任务二：Markdown 反馈循环

**修改/新增的文件**：
- `nexdr/agents/markdown_report_writer/detect_user_changes.py`（新增，400 行）
- `nexdr/agents/markdown_report_writer/__init__.py`（新增）
- `configs/markdown_report_writer/tools/DetectUserChanges.tool.yaml`（新增）
- `quick_start.py`（修改）

**核心功能**：
- 基于 difflib 的变更检测
- Markdown 章节提取
- 意图分析算法
- 交互式修订循环
- 过程文件自动清理

### 任务三：多格式输入

**修改的文件**：
- `nexdr/agents/doc_reader/file_parser.py`（扩展）
- `quick_start.py`（修改）

**核心功能**：
- 使用 pypdf 解析 PDF
- 使用多模态 LLM 生成图片描述
- 使用 pytesseract 进行 OCR 降级处理
- 自动文件类型检测
- 内容提取和存储

---

## 🔍 常见问题

### "SERPER_API_KEY environment variable is required"

**解决方案**：在 `.env` 中配置，或改用 Semantic Scholar：
```bash
# 在查询中指定学术搜索
python quick_start.py --query="搜索关于...的学术论文"
```

### PDF 解析失败

**解决方案**：
```bash
# 安装 pypdf
pip install pypdf

# 对于扫描版 PDF，还需安装 OCR
pip install pdf2image pytesseract
brew install tesseract poppler  # macOS
```

### 图片解析失败

**解决方案**：
1. 配置多模态 LLM（推荐）：
```bash
MULTI_MODAL_LLM_API_KEY=sk-xxx
MULTI_MODAL_LLM_BASE_URL=https://api.openai.com/v1
MULTI_MODAL_LLM_MODEL=gpt-4-vision-preview
```

2. 或使用 OCR（免费但功能有限）：
```bash
pip install pytesseract Pillow
brew install tesseract  # macOS
```

### 反馈循环检测不到变更

**解决方案**：确保你编辑的是 `markdown_report.md`（不是 `.original.md` 或 `.user.md` 文件）。系统会自动对比这些文件。

### Agent 调用工具而不是生成报告

**解决方案**：最新版本已修复此问题。反馈消息现在明确指示 Agent 不要调用工具。如果仍然发生，尝试减少 `--max_iterations`。

---

## 📚 额外资源

- [原始 NexDR 仓库](https://github.com/nex-agi/NexDR)
- [Semantic Scholar API 文档](https://api.semanticscholar.org/api-docs/)
- [NexAU 框架文档](https://github.com/nex-agi/nexau)
- [pypdf 文档](https://pypdf.readthedocs.io/)
- [pytesseract 文档](https://pypi.org/project/pytesseract/)

---

## 🎓 学术用途

此修改版本特别适用于：

- **文献综述** - Semantic Scholar 集成用于学术论文发现
- **迭代写作** - 反馈循环用于协作式报告完善
- **多源研究** - 在一次工作流中结合 PDF、图片和网络搜索
- **可重复研究** - 所有引用和来源在 `citations.json` 中追踪

---

## 📄 许可证

Apache License 2.0 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- 原始 NexDR 项目，由 Nex-AGI 开发
- Semantic Scholar API 提供学术搜索
- NexAU 智能体框架
- 所有开源贡献者

---

<div align="center">

**⭐ 如果你觉得这个修改版本有用，请考虑给个星标！ ⭐**

</div>
