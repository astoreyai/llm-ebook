# Chapter 1: Foundations of Prompt & Context Engineering

## Abstract

This chapter establishes the theoretical and empirical foundations of prompt engineering and context engineering for large language models (LLMs). We define core concepts including prompts, system messages, user messages, tools/functions, and structured outputs. We survey empirical evidence for reasoning-enhanced prompting techniques including Chain-of-Thought (CoT), Self-Consistency, Tree-of-Thoughts (ToT), and Reflexion. Finally, we introduce evaluation harnesses and ablation methodologies for rigorous prompt optimization. All claims are supported by peer-reviewed research and reproducible experiments.

**Learning Objectives:**
- Understand fundamental prompt engineering terminology and components
- Evaluate empirical evidence for reasoning prompts
- Design and execute ablation studies for prompt optimization
- Apply evaluation harnesses to quantify prompt effectiveness

## 1.1 Core Definitions

### 1.1.1 What is a Prompt?

A **prompt** is the input text provided to a language model to elicit a desired output. In modern LLM systems, prompts are structured into distinct message types with specific roles [1].

**Formal Definition:**

$$P = \{m_1, m_2, ..., m_n\}$$

where each message $m_i = (role_i, content_i)$ and $role_i \in \{\text{system}, \text{user}, \text{assistant}, \text{tool}\}$

**Message Types:**

1. **System Messages**: Define the model's behavior, constraints, and persona
   - Highest priority in instruction hierarchy
   - Set global context and behavioral guidelines
   - Example: `"You are a Python expert who writes secure, tested code."`

2. **User Messages**: Represent end-user input
   - Task specification and queries
   - Contextual information
   - Example: `"Write a function to compute Fibonacci numbers."`

3. **Assistant Messages**: Model's previous responses
   - Used in multi-turn conversations
   - Provide conversation history
   - Example: `"Here's a recursive Fibonacci implementation..."`

4. **Tool/Function Messages**: Results from function calls
   - Available in systems with tool use (ChatGPT, Claude)
   - Return values from external function execution
   - Example: `{"result": 42, "units": "ms"}`

### 1.1.2 Structured Outputs

Modern LLM APIs support **structured output** modes that constrain generation to valid JSON schemas, enabling reliable integration with downstream systems [2].

**Implementation Patterns:**

```python
# OpenAI Structured Outputs
from openai import OpenAI
from pydantic import BaseModel

class FibonacciResult(BaseModel):
    sequence: list[int]
    computation_time_ms: float
    method: str

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Generate first 10 Fibonacci numbers"}],
    response_format={"type": "json_schema", "json_schema": FibonacciResult.schema()}
)
```

**Benefits:**
- Type safety and validation
- Eliminates parsing errors
- Enables strong API contracts
- Reduces hallucinated or malformed outputs

**Security Note (OWASP LLM01)**: Structured outputs mitigate prompt injection by enforcing output schemas. Always validate structured outputs against expected types before executing commands or queries.

### 1.1.3 Tools and Function Calling

**Function calling** enables LLMs to invoke external tools, APIs, and databases, extending capabilities beyond text generation [3].

**Mechanism:**

1. Declare available functions with JSON schemas
2. Model generates function call specifications
3. Application executes function
4. Result returned as tool message
5. Model incorporates result into response

**Example Pattern:**

```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {"type": "string", "description": "City and state, e.g., 'San Francisco, CA'"},
      "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
  }
}
```

**Security Note (OWASP LLM07)**: Implement strict sandboxing for function execution. Never allow the model direct database write access or system command execution without human approval.

## 1.2 Reasoning-Enhanced Prompting: Empirical Evidence

### 1.2.1 Chain-of-Thought (CoT) Prompting

**Problem**: Standard prompting fails on multi-step reasoning tasks.

**Theory**: Decomposing reasoning into explicit intermediate steps improves accuracy on complex tasks [4].

**Pattern Card: Chain-of-Thought**

| Component | Details |
|-----------|---------|
| **Intent** | Elicit step-by-step reasoning for complex problems |
| **When It Helps** | Math, logic, multi-hop reasoning, planning |
| **Mechanics** | Prompt model to "think step by step" or provide example reasoning chains |
| **Minimal Prompt** | `"Let's think step by step."` appended to query |
| **Variants** | Zero-shot CoT, Few-shot CoT, Manual CoT |
| **Failure Modes** | Verbose outputs, increased latency, reasoning errors |
| **Security Notes** | CoT can expose reasoning that reveals system prompts (LLM01) |
| **Test Cases** | GSM8K, MATH, StrategyQA, HotpotQA |

**Empirical Results:**

Wei et al. [4] demonstrated CoT improvements across multiple benchmarks:

| Benchmark | Direct Prompting | CoT Prompting | Improvement |
|-----------|-----------------|---------------|-------------|
| GSM8K | 17.9% | 57.1% | +39.2pp |
| MATH | 4.4% | 7.7% | +3.3pp |
| StrategyQA | 54.3% | 70.1% | +15.8pp |

**Minimal Prompt Example:**

```
# Zero-Shot CoT
Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
   Each can has 3 tennis balls. How many tennis balls does he have now?

A: Let's think step by step.
```

**Few-Shot CoT Example:**

```
Q: Janet's ducks lay 16 eggs per day. She eats three for breakfast and
   bakes muffins with four. She sells the remainder for $2 per egg.
   How much does she make daily?

A: Let's think step by step.
   - Total eggs: 16
   - Eggs eaten: 3
   - Eggs for muffins: 4
   - Eggs sold: 16 - 3 - 4 = 9
   - Daily income: 9 × $2 = $18

Q: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
   Each can has 3 tennis balls. How many tennis balls does he have now?

A: Let's think step by step.
```

**When CoT Fails:**

1. **Simple Tasks**: Overhead without benefit
2. **Constrained Outputs**: Conflicts with brevity requirements
3. **Factual Recall**: No reasoning decomposition needed
4. **Cost Sensitivity**: Increases token usage 2-5×

### 1.2.2 Self-Consistency

**Problem**: Single CoT reasoning paths can contain errors.

**Theory**: Sample multiple reasoning paths and select the most consistent answer via majority vote [5].

**Pattern Card: Self-Consistency**

| Component | Details |
|-----------|---------|
| **Intent** | Improve reasoning reliability through multiple samples |
| **When It Helps** | High-stakes decisions, arithmetic, ambiguous problems |
| **Mechanics** | Generate N reasoning paths with temperature > 0, aggregate answers |
| **Minimal Prompt** | Standard CoT + temperature=0.7, N=5-40 samples |
| **Variants** | Weighted voting, confidence-based selection |
| **Failure Modes** | High cost (N× API calls), slower inference |
| **Security Notes** | Mitigates adversarial perturbations (improves robustness) |
| **Test Cases** | GSM8K, StrategyQA, SVAMP, AQuA |

**Algorithm:**

```python
def self_consistency(question: str, model: str, n_samples: int = 10) -> str:
    """Self-Consistency decoding with majority vote."""
    reasoning_paths = []
    answers = []

    for _ in range(n_samples):
        response = generate(
            prompt=f"{question}\n\nLet's think step by step.",
            model=model,
            temperature=0.7  # Enable sampling diversity
        )
        reasoning_paths.append(response)
        answer = extract_final_answer(response)
        answers.append(answer)

    # Majority vote
    most_common_answer = mode(answers)
    return most_common_answer
```

**Empirical Results:**

Wang et al. [5] showed significant improvements over CoT alone:

| Benchmark | CoT (Greedy) | Self-Consistency (N=40) | Improvement |
|-----------|--------------|------------------------|-------------|
| GSM8K | 57.1% | 74.4% | +17.3pp |
| SVAMP | 69.9% | 80.7% | +10.8pp |
| AQuA | 35.7% | 41.5% | +5.8pp |

**Cost-Accuracy Trade-off:**

- N=5: 80% of improvement at 12.5% cost
- N=10: 90% of improvement at 25% cost
- N=40: 100% improvement at 100% cost (baseline)

**Practical Guideline**: Use N=5-10 for production; reserve N=40 for research benchmarks.

### 1.2.3 Tree-of-Thoughts (ToT)

**Problem**: Linear CoT cannot explore multiple reasoning branches.

**Theory**: Frame reasoning as search over a thought tree, using deliberate exploration (BFS/DFS) and evaluation [6].

**Pattern Card: Tree-of-Thoughts**

| Component | Details |
|-----------|---------|
| **Intent** | Explore multiple reasoning paths with backtracking |
| **When It Helps** | Ambiguous problems, creative tasks, planning, search |
| **Mechanics** | Generate thought branches, evaluate, prune, continue promising paths |
| **Minimal Prompt** | "Generate 3 different approaches..." + evaluation |
| **Variants** | BFS-ToT, DFS-ToT, beam search |
| **Failure Modes** | Exponential complexity, high cost |
| **Security Notes** | Exploration can trigger unintended behaviors (test thoroughly) |
| **Test Cases** | Game of 24, Creative Writing, Crosswords |

**Architecture:**

```
                    [Initial Problem]
                           |
         /-----------------+-----------------\
        /                  |                  \
   [Thought 1]        [Thought 2]        [Thought 3]
       |                   |                   |
   [Evaluate]          [Evaluate]          [Evaluate]
       |                   X (pruned)          |
   [Expand]                                [Expand]
     /   \                                  /   \
[T1.1] [T1.2]                          [T3.1] [T3.2]
```

**Implementation Sketch:**

```python
def tree_of_thoughts(problem: str, depth: int = 3, breadth: int = 3) -> str:
    """Tree-of-Thoughts search with BFS."""
    candidates = [{"thought": problem, "path": [], "value": 0.0}]

    for level in range(depth):
        next_candidates = []

        for candidate in candidates:
            # Generate breadth new thoughts
            thoughts = generate_thoughts(candidate["thought"], n=breadth)

            for thought in thoughts:
                # Evaluate thought quality
                value = evaluate_thought(thought, problem)

                next_candidates.append({
                    "thought": thought,
                    "path": candidate["path"] + [thought],
                    "value": value
                })

        # Keep top-k candidates (beam search)
        candidates = sorted(next_candidates, key=lambda x: x["value"], reverse=True)[:breadth]

    return candidates[0]["path"]
```

**Empirical Results:**

Yao et al. [6] demonstrated improvements on creative and search tasks:

| Task | Input-Output Prompting | CoT | ToT (b=5) |
|------|----------------------|-----|-----------|
| Game of 24 | 7.3% | 4.0% | 74.0% |
| Creative Writing (coherence) | 6.19 | 6.93 | 7.56 |
| Crosswords (words solved) | 38.7% | 40.6% | 60.0% |

**Hyperparameter Guidance:**

- **Breadth (b)**: 3-5 for production, 10+ for research
- **Depth (d)**: Problem-dependent; 2-4 typical
- **Evaluation**: Simple heuristics or separate LLM calls

**When to Use ToT:**

[YES] Open-ended problems with multiple valid approaches
[YES] Tasks requiring backtracking (e.g., constraint satisfaction)
[YES] Creative generation with quality filters

[NO] Simple factual queries
[NO] Cost-constrained applications
[NO] Real-time latency requirements

### 1.2.4 Reflexion: Self-Reflective Iteration

**Problem**: Single-pass generation lacks error correction.

**Theory**: Enable models to critique their outputs and iteratively refine them [7].

**Pattern Card: Reflexion**

| Component | Details |
|-----------|---------|
| **Intent** | Improve outputs through self-critique and refinement |
| **When It Helps** | Code generation, reasoning tasks, content editing |
| **Mechanics** | Generate → Evaluate → Reflect → Refine (iterate) |
| **Minimal Prompt** | "Critique your previous answer and improve it." |
| **Variants** | Single-turn reflection, multi-turn iteration, external feedback |
| **Failure Modes** | Infinite loops, degradation, confirmation bias |
| **Security Notes** | Reflection can expose system instructions (LLM01) |
| **Test Cases** | HumanEval, MBPP, ALFWorld |

**Reflexion Loop:**

```python
def reflexion(problem: str, max_iterations: int = 3) -> str:
    """Reflexion: iterative self-refinement."""
    solution = generate_initial_solution(problem)

    for iteration in range(max_iterations):
        # Evaluate current solution
        eval_result = evaluate_solution(solution, problem)

        if eval_result["correct"]:
            return solution  # Success

        # Generate reflection
        reflection_prompt = f"""
        Problem: {problem}
        Your previous solution: {solution}
        Evaluation: {eval_result['feedback']}

        Reflect on what went wrong and how to improve.
        """
        reflection = generate(reflection_prompt)

        # Refine solution based on reflection
        refinement_prompt = f"""
        Problem: {problem}
        Previous solution: {solution}
        Reflection: {reflection}

        Generate an improved solution.
        """
        solution = generate(refinement_prompt)

    return solution
```

**Empirical Results:**

Shinn et al. [7] demonstrated improvements on programming and decision-making tasks:

| Task | GPT-4 (Direct) | GPT-4 + Reflexion |
|------|----------------|------------------|
| HumanEval | 67.0% | 88.0% |
| MBPP | 70.0% | 85.0% |
| ALFWorld | 18.0% | 74.0% |

**Best Practices:**

1. **Limit Iterations**: 2-4 typically sufficient; diminishing returns after
2. **Early Stopping**: Terminate if evaluation shows improvement
3. **Diverse Feedback**: Combine execution results, static analysis, LLM critique
4. **Prevent Loops**: Track seen solutions; abort if cycling

**Failure Mode Example:**

```
Iteration 1: "Use bubble sort"
Reflection: "Bubble sort is O(n²), inefficient"
Iteration 2: "Use quicksort"
Reflection: "Quicksort is O(n²) worst-case"
Iteration 3: "Use bubble sort"  ← Cycle detected!
```

**Mitigation**: Hash solutions; abort if duplicate found.

## 1.3 Evaluation Harnesses and Ablation Studies

### 1.3.1 Designing Rigorous Prompt Evaluations

**Principle**: Prompt engineering must be evidence-based. Intuition and anecdotes are insufficient for production systems.

**Evaluation Framework:**

1. **Benchmark Selection**: Representative tasks with ground truth
2. **Metrics**: Task-appropriate (accuracy, F1, ROUGE, human eval)
3. **Statistical Significance**: Multiple runs, confidence intervals
4. **Ablation Studies**: Isolate impact of each prompt component
5. **Generalization Testing**: Evaluate on held-out data

**Example Evaluation Harness:**

```python
from typing import List, Dict, Callable
import numpy as np
from scipy import stats

class PromptEvaluationHarness:
    """Rigorous prompt evaluation with statistical testing."""

    def __init__(
        self,
        benchmark: str,
        metric_fn: Callable,
        n_runs: int = 5,
        confidence_level: float = 0.95
    ):
        self.benchmark = benchmark
        self.metric_fn = metric_fn
        self.n_runs = n_runs
        self.confidence_level = confidence_level

    def evaluate_prompt(
        self,
        prompt_template: str,
        test_cases: List[Dict],
        model: str = "gpt-4"
    ) -> Dict:
        """Evaluate prompt with multiple runs and statistical analysis."""
        all_scores = []

        for run in range(self.n_runs):
            run_scores = []
            for test_case in test_cases:
                # Generate response
                prompt = prompt_template.format(**test_case["input"])
                response = generate(prompt, model=model, seed=42+run)

                # Compute metric
                score = self.metric_fn(response, test_case["expected"])
                run_scores.append(score)

            all_scores.append(np.mean(run_scores))

        # Statistical analysis
        mean_score = np.mean(all_scores)
        std_score = np.std(all_scores)
        ci = stats.t.interval(
            self.confidence_level,
            len(all_scores) - 1,
            loc=mean_score,
            scale=stats.sem(all_scores)
        )

        return {
            "mean": mean_score,
            "std": std_score,
            "ci_lower": ci[0],
            "ci_upper": ci[1],
            "runs": all_scores
        }

    def compare_prompts(
        self,
        prompt_a: str,
        prompt_b: str,
        test_cases: List[Dict]
    ) -> Dict:
        """Statistical comparison of two prompts."""
        results_a = self.evaluate_prompt(prompt_a, test_cases)
        results_b = self.evaluate_prompt(prompt_b, test_cases)

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(results_a["runs"], results_b["runs"])

        return {
            "prompt_a": results_a,
            "prompt_b": results_b,
            "t_statistic": t_stat,
            "p_value": p_value,
            "significant": p_value < (1 - self.confidence_level),
            "winner": "A" if results_a["mean"] > results_b["mean"] else "B"
        }
```

### 1.3.2 Ablation Study Methodology

**Ablation studies** isolate the contribution of individual prompt components.

**Standard Protocol:**

1. **Baseline**: Minimal prompt without enhancements
2. **Component Ablations**: Remove one component at a time
3. **Additive Analysis**: Add components incrementally
4. **Interaction Effects**: Test component combinations

**Example Ablation:**

| Prompt Configuration | Accuracy | Δ from Baseline |
|---------------------|----------|----------------|
| Baseline (minimal) | 45.2% | - |
| + "Think step by step" | 62.8% | +17.6pp |
| + Few-shot examples | 58.1% | +12.9pp |
| + System message | 48.9% | +3.7pp |
| + All components | 71.3% | +26.1pp |

**Interpretation**: CoT contributes most; combining all components yields synergistic improvements.

**Implementation Pattern:**

```python
def ablation_study(
    baseline_prompt: str,
    components: Dict[str, str],
    test_cases: List[Dict]
) -> pd.DataFrame:
    """Run ablation study across prompt components."""
    results = []

    # Baseline
    baseline_score = evaluate(baseline_prompt, test_cases)
    results.append({"config": "baseline", "score": baseline_score})

    # Single component additions
    for name, component in components.items():
        prompt = baseline_prompt + "\n" + component
        score = evaluate(prompt, test_cases)
        results.append({
            "config": f"baseline + {name}",
            "score": score,
            "delta": score - baseline_score
        })

    # Full combination
    full_prompt = baseline_prompt + "\n" + "\n".join(components.values())
    full_score = evaluate(full_prompt, test_cases)
    results.append({
        "config": "full",
        "score": full_score,
        "delta": full_score - baseline_score
    })

    return pd.DataFrame(results)
```

### 1.3.3 Common Benchmarks

| Benchmark | Task Type | Metrics | Size | Citation |
|-----------|-----------|---------|------|----------|
| GSM8K | Math reasoning | Accuracy | 8.5K | [4] |
| MATH | Advanced math | Accuracy | 12.5K | [8] |
| HumanEval | Code generation | pass@k | 164 | [9] |
| MMLU | Multi-domain QA | Accuracy | 15.9K | [10] |
| TruthfulQA | Truthfulness | % truthful | 817 | [11] |
| HotpotQA | Multi-hop reasoning | F1, EM | 113K | [12] |

## 1.4 Practical Guidelines and Checklists

### 1.4.1 When to Use Each Technique

**Decision Tree:**

```
Is the task simple factual recall?
├─ Yes → Direct prompting
└─ No
   └─ Is multi-step reasoning required?
      ├─ Yes
      │  └─ Is single reasoning path sufficient?
      │     ├─ Yes → Chain-of-Thought
      │     └─ No
      │        └─ Is cost a concern?
      │           ├─ Yes → CoT + Self-Consistency (N=5)
      │           └─ No → Tree-of-Thoughts or Self-Consistency (N=40)
      └─ No
         └─ Is output quality critical?
            ├─ Yes → Reflexion
            └─ No → Direct prompting with structured output
```

### 1.4.2 Prompt Engineering Checklist

**Pre-Development:**
- [ ] Define clear success metrics and benchmarks
- [ ] Identify representative test cases
- [ ] Establish baseline performance
- [ ] Set cost and latency budgets

**Development:**
- [ ] Start with minimal prompt
- [ ] Add components incrementally
- [ ] Run ablation studies for each addition
- [ ] Test on diverse inputs
- [ ] Validate structured output schemas
- [ ] Implement security mitigations (see Chapter 8)

**Evaluation:**
- [ ] Multiple runs (N ≥ 5) for statistical validity
- [ ] Report confidence intervals
- [ ] Compare against baselines with significance tests
- [ ] Test generalization on held-out data
- [ ] Measure cost and latency

**Production:**
- [ ] Implement monitoring and logging
- [ ] A/B test prompt variants
- [ ] Set up automated regression testing
- [ ] Document prompt versioning
- [ ] Establish incident response for failures

### 1.4.3 Anti-Patterns to Avoid

[NO] **Premature Optimization**: Adding complexity without measurement
[NO] **Anecdotal Evidence**: Trusting single examples over systematic evaluation
[NO] **Overfitting**: Optimizing too heavily for specific test cases
[NO] **Ignoring Cost**: Deploying expensive techniques without ROI analysis
[NO] **Version Neglect**: Failing to track prompt versions and changes
[NO] **Security Blindness**: Not testing for prompt injection and adversarial inputs

## 1.5 Summary and Key Takeaways

**Core Principles:**

1. **Structured Communication**: Use system/user/assistant/tool messages appropriately
2. **Evidence-Based**: Ground decisions in empirical results, not intuition
3. **Systematic Evaluation**: Employ rigorous benchmarks, metrics, and ablations
4. **Reasoning Enhancement**: Apply CoT, Self-Consistency, ToT, Reflexion when task complexity warrants
5. **Cost-Awareness**: Balance performance gains against computational costs

**Empirical Findings:**

- Chain-of-Thought improves multi-step reasoning by 15-40 percentage points [4]
- Self-Consistency with N=5-10 captures most benefits at reduced cost [5]
- Tree-of-Thoughts excels on open-ended and search tasks [6]
- Reflexion enables iterative refinement for code and planning [7]

**Next Steps:**

Chapter 2 examines affective and persona prompting, including benefits, risks, and ethical considerations. Chapter 3 covers context engineering for long inputs and RAG systems.

## References

[1] OpenAI. (2024). "Chat Completions API." OpenAI Documentation. https://platform.openai.com/docs/guides/chat

[2] OpenAI. (2024). "Structured Outputs." OpenAI Documentation. https://platform.openai.com/docs/guides/structured-outputs

[3] Anthropic. (2024). "Tool Use (Function Calling)." Anthropic Documentation. https://docs.anthropic.com/claude/docs/tool-use

[4] Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS 2022*.

[5] Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., & Zhou, D. (2023). "Self-Consistency Improves Chain of Thought Reasoning in Language Models." *ICLR 2023*.

[6] Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T., Cao, Y., & Narasimhan, K. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models." *NeurIPS 2023*.

[7] Shinn, N., Cassano, F., Labash, B., Gopinath, A., Narasimhan, K., & Yao, S. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." *NeurIPS 2023*.

[8] Hendrycks, D., Burns, C., Kadavath, S., Arora, A., Basart, S., Tang, E., Song, D., & Steinhardt, J. (2021). "Measuring Mathematical Problem Solving With the MATH Dataset." *NeurIPS 2021*.

[9] Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. de O., Kaplan, J., Edwards, H., Burda, Y., Joseph, N., Brockman, G., Ray, A., Puri, R., Krueger, G., Petrov, M., Khlaaf, H., Sastry, G., Mishkin, P., Chan, B., Gray, S., ... Zaremba, W. (2021). "Evaluating Large Language Models Trained on Code." *arXiv:2107.03374*.

[10] Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., & Steinhardt, J. (2021). "Measuring Massive Multitask Language Understanding." *ICLR 2021*.

[11] Lin, S., Hilton, J., & Evans, O. (2022). "TruthfulQA: Measuring How Models Mimic Human Falsehoods." *ACL 2022*.

[12] Yang, Z., Qi, P., Zhang, S., Bengio, Y., Cohen, W., Salakhutdinov, R., & Manning, C. D. (2018). "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering." *EMNLP 2018*.

---

**End of Chapter 1**

**Exercises:**

1. Implement CoT vs. direct prompting comparison on GSM8K (see `labs/ch01-foundations/`)
2. Run ablation study on your own prompt with ≥3 components
3. Conduct paired t-test comparing two prompt variants
4. Design Tree-of-Thoughts search for the Game of 24
5. Implement Reflexion loop with execution feedback for code generation
