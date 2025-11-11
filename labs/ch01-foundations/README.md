# Chapter 1 Labs: Foundations of Prompt & Context Engineering

This directory contains runnable code examples for Chapter 1 concepts.

## Labs Overview

### 1. Chain-of-Thought vs Direct Prompting (`cot_vs_direct.py`)

Compares direct prompting against Chain-of-Thought prompting on mathematical reasoning tasks.

**Run:**
```bash
python cot_vs_direct.py --n_samples 10 --n_trials 5
```

**Key Features:**
- Statistical comparison with t-tests
- Multiple trial runs for confidence intervals
- GSM8K-style math problems
- Extractors for numeric answers

**Expected Output:**
```
Chain-of-Thought vs Direct Prompting Comparison
============================================================
Model: gpt-4
Examples: 10
Trials: 5

Results:
------------------------------------------------------------
Direct Prompting:  45.0% ± 5.0%
CoT Prompting:     78.0% ± 4.2%

Improvement:       +33.0%
T-statistic:       4.123
P-value:           0.0143
Significant:       True
============================================================
```

### 2. Tree-of-Thoughts Search (`tot_search.py`)

Implements Tree-of-Thoughts (ToT) search for the Game of 24 puzzle.

**Run:**
```bash
python tot_search.py --numbers 4 6 8 9 --breadth 5 --depth 4
```

**Key Features:**
- Beam search with configurable breadth
- Thought evaluation heuristics
- Search trace visualization
- Solution verification

**Example Solution:**
```
Solution found!
------------------------------------------------------------
Step 1: 8 - 4 = 4
Step 2: 4 * 6 = 24
Step 3: Final result: 24

Verification: Yes Valid
```

### 3. Reflexion Self-Critique (`reflexion_example.py`)

Demonstrates iterative code improvement through self-reflection.

**Run:**
```bash
python reflexion_example.py --task fibonacci --max_iterations 3
```

**Key Features:**
- Generate → Test → Reflect → Refine loop
- Execution feedback integration
- Cycle detection
- Performance measurement

**Expected Iterations:**
```
Iteration 0: Naive recursion (fails on large inputs)
Iteration 1: Reflection identifies exponential complexity
Iteration 2: Improved with memoization (passes all tests)
```

## Running Tests

All labs include unit tests:

```bash
# Run all tests
pytest -v

# Run specific test file
pytest test_cot_comparison.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Mock vs Production Mode

**Current Implementation:**
- Labs use **mock LLM responses** for reproducibility and testing
- No API keys required to run examples

**Production Mode:**
To use real LLM APIs, replace the `generate()` function:

```python
# Replace mock implementation with real API
from openai import OpenAI

def generate(prompt: str, model: str = "gpt-4", **kwargs) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **kwargs
    )
    return response.choices[0].message.content
```

**Set API Keys:**
```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"  # For Claude examples
```

## Dependencies

See `requirements.txt` in project root:

```bash
pip install -r ../../requirements.txt
```

**Key Libraries:**
- `numpy`: Statistical computations
- `scipy`: Statistical tests (t-test, confidence intervals)
- `pytest`: Unit testing

## Expected Runtime

**With Mock Responses:**
- CoT Comparison: ~1 second
- ToT Search: ~2 seconds
- Reflexion: ~5 seconds (includes code execution)

**With Real APIs:**
- CoT Comparison: 2-5 minutes (API latency)
- ToT Search: 5-10 minutes (multiple API calls)
- Reflexion: 3-7 minutes (iterative refinement)

## Reproducibility

All labs use fixed random seeds for reproducibility:

```bash
# Default seed is 42
python cot_vs_direct.py --seed 42

# Different seed for variation
python cot_vs_direct.py --seed 123
```

## Troubleshooting

**Import Errors:**
```
ModuleNotFoundError: No module named 'numpy'
```
**Solution:** Install dependencies: `pip install -r ../../requirements.txt`

**API Rate Limits:**
```
openai.error.RateLimitError: Rate limit exceeded
```
**Solution:** Labs include mock mode by default. For production, implement retry logic with exponential backoff.

**Execution Timeouts:**
```
Reflexion: Execution timed out (>5s)
```
**Solution:** Expected for inefficient code (e.g., naive recursion). The reflexion loop should fix this in subsequent iterations.

## Extensions

Ideas for extending these labs:

1. **CoT Comparison:**
   - Add few-shot examples
   - Compare different reasoning prompts
   - Test on different benchmarks (MATH, StrategyQA)

2. **ToT Search:**
   - Implement DFS variant
   - Add more sophisticated evaluation (LLM-based)
   - Test on other puzzles (crosswords, planning)

3. **Reflexion:**
   - Add static analysis tools (mypy, bandit)
   - Implement external feedback (human-in-loop)
   - Test on HumanEval benchmark

## References

See Chapter 1 for detailed citations and theoretical background.

**Key Papers:**
- Wei et al. (2022): Chain-of-Thought Prompting
- Wang et al. (2023): Self-Consistency
- Yao et al. (2023): Tree of Thoughts
- Shinn et al. (2023): Reflexion

---

For questions or issues, see main project [README](../../README.md).
