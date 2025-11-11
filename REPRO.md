# Reproducibility Guide

This document provides detailed instructions for reproducing all results, figures, and examples in the book "Best Current Practices in Prompt & Context Engineering."

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Building the Book](#building-the-book)
3. [Running Lab Examples](#running-lab-examples)
4. [Regenerating Figures](#regenerating-figures)
5. [Validation & Testing](#validation--testing)
6. [Troubleshooting](#troubleshooting)

## Environment Setup

### System Requirements

**Minimum Requirements:**
- OS: Linux (Ubuntu 20.04+) or macOS (11.0+)
- Python: 3.8 or higher
- RAM: 8 GB minimum, 16 GB recommended
- Disk Space: 5 GB for dependencies and build artifacts

**Required System Packages:**

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    python3.8 \
    python3-pip \
    python3-venv \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    git \
    curl
```

#### macOS (with Homebrew)

```bash
brew update
brew install python@3.8 pandoc
brew install --cask mactex-no-gui  # Or mactex for full TeX distribution
```

### Python Environment

**Step 1: Clone Repository**

```bash
git clone https://github.com/yourusername/llm-ebook.git
cd llm-ebook
```

**Step 2: Create Virtual Environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows (not officially supported)
```

**Step 3: Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Verify Installation:**

```bash
python --version  # Should be 3.8 or higher
pip list | grep -E "mkdocs|pytest|langchain"
pandoc --version  # Should be 2.0 or higher
```

### API Keys (for Lab Examples)

Some labs require API keys. Create a `.env` file in the project root:

```bash
# .env file (DO NOT commit this file)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Note**: Labs are designed to work with mock responses when API keys are not provided, but real API keys enable full functionality.

## Building the Book

### Build All Formats

```bash
make all
```

This command:
1. Generates PDF: `output/prompt-engineering-book.pdf`
2. Generates EPUB: `output/prompt-engineering-book.epub`
3. Builds web version: `site/index.html`

### Build Individual Formats

**PDF Only:**

```bash
make pdf
```

Output: `output/prompt-engineering-book.pdf`

**EPUB Only:**

```bash
make epub
```

Output: `output/prompt-engineering-book.epub`

**Web Version Only:**

```bash
make web
```

Output: `site/index.html`

**Serve Web Version Locally:**

```bash
make serve
```

Access at: `http://localhost:8000`

### Expected Build Times

- PDF: ~30 seconds
- EPUB: ~20 seconds
- Web: ~10 seconds

(Times on a standard laptop with Intel i5/M1 processor)

## Running Lab Examples

### Test All Labs

```bash
make labs
```

This runs pytest on all lab examples with verbose output.

### Test Specific Chapter

**Chapter 1: Foundations**

```bash
cd labs/ch01-foundations
pytest -v
```

Expected tests:
- `test_cot_comparison.py`: CoT vs. direct prompting
- `test_tot_search.py`: Tree-of-Thoughts breadth variations
- `test_reflexion.py`: Self-critique and refinement

**Chapter 2: Affective Prompting**

```bash
cd labs/ch02-affective-prompting
pytest -v
```

Expected tests:
- `test_sentiment_prompts.py`: Emotional conditioning effects
- `test_red_team.py`: Safety and sycophancy checks
- `test_persona_conditioning.py`: Persona-based variations

**Chapter 3: Context Engineering**

```bash
cd labs/ch03-context-engineering
pytest -v
```

Expected tests:
- `test_hyde.py`: Hypothetical Document Embeddings
- `test_raptor.py`: Recursive Abstractive Processing
- `test_self_rag.py`: Self-Reflective RAG

### Run with Coverage

```bash
make test
```

Generates coverage report in `htmlcov/index.html`

### Individual Lab Execution

Each lab can be run standalone:

```bash
cd labs/ch01-foundations
python cot_vs_direct.py --seed 42 --model gpt-4 --task gsm8k
```

**Common Parameters:**
- `--seed`: Random seed for reproducibility (default: 42)
- `--model`: Model to use (default: gpt-4)
- `--task`: Benchmark task (varies by lab)
- `--output`: Output file for results (default: stdout)

## Regenerating Figures

All figures are generated from code and data in `labs/`.

### Generate All Figures

```bash
cd labs/figures
python generate_all_figures.py
```

Output: SVG files in `figures/`

### Generate Specific Figures

**Chapter 1 Figures:**

```bash
cd labs/ch01-foundations
python generate_cot_comparison_chart.py --output ../../figures/ch01-cot-comparison.svg
python generate_tot_tree_diagram.py --output ../../figures/ch01-tot-tree.svg
```

**Chapter 2 Figures:**

```bash
cd labs/ch02-affective-prompting
python generate_sentiment_heatmap.py --output ../../figures/ch02-sentiment-heatmap.svg
```

**Chapter 3 Figures:**

```bash
cd labs/ch03-context-engineering
python generate_rag_pipeline.py --output ../../figures/ch03-rag-pipeline.svg
```

### Expected Figures

Each chapter should produce:
- Pipeline diagrams (SVG)
- Performance comparison charts (SVG)
- Architecture diagrams (SVG)

## Validation & Testing

### Validate Citations

```bash
make validate
```

This checks:
- All citations in Markdown reference entries in `book/book.bib`
- All BibTeX entries are well-formed
- No broken internal links

### Check Code Quality

```bash
make lint
```

Runs:
- `flake8`: PEP 8 style checking
- `mypy`: Type checking
- `black --check`: Code formatting

### Run Security Scans

```bash
bandit -r labs/ tests/
safety check
```

## Troubleshooting

### Common Issues

**1. Pandoc Not Found**

```
Error: pandoc: command not found
```

**Solution**: Install pandoc (see [System Requirements](#system-requirements))

**2. LaTeX Errors During PDF Generation**

```
Error: LaTeX Error: File 'unicode-math.sty' not found
```

**Solution**: Install complete TeX distribution:

```bash
# Ubuntu/Debian
sudo apt-get install texlive-full

# macOS
brew install --cask mactex
```

**3. Import Errors in Labs**

```
ModuleNotFoundError: No module named 'langchain'
```

**Solution**: Ensure virtual environment is activated and dependencies are installed:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**4. API Rate Limits**

```
openai.error.RateLimitError: Rate limit exceeded
```

**Solution**: Labs include retry logic with exponential backoff. Wait a few seconds and retry, or use mock mode:

```bash
python cot_vs_direct.py --mock-responses
```

**5. Out of Memory During Vector Operations**

```
numpy.core._exceptions.MemoryError
```

**Solution**: Reduce batch size or chunk size:

```bash
python test_raptor.py --chunk-size 512 --batch-size 16
```

### Verifying Reproducibility

To verify exact reproducibility of results:

**1. Set Environment Variables**

```bash
export PYTHONHASHSEED=42
export CUBLAS_WORKSPACE_CONFIG=:4096:8  # For CUDA determinism (if using GPU)
```

**2. Run Lab with Fixed Seed**

```bash
python labs/ch01-foundations/cot_vs_direct.py --seed 42 --deterministic
```

**3. Compare Output Hashes**

```bash
# Generate reference hash
python cot_vs_direct.py --seed 42 | sha256sum > expected_hash.txt

# Verify later
python cot_vs_direct.py --seed 42 | sha256sum -c expected_hash.txt
```

### Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/yourusername/llm-ebook/issues)
2. Review error logs in `LOGS/`
3. Open a new issue with:
   - OS and version
   - Python version
   - Error message and full traceback
   - Steps to reproduce

## Performance Benchmarks

Expected execution times on reference hardware:

**Reference System:**
- CPU: Intel i5-12400 / Apple M1
- RAM: 16 GB
- SSD: NVMe

**Lab Execution Times:**

| Lab | Expected Duration | Notes |
|-----|------------------|-------|
| CoT Comparison | 2-5 min | Depends on API latency |
| ToT Search | 5-10 min | Tree breadth affects time |
| Reflexion | 3-7 min | Multiple refinement rounds |
| HyDE RAG | 1-3 min | Vector operations |
| RAPTOR Indexing | 5-15 min | Hierarchical clustering |
| Self-RAG | 3-8 min | Reflection tokens |

**Build Times:**

| Build Target | Expected Duration |
|--------------|------------------|
| PDF | 30-60 sec |
| EPUB | 20-40 sec |
| Web | 10-20 sec |
| All formats | 60-120 sec |

## Data Provenance

All datasets used in labs:

| Dataset | Source | License | Version |
|---------|--------|---------|---------|
| GSM8K | [OpenAI](https://github.com/openai/grade-school-math) | MIT | v1.0 |
| HotpotQA | [Stanford](https://hotpotqa.github.io/) | CC BY-SA 4.0 | v1.0 |
| MMLU | [Hendrycks et al.](https://github.com/hendrycks/test) | MIT | 2020 |
| TruthfulQA | [Lin et al.](https://github.com/sylinrl/TruthfulQA) | Apache 2.0 | v1.0 |

Datasets are automatically downloaded to `data/` on first run and cached.

## Reproducibility Checklist

- [ ] System packages installed (pandoc, TeX)
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] API keys configured (if needed)
- [ ] All builds complete successfully
- [ ] All labs pass tests
- [ ] Figures generated correctly
- [ ] Citations validated
- [ ] Code quality checks pass

## Version Information

**Document Version**: 1.0.0
**Last Updated**: 2025-11-11
**Tested On**:
- Ubuntu 22.04 LTS
- macOS 13 (Ventura)
- Python 3.8, 3.9, 3.10, 3.11

---

For questions or issues, please open an issue on GitHub or contact the maintainers.
