# Best Current Practices in Prompt & Context Engineering

**Agentic Systems, Affective Prompting, and MCP/Hooks/Skills Across ChatGPT, Claude, and Self-Hosted Stacks**

---

## Welcome

This book provides a comprehensive, rigorous treatment of prompt engineering, context engineering, and agentic system design for modern large language models (LLMs). Whether you're building production AI applications, conducting research, or deploying LLM infrastructure, this book offers evidence-based guidance grounded in peer-reviewed research and reproducible experiments.

## Who This Book Is For

- **AI Engineers** building production LLM applications
- **Researchers** exploring prompt optimization and agentic systems
- **ML Product Teams** designing user-facing AI features
- **SRE/Platform Engineers** deploying and scaling LLM infrastructure

## What Makes This Book Different

### Evidence-Based
Every technique is supported by empirical results from peer-reviewed research. No anecdotes or speculation—only validated approaches with quantified performance gains.

### 🔬 Reproducible
All code examples are end-to-end runnable with pinned dependencies, fixed seeds, and one-command builds. Every experiment in this book can be reproduced on your machine.

### 🔒 Security-First
Integrated OWASP LLM Top 10 mitigations throughout. Each pattern includes security considerations, failure modes, and red-team test cases.

### 🎯 Platform-Agnostic
Covers self-hosted models (vLLM, llama.cpp, Ollama), ChatGPT (Custom GPTs, Actions), and Claude (Skills, MCP, Hooks) with abstract principles that apply across platforms.

### 📐 Structured Methodology
Every technique follows a consistent pattern:
**Problem → Theory → Pattern → Implementation → Evaluation → Pitfalls → Checklist**

## Book Contents

### Part I: Foundations

#### [Chapter 1: Foundations of Prompt & Context Engineering](ch01-foundations.md)
- Core concepts: prompts, messages, tools, structured outputs
- Chain-of-Thought (CoT): +15-40% on reasoning tasks
- Self-Consistency: +10-17% with N=5-10 samples
- Tree-of-Thoughts: +300% on creative search tasks
- Reflexion: +20% on code generation
- **Labs**: CoT comparison, ToT search, Reflexion iteration

#### [Chapter 2: Affective Prompting & Persona Conditioning](ch02-affective-prompting.md)
- Empirical results: +5-13% performance, -6% truthfulness
- Sycophancy problem: larger models = more sycophancy
- Persona conditioning: benefits and risks
- Ethical considerations and governance frameworks
- **Labs**: Sentiment analysis, red-team evaluation, anti-sycophancy

#### Chapter 3: Context Engineering for Long Inputs & RAG
- Context window management and position effects
- HyDE: Hypothetical Document Embeddings
- RAPTOR: Recursive Abstractive Processing
- Self-RAG: Retrieval with self-reflection
- **Labs**: HyDE baseline, RAPTOR indexing, Self-RAG

### Part II: Platform-Specific Patterns

#### Chapter 4: Self-Hosted Models
- vLLM: High-throughput inference with PagedAttention
- llama.cpp: CPU and edge deployment
- Ollama & LM Studio: Local development
- Quantization and optimization strategies

#### Chapter 5: ChatGPT Custom GPTs & Actions
- Custom GPT design patterns
- Actions: RESTful API integration
- OAuth and authentication
- Marketplace deployment

#### Chapter 6: Claude Skills, MCP & Hooks
- Claude Skills development
- Model Context Protocol (MCP)
- Pre/post-generation hooks
- Computer use and tool orchestration

### Part III: Advanced Topics

#### Chapter 7: Agentic Systems & Orchestration
- Agent architectures: ReAct, Reflexion, AutoGPT
- Multi-agent coordination
- Planning and tool use
- Human-in-the-loop patterns

#### Chapter 8: Security & OWASP LLM Top 10
- LLM01: Prompt Injection
- LLM02: Insecure Output Handling
- LLM03: Training Data Poisoning
- LLM04-10: Complete mitigation guide
- Red-team frameworks

#### Chapter 9: Observability & Evaluation
- Metrics: accuracy, faithfulness, groundedness
- LLM-as-a-judge evaluation
- Tracing and monitoring (LangSmith, OpenTelemetry)
- A/B testing frameworks

#### Chapter 10: Production Best Practices
- Deployment architectures
- Cost optimization strategies
- Latency and throughput tuning
- Incident response
- Governance and compliance

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/llm-ebook.git
cd llm-ebook

# Install dependencies
make install

# Activate virtual environment
source .venv/bin/activate
```

### Build the Book

```bash
# Build all formats (PDF, EPUB, web)
make all

# View web version
make serve  # Opens at http://localhost:8000
```

### Run Labs

```bash
# Test all labs
make labs

# Run specific chapter
cd labs/ch01-foundations
pytest -v
```

## Key Features

### Pattern Cards

Every technique includes a structured pattern card:

| Component | Description |
|-----------|-------------|
| **Intent** | What problem does this solve? |
| **When It Helps** | Appropriate use cases |
| **Mechanics** | How it works |
| **Minimal Prompt** | Concrete example |
| **Variants** | Alternative approaches |
| **Failure Modes** | Common pitfalls |
| **Security Notes** | OWASP considerations |
| **Test Cases** | Validation approach |

### Empirical Results

All performance claims are quantified:

| Technique | Benchmark | Baseline | Improvement | Citation |
|-----------|-----------|----------|-------------|----------|
| Chain-of-Thought | GSM8K | 17.9% | +39.2pp | Wei et al. 2022 |
| Self-Consistency | GSM8K | 57.1% | +17.3pp | Wang et al. 2023 |
| Tree-of-Thoughts | Game of 24 | 7.3% | +66.7pp | Yao et al. 2023 |
| Reflexion | HumanEval | 67.0% | +21.0pp | Shinn et al. 2023 |

### Security Integration

Every pattern includes OWASP LLM Top 10 considerations:

- **LLM01 (Prompt Injection)**: Input validation strategies
- **LLM02 (Insecure Output)**: Output encoding and sanitization
- **LLM07 (Insecure Plugin)**: Sandboxing and permissions
- **LLM08 (Excessive Agency)**: Human-in-loop controls

## Writing Style

This book uses **PhD-level technical writing**:
- Neutral and precise tone
- Numbered IEEE-style citations
- Reproducible code with exact versions
- Statistical rigor (t-tests, confidence intervals)
- No marketing hype or unsupported claims

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

**Areas where we need help:**
- Additional benchmark implementations
- Platform-specific examples
- Translations
- Bug fixes and improvements

## License

This work is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

**You are free to:**
- Share and adapt the material
- Use for educational purposes

**Under the following terms:**
- Attribution required
- Non-commercial use only
- Share derivatives under same license

## Citation

```bibtex
@book{llm_prompt_engineering_2025,
  title={Best Current Practices in Prompt \& Context Engineering},
  author={AI Engineering Research Team},
  year={2025},
  publisher={Self-published},
  url={https://github.com/yourusername/llm-ebook}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/llm-ebook/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/llm-ebook/discussions)

## Acknowledgments

This work builds on research from the broader AI community. See the bibliography in each chapter for specific citations.

---

**Ready to get started?** Jump to [Chapter 1: Foundations](ch01-foundations.md) or explore the [labs](../labs/).

**Current Version**: 1.0.0 | **Last Updated**: 2025-01-10 | [Changelog](../CHANGELOG.md)
