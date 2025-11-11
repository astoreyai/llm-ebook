# Best Current Practices in Prompt & Context Engineering

**Agentic Systems, Affective Prompting, and MCP/Hooks/Skills Across ChatGPT, Claude, and Self-Hosted Stacks**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/astoreyai/llm-ebook)

## Overview

This book provides a rigorous, citation-driven treatment of prompt engineering, context engineering, and agentic system design for modern large language models. Designed for AI engineers, researchers, ML product teams, and SRE/Platform engineers, it covers best practices across three major deployment paradigms:

- **Self-Hosted Models**: vLLM, llama.cpp, Ollama, LM Studio
- **ChatGPT**: Custom GPTs, Actions, and API patterns
- **Claude**: Skills, Model Context Protocol (MCP), and Hooks

## Key Features

- **PhD-Level Technical Writing**: Rigorous, evidence-based content with IEEE-style citations
- **Reproducible Examples**: End-to-end runnable labs with pinned dependencies
- **Security-First**: Integrated OWASP LLM Top 10 mitigations throughout
- **Platform-Agnostic Patterns**: Abstract principles that apply across implementations
- **Comprehensive Coverage**: From foundations to production deployment
- **Multiple Formats**: PDF, EPUB, and searchable web version

## Target Audience

- **AI Engineers** building production LLM applications
- **Researchers** exploring prompt optimization and agentic systems
- **ML Product Teams** designing user-facing AI features
- **SRE/Platform Engineers** deploying and scaling LLM infrastructure

## Book Structure

### Part I: Foundations

1. **Foundations of Prompt & Context Engineering**
   - System vs. user messages, tools/functions, structured outputs
   - Evidence for reasoning prompts: CoT, Self-Consistency, Tree-of-Thoughts, Reflexion
   - Evaluation harnesses and ablation studies

2. **Affective Prompting & Persona Conditioning**
   - Empirical results on emotional/affective prompts
   - Trade-offs: truthfulness, sycophancy, toxicity risks
   - Safe-use patterns and governance checklists

3. **Context Engineering for Long Inputs & RAG**
   - Context window management and position effects
   - Advanced RAG: HyDE, RAPTOR indices, Self-RAG
   - Retrieval routing and hallucination testing

### Part II: Platform-Specific Patterns

4. **Self-Hosted Models** (vLLM, llama.cpp, Ollama)
5. **ChatGPT Custom GPTs & Actions**
6. **Claude Skills, MCP & Hooks**

### Part III: Advanced Topics

7. **Agentic Systems & Orchestration**
8. **Security & OWASP LLM Top 10**
9. **Observability & Evaluation**
10. **Production Best Practices**

## Quick Start

### Prerequisites

- **Operating System**: Linux or macOS
- **Python**: 3.8 or higher
- **System Packages**: `pandoc`, `texlive-xetex` (for PDF generation)

### Installation

```bash
# Clone the repository
git clone https://github.com/astoreyai/llm-ebook.git
cd llm-ebook

# Install dependencies
make install

# Activate the virtual environment
source .venv/bin/activate
```

### Building the Book

```bash
# Build all formats (PDF, EPUB, web)
make all

# Build specific formats
make pdf    # Create PDF version
make epub   # Create EPUB version
make web    # Build web version with MkDocs

# View web version locally
make serve  # Opens at http://localhost:8000
```

### Running Labs

```bash
# Test all lab examples
make labs

# Run specific chapter labs
cd labs/ch01-foundations
pytest test_cot_comparison.py -v

# Run with coverage
make test
```

## Project Structure

```
llm-ebook/
├── book/                   # Book chapters in Markdown
│   ├── ch01-foundations.md
│   ├── ch02-affective-prompting.md
│   ├── ch03-context-engineering.md
│   ├── ...
│   ├── book.bib           # IEEE-style bibliography
│   └── metadata.yaml      # Book metadata
├── figures/               # SVG diagrams and figures
├── labs/                  # Runnable code examples
│   ├── ch01-foundations/
│   │   ├── cot_vs_direct.py
│   │   ├── tot_search.py
│   │   └── reflexion_example.py
│   ├── ch02-affective-prompting/
│   └── ch03-context-engineering/
├── templates/             # Prompt patterns and configs
│   ├── patterns/          # JSON/YAML prompt patterns
│   └── evaluation/        # Evaluation harnesses
├── tests/                 # Unit tests
├── docs/                  # Additional documentation
├── Makefile              # Build automation
├── mkdocs.yml            # Web version configuration
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Writing Style & Pattern Cards

Each technical pattern follows a structured template:

- **Intent**: What problem does this solve?
- **When It Helps**: Appropriate use cases
- **Mechanics**: How it works
- **Minimal Prompt**: Concrete example
- **Variants**: Alternative approaches
- **Failure Modes**: Common pitfalls
- **Security Notes**: OWASP considerations
- **Test Cases**: Validation approach

## Development Guidelines

### Adding New Content

1. **Chapters**: Add Markdown files to `book/` following the naming convention `chNN-topic.md`
2. **Labs**: Create runnable Python files in `labs/chNN-topic/` with corresponding tests
3. **Figures**: Use SVG format in `figures/` for scalability
4. **Citations**: Add references to `book/book.bib` in BibTeX format

### Testing Changes

```bash
# Run tests
pytest tests/ -v

# Check code quality
make lint

# Validate citations and links
make validate
```

### Building Documentation

```bash
# Full rebuild
make clean && make all

# Quick iteration on web version
make serve  # Auto-reloads on changes
```

## Citation Format

This book uses IEEE citation style. All non-trivial claims are supported by:

- Peer-reviewed publications
- Official documentation
- Reproducible experiments in the labs

Example citation in text:
```markdown
Chain-of-Thought prompting improves reasoning performance on complex tasks [1].
```

Bibliography entry in `book/book.bib`:
```bibtex
@article{wei2022chain,
  title={Chain-of-thought prompting elicits reasoning in large language models},
  author={Wei, Jason and Wang, Xuezhi and others},
  journal={NeurIPS},
  year={2022}
}
```

## Security Considerations

All code examples integrate OWASP LLM Top 10 mitigations:

1. **LLM01: Prompt Injection** - Input validation and sanitization
2. **LLM02: Insecure Output Handling** - Output encoding
3. **LLM03: Training Data Poisoning** - Model provenance verification
4. **LLM04: Model Denial of Service** - Rate limiting and quotas
5. **LLM05: Supply Chain Vulnerabilities** - Dependency scanning
6. **LLM06: Sensitive Information Disclosure** - PII detection
7. **LLM07: Insecure Plugin Design** - Sandboxing and permissions
8. **LLM08: Excessive Agency** - Human-in-the-loop controls
9. **LLM09: Overreliance** - Confidence scoring and verification
10. **LLM10: Model Theft** - Access controls and monitoring

## Reproducibility

All labs are designed for reproducibility:

- **Pinned Dependencies**: `requirements.txt` with exact versions
- **Random Seeds**: Fixed seeds for deterministic results
- **Environment Specification**: OS, Python version, system packages
- **Data Provenance**: Clear sourcing for all datasets
- **One-Command Execution**: `make all` builds everything

See [REPRO.md](REPRO.md) for detailed reproduction instructions.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Follow the existing structure and style
4. Add tests for code examples
5. Update documentation
6. Submit a pull request

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

**You are free to:**
- Share — copy and redistribute the material
- Adapt — remix, transform, and build upon the material

**Under the following terms:**
- Attribution — Give appropriate credit
- NonCommercial — Not for commercial use
- ShareAlike — Distribute derivatives under the same license

## Citation

If you use this work in your research or projects, please cite:

```bibtex
@book{llm_prompt_engineering_2025,
  title={Best Current Practices in Prompt \& Context Engineering: Agentic Systems, Affective Prompting, and MCP/Hooks/Skills},
  author={AI Engineering Research Team},
  year={2025},
  publisher={Self-published},
  url={https://github.com/astoreyai/llm-ebook}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/astoreyai/llm-ebook/issues)
- **Discussions**: [GitHub Discussions](https://github.com/astoreyai/llm-ebook/discussions)

## Acknowledgments

This work builds on research from the broader AI community. See the bibliography in each chapter for specific citations.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Version**: 1.0.0
**Last Updated**: 2025-11-11
**Build Status**: ![Passing](https://img.shields.io/badge/build-passing-brightgreen.svg)
