# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-10

### Added
- **Chapter 1: Foundations of Prompt & Context Engineering**
  - Core definitions (prompts, messages, structured outputs, tools)
  - Empirical evidence for CoT, Self-Consistency, ToT, Reflexion
  - Evaluation harnesses and ablation methodologies
  - Pattern cards for each technique
  - Runnable labs with tests:
    - CoT vs direct prompting comparison
    - Tree-of-Thoughts search
    - Reflexion self-critique

- **Chapter 2: Affective Prompting & Persona Conditioning**
  - Empirical results on affective prompts
  - Persona conditioning patterns and risks
  - Sycophancy measurement and mitigation
  - Ethical considerations and governance framework
  - Safe-use patterns by risk level
  - Red-team evaluation templates

- **Build System**
  - Makefile for PDF, EPUB, and web builds
  - MkDocs configuration for web version
  - Pandoc configuration for PDF/EPUB
  - IEEE CSL citation style

- **Templates**
  - Chain-of-Thought pattern library (YAML)
  - Prompt evaluation harness (Python)

- **Documentation**
  - Comprehensive README with quick start
  - Reproducibility guide (REPRO.md)
  - Project structure and conventions

- **Infrastructure**
  - requirements.txt with pinned dependencies
  - .gitignore for Python, build artifacts, secrets
  - Testing framework with pytest
  - Bibliography (book.bib) with IEEE-style citations

### Security
- Integrated OWASP LLM Top 10 considerations throughout
- Prompt injection mitigations in pattern cards
- Security notes for all major techniques
- Red-team evaluation frameworks

### Technical Details
- Python 3.8+ support
- Type hints and docstrings
- Unit tests for all lab examples
- Mock implementations for reproducibility
- Statistical evaluation with confidence intervals

## [Unreleased]

### Planned for Future Releases

#### Chapters
- **Chapter 3**: Context Engineering for Long Inputs & RAG
  - HyDE, RAPTOR, Self-RAG implementations
  - Context window management strategies
- **Chapter 4**: Self-Hosted Models (vLLM, llama.cpp, Ollama)
- **Chapter 5**: ChatGPT Custom GPTs & Actions
- **Chapter 6**: Claude Skills, MCP & Hooks
- **Chapter 7**: Agentic Systems & Orchestration
- **Chapter 8**: Security & OWASP LLM Top 10
- **Chapter 9**: Observability & Evaluation
- **Chapter 10**: Production Best Practices

#### Features
- Complete figure generation scripts (SVG)
- Interactive web demos for key concepts
- Video tutorials for complex topics
- Multi-language support (code examples)
- Advanced RAG evaluation harnesses
- Production monitoring templates

#### Infrastructure
- Automated build pipeline (CI/CD)
- PDF/EPUB generation testing
- Link checking automation
- Citation validation scripts
- Automated security scanning

---

## Version History

### Version Numbering
- **Major version** (X.0.0): New chapters or significant restructuring
- **Minor version** (0.X.0): New sections, labs, or substantial updates
- **Patch version** (0.0.X): Bug fixes, typos, minor clarifications

### Release Schedule
- Monthly minor releases with new content
- Weekly patch releases for fixes and improvements
- Quarterly major releases with complete chapters

---

**Current Version**: 1.0.0
**Last Updated**: 2025-01-10
**Status**: Active Development
