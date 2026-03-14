# NexDR (Nex Deep Research) - Modified Version

<div align="center">

**NexDR** is an advanced deep research agent built on the [Nex-N1](https://huggingface.co/nex-agi/DeepSeek-V3.1-Nex-N1) agentic model and the [NexAU](https://github.com/nex-agi/nexau) agent framework. It autonomously decomposes research tasks, conducts parallel investigations, and generates structured research reports.

**This is a modified version** with enhanced capabilities:
- 📚 **Academic Search** - Semantic Scholar API integration for scholarly research
- 🔄 **Interactive Feedback Loop** - Revise reports through natural user-Agent collaboration
- 📎 **Multi-Format Input** - Support for PDF, images, and various document types

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

</div>

---

## 🆕 What's New in This Version

### 1. Semantic Scholar Academic Search 🔬

Added Semantic Scholar API as an alternative search source for academic research:

- **Scholarly Focus**: Search peer-reviewed papers with citation metrics
- **Advanced Filtering**: Filter by year, sort by citations/influence/publication date
- **Rich Metadata**: Authors, abstracts, venues, citation counts, references
- **Free Tier**: 100 requests/day without API key

```python
# Agent automatically chooses appropriate search source
# Or specify in your query: "Search academic papers about transformer models"
```

**Implementation**: `nexdr/agents/deep_research/semantic_scholar_search.py`

---

### 2. Interactive Markdown Feedback Loop 🔄

Generate reports iteratively with user collaboration:

- **User Edits**: Modify the generated markdown report
- **Auto Detection**: System detects what you changed (sections added/modified/deleted)
- **Intent Analysis**: Agent understands your editing intent
- **Smart Revision**: Agent continues improving based on your changes
- **No Overwrite**: Your modifications are always preserved

```bash
# Enable feedback loop
python quick_start.py \
  --query "AI in healthcare" \
  --report_format markdown \
  --use_feedback_loop \
  --max_iterations=3
```

**Workflow**:
```
Agent generates draft → You edit → Agent detects changes → 
Agent understands intent → Agent revises → Repeat until satisfied
```

**Implementation**: 
- `nexdr/agents/markdown_report_writer/detect_user_changes.py`
- `nexdr/agents/markdown_report_writer/detect_user_changes.py::infer_user_intent()`

---

### 3. Multi-Format Input Support 📎

Process various input formats alongside your research query:

- **PDF Documents** - Extract text using pypdf
- **Images** - Generate captions with multi-modal LLM or OCR
- **Text Files** - .txt, .md, .csv, .json, .yaml, etc.
- **Automatic Processing** - All files parsed and incorporated into research

```bash
# Process PDFs, images, and text files
python quick_start.py \
  --query "Summarize these research papers" \
  --report_format markdown \
  --input_files paper1.pdf paper2.pdf chart.png notes.md
```

**Implementation**: `nexdr/agents/doc_reader/file_parser.py` (extended)

---

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- pip or uv package manager

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/Bamboovan/deep-researcher.git
cd deep-researcher

# Install with uv
uv sync
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/Bamboovan/deep-researcher.git
cd deep-researcher

# Install dependencies
pip install -e .

# Optional: Additional format support
pip install pypdf        # PDF parsing
pip install pytesseract  # Image OCR
pip install Pillow       # Image processing
```

### Environment Setup

Create a `.env` file in the project root:

```bash
# Required for LLM capabilities
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# Required for web search
SERPER_API_KEY=your_serper_api_key

# Optional: Semantic Scholar (free tier available)
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# Optional: For document parsing (choose at least one)
JINA_API_KEY=your_jina_api_key
DOC_READER_PROVIDERS=jina,serper

# Optional: For multi-modal image captioning
MULTI_MODAL_LLM_API_KEY=sk-xxxxx
MULTI_MODAL_LLM_BASE_URL=https://api.openai.com/v1
MULTI_MODAL_LLM_MODEL=gpt-4-vision-preview

# Optional: For Langfuse tracing
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Get API Keys**:
- Serper API: https://serper.dev/ (100 free requests/month)
- Semantic Scholar: https://www.semanticscholar.org/product/api (100 free requests/day)
- OpenAI: https://platform.openai.com/api-keys

---

## 🚀 Quick Start

### Basic Usage

Run a research task and generate a markdown report:

```bash
python quick_start.py \
  --query "What are the latest developments in quantum computing?" \
  --report_format markdown \
  --output_dir workspaces/my_research
```

### With Interactive Feedback Loop ⭐

```bash
python quick_start.py \
  --query "AI applications in finance" \
  --report_format markdown \
  --use_feedback_loop \
  --max_iterations=3 \
  --output_dir workspaces/finance_research
```

**Interactive Process**:
1. Agent generates initial report
2. You edit `markdown_report.md` with your preferred editor
3. Press Enter in terminal
4. System detects your changes and analyzes intent
5. Agent revises based on your modifications
6. Repeat until you type `done`

### With Input Files 📎

```bash
python quick_start.py \
  --query "Summarize the key findings from these papers" \
  --report_format markdown \
  --input_files paper1.pdf paper2.pdf data.csv \
  --output_dir workspaces/paper_review
```

### Academic Research Mode 🔬

```bash
python quick_start.py \
  --query "Survey on large language model reasoning capabilities" \
  --report_format markdown \
  --use_feedback_loop \
  --output_dir workspaces/llm_survey
```

The Agent will prefer Semantic Scholar for academic queries.

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--query` | Research question (required) | - |
| `--report_format` | Output format: `markdown`, `html`, `markdown+html` | `markdown` |
| `--output_dir` | Directory to save results | `workspaces/workspace_TIMESTAMP` |
| `--use_feedback_loop` | Enable interactive revision mode | `False` |
| `--max_iterations` | Maximum feedback iterations | `3` |
| `--input_files` | Input files to process (PDF, images, etc.) | `None` |

---

## 📊 Output Structure

After running a research task:

```
workspaces/my_research/
├── logs_TIMESTAMP.log           # Detailed execution logs
├── markdown_report.md           # Final research report
├── citations.json               # Citation references
├── final_state.json            # Execution metadata and statistics
├── *.extracted.txt             # Extracted text from input files
└── (process files cleaned up)   # Temporary files auto-deleted
```

**With Feedback Loop**:
- Process files (`markdown_report.original.md`, `markdown_report.user.md`) are automatically deleted after completion
- Only the final `markdown_report.md` is kept

---

## 🔧 Advanced Features

### 1. Change Detection & Intent Analysis

The system automatically detects and analyzes your modifications:

**Detected Changes**:
- Added sections (new content you wrote)
- Modified sections (content you edited)
- Deleted sections (content you removed)
- Line-level diff statistics

**Intent Analysis**:
- Identifies if you're adding conclusions, methodology, or general content
- Recognizes refinements to introduction or existing sections
- Understands simplification (deletions)
- Provides suggestions to the Agent for appropriate follow-up

**Example Output**:
```
✓ Changes detected:
  +50 lines added; -20 lines deleted; 2 new section(s)
  Added sections: Ethics Considerations, Future Outlook
  Modified sections: Introduction, Diagnostic Applications

Intent Analysis:
  - User added conclusion/outlook sections
  - User modified introduction to adjust focus
  - Please preserve all user modifications
```

### 2. Multi-Format File Parsing

**Supported Formats**:

| Type | Extensions | Method |
|------|------------|--------|
| Text | .txt, .md, .py, .json, .csv, .yaml, .html | Direct read |
| PDF | .pdf | pypdf extraction |
| Images | .jpg, .png, .gif, .bmp, .webp | Multi-modal LLM captioning or OCR |

**Image Processing Strategy**:
1. **Primary**: Multi-modal LLM generates detailed caption
2. **Fallback**: OCR extracts visible text
3. **Graceful degradation**: Works even without API keys (with reduced capability)

### 3. Academic Search Capabilities

**Semantic Scholar Features**:
- Search by keyword with academic focus
- Filter by publication year range
- Sort by relevance, citation count, publication date, or influence
- Retrieve: title, abstract, authors, venue, citations, references, PDF links

**Example Query**:
```
"Find recent papers on graph neural networks for fraud detection (2023-2025)"
```

Agent will:
- Use Semantic Scholar API
- Filter by year 2023-2025
- Sort by citation count
- Extract key findings and methodologies

---

## 🎯 Use Cases

### 1. Academic Literature Review

```bash
python quick_start.py \
  --query "Survey on transformer architectures in NLP" \
  --report_format markdown \
  --use_feedback_loop \
  --input_files related_papers.pdf \
  --output_dir workspaces/lit_review
```

### 2. Market Research with Data Analysis

```bash
python quick_start.py \
  --query "Analyze the EV market trends and competitive landscape" \
  --report_format markdown \
  --use_feedback_loop \
  --input_files market_data.csv competitor_analysis.pdf \
  --output_dir workspaces/ev_market
```

### 3. Technical Documentation from Papers

```bash
python quick_start.py \
  --query "Explain the methodology and results from these papers" \
  --report_format markdown \
  --input_files paper1.pdf paper2.pdf architecture.png \
  --output_dir workspaces/tech_doc
```

### 4. Iterative Report Refinement

```bash
# Start research
python quick_start.py \
  --query "Climate change impact on agriculture" \
  --report_format markdown \
  --use_feedback_loop \
  --max_iterations=5

# Then:
# 1. Edit report to add regional focus
# 2. Agent detects and expands on your additions
# 3. Edit again to refine conclusions
# 4. Agent polishes and adds supporting evidence
# 5. Type 'done' when satisfied
```

---

## 🏗️ Architecture

### Modified Components

```
NexDR (Modified)
├── nexdr/agents/deep_research/
│   ├── search.py                    # Extended with semantic_scholar source
│   ├── semantic_scholar_search.py   # NEW: Academic search implementation
│   ├── web_search.py                # Original web search
│   └── arxiv_search.py              # Original arxiv search
│
├── nexdr/agents/markdown_report_writer/
│   ├── detect_user_changes.py       # NEW: Change detection & intent analysis
│   └── __init__.py                  # NEW: Module initialization
│
├── nexdr/agents/doc_reader/
│   └── file_parser.py               # Extended: PDF & image parsing
│
├── configs/deep_research/tools/
│   └── Search.tool.yaml             # Extended: semantic_scholar option
│
├── configs/markdown_report_writer/tools/
│   └── DetectUserChanges.tool.yaml  # NEW: Tool configuration
│
└── quick_start.py                   # Extended: Feedback loop & file processing
```

### Key Modifications

| File | Change | Purpose |
|------|--------|---------|
| `search.py` | Added `semantic_scholar` source | Academic search support |
| `semantic_scholar_search.py` | NEW | Semantic Scholar API integration |
| `file_parser.py` | Added PDF & image parsing | Multi-format input |
| `detect_user_changes.py` | NEW | Change detection & intent analysis |
| `quick_start.py` | Added feedback loop | Interactive revision |
| `Search.tool.yaml` | Extended schema | New search source options |

---

## 🧪 Testing

### Test Semantic Scholar Search

```bash
cd NexDR
source .venv/bin/activate

python -c "
from nexdr.agents.deep_research.semantic_scholar_search import search_papers
result = search_papers('transformer attention', num_results=3)
if isinstance(result, list):
    print(f'✓ Search successful: {len(result)} results')
    print(f'First paper: {result[0][\"title\"]}')
"
```

### Test Change Detection

```bash
python -c "
from nexdr.agents.markdown_report_writer.detect_user_changes import detect_user_changes
import tempfile

# Create test files
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f1:
    f1.write('# Report\n\n## Intro\n\nOriginal\n')
    original = f1.name

with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f2:
    f2.write('# Report\n\n## Intro\n\nModified\n\n## New\n\nAdded\n')
    modified = f2.name

result = detect_user_changes(original, modified, None)
data = result['data'] if isinstance(result, dict) and 'data' in result else result.data

print(f'✓ Changes detected: {data.get(\"has_changes\")}')
print(f'  Summary: {data.get(\"changes_summary\")}')
print(f'  Intent: {data.get(\"intent\", {}).get(\"primary_intent\")}')
"
```

### Test File Parser

```bash
python -c "
from nexdr.agents.doc_reader.file_parser import FileParser
import asyncio

parser = FileParser()

# Test PDF
success, content, suffix = asyncio.run(parser.parse('test.pdf'))
print(f'PDF: success={success}, chars={len(content) if success else 0}')

# Test image
success, content, suffix = asyncio.run(parser.parse('test.png'))
print(f'Image: success={success}, chars={len(content) if success else 0}')
"
```

---

## 📝 Implementation Details

### Task 1: Semantic Scholar Alternative

**Files Modified/Created**:
- `nexdr/agents/deep_research/semantic_scholar_search.py` (NEW, 508 lines)
- `nexdr/agents/deep_research/search.py` (modified)
- `configs/deep_research/tools/Search.tool.yaml` (modified)

**Key Features**:
- Full Semantic Scholar API implementation
- Support for paper search, citations, references
- Year filtering, multiple sort options
- Retry mechanism and error handling

### Task 2: Markdown Feedback Loop

**Files Modified/Created**:
- `nexdr/agents/markdown_report_writer/detect_user_changes.py` (NEW, 400 lines)
- `nexdr/agents/markdown_report_writer/__init__.py` (NEW)
- `configs/markdown_report_writer/tools/DetectUserChanges.tool.yaml` (NEW)
- `quick_start.py` (modified)

**Key Features**:
- difflib-based change detection
- Markdown section extraction
- Intent analysis algorithm
- Interactive revision loop
- Auto-cleanup of process files

### Task 3: Multi-Format Input

**Files Modified**:
- `nexdr/agents/doc_reader/file_parser.py` (extended)
- `quick_start.py` (modified)

**Key Features**:
- PDF parsing with pypdf
- Image captioning with multi-modal LLM
- OCR fallback with pytesseract
- Automatic file type detection
- Content extraction and storage

---

## 🔍 Troubleshooting

### "SERPER_API_KEY environment variable is required"

**Solution**: Configure in `.env` or use Semantic Scholar instead:
```bash
# In your query, specify academic search
python quick_start.py --query="Search academic papers about..."
```

### PDF parsing fails

**Solution**:
```bash
# Install pypdf
pip install pypdf

# For scanned PDFs, also install OCR
pip install pdf2image pytesseract
brew install tesseract poppler  # macOS
```

### Image parsing fails

**Solution**:
1. Configure multi-modal LLM (recommended):
```bash
MULTI_MODAL_LLM_API_KEY=sk-xxx
MULTI_MODAL_LLM_BASE_URL=https://api.openai.com/v1
MULTI_MODAL_LLM_MODEL=gpt-4-vision-preview
```

2. Or use OCR (free but limited):
```bash
pip install pytesseract Pillow
brew install tesseract  # macOS
```

### Feedback loop doesn't detect changes

**Solution**: Make sure you're editing `markdown_report.md` (not the `.original.md` or `.user.md` files). The system compares these automatically.

### Agent calls tools instead of generating report

**Solution**: This was fixed in the latest version. The feedback message now explicitly instructs the Agent not to call tools. If it still happens, try reducing `--max_iterations`.

---

## 📚 Additional Resources

- [Original NexDR Repository](https://github.com/nex-agi/NexDR)
- [Semantic Scholar API Documentation](https://api.semanticscholar.org/api-docs/)
- [NexAU Framework Documentation](https://github.com/nex-agi/nexau)
- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [pytesseract Documentation](https://pypi.org/project/pytesseract/)

---

## 🎓 Academic Use

This modified version is particularly suitable for:

- **Literature Reviews**: Semantic Scholar integration for academic paper discovery
- **Iterative Writing**: Feedback loop for collaborative report refinement
- **Multi-Source Research**: Combine PDFs, images, and web search in one workflow
- **Reproducible Research**: All citations and sources tracked in `citations.json`

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Original NexDR project by Nex-AGI
- Semantic Scholar API for academic search
- NexAU agent framework
- All open-source contributors

---

<div align="center">

**⭐ If you find this modified version useful, please consider giving it a star! ⭐**

</div>
