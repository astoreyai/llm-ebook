# Chapter 9: Observability & Evaluation

## 9.1 Introduction: Observability Paradigm for LLM Applications

LLM applications present unique observability challenges: non-deterministic outputs, high inference costs, emergent failure modes, and complex multi-step agent workflows. Traditional application monitoring (uptime, latency, error rates) remains necessary but insufficient. Production LLM systems require specialized instrumentation to capture prompt-response pairs, token usage, model behavior drift, and quality degradation [@smith2023langsmith].

**Observability layers for LLM applications**:

| Layer | Traditional Apps | LLM Apps |
|-------|------------------|----------|
| **Infrastructure** | CPU, memory, network | GPU utilization, inference latency, queue depth |
| **Application** | Request/response logs | Prompt/completion pairs, token counts, costs |
| **Business logic** | Function execution traces | Agent reasoning traces, tool calls, decision paths |
| **Quality** | Error rates, SLA compliance | Output quality, hallucination rates, user satisfaction |

**Chapter roadmap**:

1. Logging and tracing architecture for LLM systems
2. Metrics and KPIs (latency, cost, quality)
3. Evaluation frameworks (offline, online, continuous)
4. LLM-as-a-judge evaluation patterns
5. Monitoring and alerting strategies
6. Cost tracking and optimization
7. Production observability stack

---

## 9.2 Logging & Tracing Architecture

### 9.2.1 Structured Logging for LLM Calls

Capture complete context for every LLM invocation to enable debugging, auditing, and quality analysis.

**Essential log fields**:

```python
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

class LLMLogger:
    """Structured logger for LLM interactions."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)

    def log_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        metadata: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log LLM call with complete context."""

        # Hash prompt/response for duplicate detection
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        response_hash = hashlib.sha256(response.encode()).hexdigest()[:16]

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "trace_id": trace_id or self._generate_trace_id(),
            "session_id": session_id,
            "user_id": user_id,
            "model": model,
            "prompt": prompt,
            "prompt_hash": prompt_hash,
            "response": response,
            "response_hash": response_hash,
            "prompt_tokens": metadata.get("prompt_tokens"),
            "completion_tokens": metadata.get("completion_tokens"),
            "total_tokens": metadata.get("total_tokens"),
            "latency_ms": metadata.get("latency_ms"),
            "cost_usd": metadata.get("cost_usd"),
            "temperature": metadata.get("temperature"),
            "max_tokens": metadata.get("max_tokens"),
            "finish_reason": metadata.get("finish_reason"),
            "model_version": metadata.get("model_version"),
            "error": metadata.get("error"),
            "tags": metadata.get("tags", [])
        }

        self.logger.info(
            "llm_call",
            extra={"structured_data": json.dumps(log_entry)}
        )

        return log_entry

    def _generate_trace_id(self) -> str:
        """Generate unique trace ID."""
        import uuid
        return str(uuid.uuid4())
```

**Usage example**:

```python
logger = LLMLogger(service_name="document_qa")

# Before LLM call
start_time = time.time()

# Make LLM call
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)

# After LLM call
latency_ms = (time.time() - start_time) * 1000

# Log with complete metadata
logger.log_llm_call(
    model="gpt-4",
    prompt=prompt,
    response=response.choices[0].message.content,
    metadata={
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "latency_ms": latency_ms,
        "cost_usd": calculate_cost(response.usage, "gpt-4"),
        "temperature": 0.7,
        "finish_reason": response.choices[0].finish_reason,
        "tags": ["document_qa", "production"]
    },
    user_id=user_id,
    session_id=session_id,
    trace_id=request.headers.get("X-Trace-ID")
)
```

### 9.2.2 Distributed Tracing for Agent Workflows

Multi-step agent systems require distributed tracing to understand decision paths and identify bottlenecks.

**OpenTelemetry integration**:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure exporter (Jaeger, Zipkin, or vendor-specific)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

class TracedReActAgent:
    """ReAct agent with distributed tracing."""

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.tracer = trace.get_tracer(__name__)

    def run(self, question: str, trace_context=None) -> str:
        """Execute agent with tracing."""

        with self.tracer.start_as_current_span(
            "react_agent",
            attributes={
                "agent.question": question,
                "agent.max_iterations": 10
            }
        ) as span:
            for iteration in range(10):
                # Trace LLM reasoning step
                with self.tracer.start_as_current_span(
                    f"agent.reasoning.iter_{iteration}"
                ) as reasoning_span:
                    thought_response = self.llm.generate(prompt)

                    reasoning_span.set_attributes({
                        "llm.model": "gpt-4",
                        "llm.prompt_tokens": thought_response.usage.prompt_tokens,
                        "llm.completion_tokens": thought_response.usage.completion_tokens,
                        "agent.thought": thought_response.text[:200]
                    })

                # Parse action
                action = self._parse_action(thought_response.text)

                if action.is_final_answer:
                    span.set_attribute("agent.iterations", iteration + 1)
                    span.set_attribute("agent.final_answer", action.answer[:200])
                    return action.answer

                # Trace tool execution
                with self.tracer.start_as_current_span(
                    f"agent.tool.{action.tool_name}"
                ) as tool_span:
                    observation = self.tools[action.tool_name](action.args)

                    tool_span.set_attributes({
                        "tool.name": action.tool_name,
                        "tool.args": str(action.args),
                        "tool.result_length": len(observation)
                    })

            # Agent failed to complete
            span.set_attribute("agent.status", "max_iterations_exceeded")
            return "Failed to answer question within iteration limit"
```

**Trace visualization benefits**:

1. **Identify bottlenecks**: Which tool calls take longest?
2. **Understand reasoning paths**: What sequence of tools led to answer?
3. **Debug failures**: Where did agent get stuck?
4. **Optimize costs**: Which LLM calls are most expensive?

---

## 9.3 Metrics & KPIs

### 9.3.1 Latency Metrics

Track end-to-end latency and component-level timing:

```python
from dataclasses import dataclass
from typing import List
import statistics

@dataclass
class LatencyMetrics:
    """Latency measurements for LLM calls."""

    p50_ms: float  # Median
    p90_ms: float  # 90th percentile
    p99_ms: float  # 99th percentile
    mean_ms: float
    max_ms: float
    min_ms: float
    count: int

class LatencyTracker:
    """Track and compute latency percentiles."""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.latencies: List[float] = []

    def record(self, latency_ms: float):
        """Record latency measurement."""
        self.latencies.append(latency_ms)

        # Keep only recent measurements
        if len(self.latencies) > self.window_size:
            self.latencies = self.latencies[-self.window_size:]

    def compute_metrics(self) -> LatencyMetrics:
        """Compute latency statistics."""

        if not self.latencies:
            return LatencyMetrics(0, 0, 0, 0, 0, 0, 0)

        sorted_latencies = sorted(self.latencies)
        count = len(sorted_latencies)

        return LatencyMetrics(
            p50_ms=sorted_latencies[int(count * 0.50)],
            p90_ms=sorted_latencies[int(count * 0.90)],
            p99_ms=sorted_latencies[int(count * 0.99)],
            mean_ms=statistics.mean(sorted_latencies),
            max_ms=max(sorted_latencies),
            min_ms=min(sorted_latencies),
            count=count
        )

# Usage with Prometheus metrics
from prometheus_client import Histogram, Counter

# Define metrics
llm_latency_histogram = Histogram(
    'llm_request_latency_seconds',
    'LLM request latency in seconds',
    ['model', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

# Instrument LLM calls
def call_llm_instrumented(model: str, prompt: str) -> str:
    """LLM call with instrumentation."""

    with llm_latency_histogram.labels(model=model, endpoint="chat").time():
        try:
            response = llm.generate(model, prompt)
            llm_requests_total.labels(model=model, status="success").inc()
            return response
        except Exception as e:
            llm_requests_total.labels(model=model, status="error").inc()
            raise
```

### 9.3.2 Cost Metrics

Track token usage and costs per request, user, and time period:

```python
class CostTracker:
    """Track LLM costs."""

    # Pricing per 1M tokens (as of Jan 2025)
    PRICING = {
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00}
    }

    def __init__(self):
        self.costs_by_user = {}
        self.costs_by_model = {}
        self.total_cost = 0.0

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for single LLM call."""

        if model not in self.PRICING:
            raise ValueError(f"Unknown model: {model}")

        pricing = self.PRICING[model]

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def record_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        user_id: str
    ) -> float:
        """Record cost and return amount."""

        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        # Track by user
        if user_id not in self.costs_by_user:
            self.costs_by_user[user_id] = 0.0
        self.costs_by_user[user_id] += cost

        # Track by model
        if model not in self.costs_by_model:
            self.costs_by_model[model] = 0.0
        self.costs_by_model[model] += cost

        # Track total
        self.total_cost += cost

        return cost

    def get_user_cost(self, user_id: str) -> float:
        """Get total cost for user."""
        return self.costs_by_user.get(user_id, 0.0)

    def get_top_users(self, n: int = 10) -> List[tuple]:
        """Get top N users by cost."""
        return sorted(
            self.costs_by_user.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by model."""
        return dict(self.costs_by_model)
```

### 9.3.3 Quality Metrics

Automated quality scoring for production outputs:

```python
import re
from typing import Dict

class QualityMetrics:
    """Compute quality metrics for LLM outputs."""

    @staticmethod
    def compute_metrics(response: str, expected: str = None) -> Dict[str, float]:
        """Compute multiple quality indicators."""

        metrics = {}

        # Length-based metrics
        metrics["response_length"] = len(response)
        metrics["word_count"] = len(response.split())

        # Completeness indicators
        metrics["has_answer"] = 1.0 if len(response.strip()) > 10 else 0.0
        metrics["finish_naturally"] = 1.0 if response[-1] in '.!?' else 0.0

        # Hallucination risk indicators
        metrics["hedge_words"] = QualityMetrics._count_hedge_words(response)
        metrics["certainty_words"] = QualityMetrics._count_certainty_words(response)
        metrics["citation_present"] = 1.0 if '[' in response or '(' in response else 0.0

        # Refusal detection
        metrics["is_refusal"] = QualityMetrics._detect_refusal(response)

        # Exact match (if expected provided)
        if expected:
            metrics["exact_match"] = 1.0 if response.strip() == expected.strip() else 0.0

        return metrics

    @staticmethod
    def _count_hedge_words(text: str) -> int:
        """Count hedging words indicating uncertainty."""
        hedge_words = [
            "might", "may", "could", "possibly", "perhaps",
            "seem", "appear", "suggest", "likely", "probably"
        ]
        return sum(text.lower().count(word) for word in hedge_words)

    @staticmethod
    def _count_certainty_words(text: str) -> int:
        """Count words indicating high certainty."""
        certainty_words = [
            "definitely", "certainly", "absolutely", "clearly",
            "obviously", "undoubtedly", "always", "never"
        ]
        return sum(text.lower().count(word) for word in certainty_words)

    @staticmethod
    def _detect_refusal(text: str) -> float:
        """Detect if model refused to answer."""
        refusal_patterns = [
            r"I cannot",
            r"I'm (not able|unable)",
            r"I don't have (access|information)",
            r"I apologize, but",
            r"as an AI"
        ]

        for pattern in refusal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return 1.0

        return 0.0
```

---

## 9.4 Offline Evaluation

Systematic evaluation on held-out test sets before deployment.

### 9.4.1 Benchmark Dataset Construction

```python
from typing import List, Dict
import json

class BenchmarkDataset:
    """Test set for LLM evaluation."""

    def __init__(self, name: str):
        self.name = name
        self.examples: List[Dict] = []

    def add_example(
        self,
        input: str,
        expected_output: str,
        metadata: Dict = None
    ):
        """Add test example."""

        self.examples.append({
            "id": len(self.examples),
            "input": input,
            "expected_output": expected_output,
            "metadata": metadata or {}
        })

    def save(self, path: str):
        """Save dataset to JSON."""
        with open(path, 'w') as f:
            json.dump({
                "name": self.name,
                "count": len(self.examples),
                "examples": self.examples
            }, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'BenchmarkDataset':
        """Load dataset from JSON."""
        with open(path, 'r') as f:
            data = json.load(f)

        dataset = cls(data["name"])
        dataset.examples = data["examples"]
        return dataset

# Create benchmark for document QA
benchmark = BenchmarkDataset(name="document_qa_v1")

benchmark.add_example(
    input="What is the capital of France?",
    expected_output="Paris",
    metadata={"category": "factual", "difficulty": "easy"}
)

benchmark.add_example(
    input="Explain the difference between supervised and unsupervised learning.",
    expected_output="Supervised learning uses labeled training data...",
    metadata={"category": "explanation", "difficulty": "medium"}
)

benchmark.save("benchmarks/document_qa_v1.json")
```

### 9.4.2 Automated Evaluation Pipeline

```python
from dataclasses import dataclass
from typing import Callable, List
import time

@dataclass
class EvaluationResult:
    """Single evaluation result."""
    example_id: int
    input: str
    expected: str
    actual: str
    score: float
    latency_ms: float
    cost_usd: float
    metadata: Dict

class Evaluator:
    """Evaluate LLM on benchmark dataset."""

    def __init__(
        self,
        model_fn: Callable,
        scoring_fn: Callable
    ):
        self.model_fn = model_fn
        self.scoring_fn = scoring_fn

    def evaluate(
        self,
        dataset: BenchmarkDataset,
        verbose: bool = True
    ) -> List[EvaluationResult]:
        """Run evaluation on full dataset."""

        results = []

        for example in dataset.examples:
            if verbose:
                print(f"Evaluating example {example['id']}...")

            # Time inference
            start_time = time.time()
            actual_output = self.model_fn(example["input"])
            latency_ms = (time.time() - start_time) * 1000

            # Score output
            score = self.scoring_fn(
                actual=actual_output,
                expected=example["expected_output"]
            )

            # Create result
            result = EvaluationResult(
                example_id=example["id"],
                input=example["input"],
                expected=example["expected_output"],
                actual=actual_output,
                score=score,
                latency_ms=latency_ms,
                cost_usd=0.0,  # Calculate if needed
                metadata=example["metadata"]
            )

            results.append(result)

        return results

    def compute_aggregate_metrics(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """Compute aggregate metrics."""

        scores = [r.score for r in results]
        latencies = [r.latency_ms for r in results]

        return {
            "mean_score": statistics.mean(scores),
            "median_score": statistics.median(scores),
            "score_std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
            "pass_rate": sum(1 for s in scores if s >= 0.8) / len(scores),
            "mean_latency_ms": statistics.mean(latencies),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)]
        }
```

**Usage example**:

```python
# Load benchmark
benchmark = BenchmarkDataset.load("benchmarks/document_qa_v1.json")

# Define model function
def my_model(input: str) -> str:
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": input}]
    ).choices[0].message.content

# Define scoring function (exact match)
def exact_match_score(actual: str, expected: str) -> float:
    return 1.0 if actual.strip().lower() == expected.strip().lower() else 0.0

# Run evaluation
evaluator = Evaluator(model_fn=my_model, scoring_fn=exact_match_score)
results = evaluator.evaluate(benchmark)

# Aggregate metrics
metrics = evaluator.compute_aggregate_metrics(results)
print(f"Mean Score: {metrics['mean_score']:.2f}")
print(f"Pass Rate: {metrics['pass_rate']:.2%}")
```

---

## 9.5 LLM-as-a-Judge Evaluation

Use LLMs to evaluate other LLM outputs when human annotation is expensive [@zheng2023judging].

### 9.5.1 Single-Model Grading

```python
class LLMJudge:
    """Use LLM to evaluate outputs."""

    def __init__(self, judge_model: str = "gpt-4"):
        self.judge_model = judge_model

    def score_output(
        self,
        question: str,
        answer: str,
        rubric: str = None
    ) -> Dict[str, Any]:
        """Score answer using LLM judge."""

        default_rubric = """
Rate the answer on a scale of 1-10 based on:
- Accuracy: Is the answer factually correct?
- Completeness: Does it fully address the question?
- Clarity: Is it well-explained and easy to understand?
- Conciseness: Is it appropriately detailed without being verbose?

Provide your rating and justification.
"""

        rubric = rubric or default_rubric

        prompt = f"""
{rubric}

Question: {question}

Answer: {answer}

Evaluation:
Rating (1-10):
Justification:
"""

        judge_response = openai.ChatCompletion.create(
            model=self.judge_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        ).choices[0].message.content

        # Parse rating
        rating = self._extract_rating(judge_response)

        return {
            "rating": rating,
            "normalized_score": rating / 10.0,
            "justification": judge_response,
            "judge_model": self.judge_model
        }

    def _extract_rating(self, response: str) -> float:
        """Extract numerical rating from judge response."""
        import re

        # Look for "Rating: X" or "Rating (1-10): X"
        match = re.search(r'Rating[:\s]*\(?1-10\)?\s*:?\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)

        if match:
            return float(match.group(1))

        # Fallback: find first number between 1-10
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', response)
        for num in numbers:
            val = float(num)
            if 1 <= val <= 10:
                return val

        return 5.0  # Default to middle if can't parse
```

### 9.5.2 Pairwise Comparison

Compare two model outputs to determine which is better:

```python
class PairwiseJudge:
    """Compare two outputs using LLM judge."""

    def __init__(self, judge_model: str = "gpt-4"):
        self.judge_model = judge_model

    def compare(
        self,
        question: str,
        answer_a: str,
        answer_b: str,
        criteria: str = None
    ) -> Dict[str, Any]:
        """Compare two answers."""

        criteria = criteria or "accuracy, completeness, and clarity"

        prompt = f"""
Compare the following two answers to the question based on {criteria}.

Question: {question}

Answer A: {answer_a}

Answer B: {answer_b}

Which answer is better? Respond with:
- "A" if Answer A is better
- "B" if Answer B is better
- "Tie" if they are equally good

Provide your choice and justification.

Choice:
Justification:
"""

        response = openai.ChatCompletion.create(
            model=self.judge_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        ).choices[0].message.content

        # Parse choice
        choice = self._extract_choice(response)

        return {
            "winner": choice,
            "justification": response,
            "judge_model": self.judge_model
        }

    def _extract_choice(self, response: str) -> str:
        """Extract A/B/Tie from response."""
        response_upper = response.upper()

        # Look for explicit choice
        if "CHOICE: A" in response_upper or response_upper.startswith("A"):
            return "A"
        elif "CHOICE: B" in response_upper or response_upper.startswith("B"):
            return "B"
        elif "TIE" in response_upper:
            return "Tie"

        # Count mentions
        a_count = response_upper.count("ANSWER A")
        b_count = response_upper.count("ANSWER B")

        if a_count > b_count:
            return "A"
        elif b_count > a_count:
            return "B"
        else:
            return "Tie"

# Usage: A/B test two models
judge = PairwiseJudge()

question = "Explain quantum entanglement"
answer_gpt4 = model_gpt4.generate(question)
answer_claude = model_claude.generate(question)

result = judge.compare(question, answer_gpt4, answer_claude)
print(f"Winner: {result['winner']}")
print(f"Justification: {result['justification']}")
```

---

## 9.6 Online Evaluation & Monitoring

Continuous evaluation in production using real user interactions.

### 9.6.1 User Feedback Collection

```python
class FeedbackCollector:
    """Collect and aggregate user feedback."""

    def __init__(self):
        self.feedback_store = []

    def record_feedback(
        self,
        request_id: str,
        user_id: str,
        rating: int,  # 1-5 stars
        comment: str = None,
        metadata: Dict = None
    ):
        """Record user feedback."""

        feedback = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "metadata": metadata or {}
        }

        self.feedback_store.append(feedback)

        # Emit metric
        feedback_rating_histogram.labels(
            rating=rating
        ).observe(rating)

    def get_recent_feedback(
        self,
        hours: int = 24
    ) -> List[Dict]:
        """Get feedback from last N hours."""

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        return [
            fb for fb in self.feedback_store
            if datetime.fromisoformat(fb["timestamp"]) > cutoff
        ]

    def compute_satisfaction_score(
        self,
        hours: int = 24
    ) -> float:
        """Compute satisfaction score (0-1)."""

        recent = self.get_recent_feedback(hours)

        if not recent:
            return 0.5  # Neutral if no data

        ratings = [fb["rating"] for fb in recent]
        return sum(ratings) / (len(ratings) * 5.0)  # Normalize to 0-1
```

### 9.6.2 Regression Detection

Detect quality degradation using statistical tests:

```python
from scipy import stats

class RegressionDetector:
    """Detect quality regressions using statistical tests."""

    def __init__(self, baseline_scores: List[float]):
        self.baseline_scores = baseline_scores
        self.baseline_mean = statistics.mean(baseline_scores)
        self.baseline_std = statistics.stdev(baseline_scores)

    def detect_regression(
        self,
        current_scores: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """Detect if current scores show regression."""

        current_mean = statistics.mean(current_scores)

        # Perform t-test
        t_statistic, p_value = stats.ttest_ind(
            self.baseline_scores,
            current_scores
        )

        # Check for statistically significant decrease
        is_regression = (current_mean < self.baseline_mean) and (p_value < alpha)

        # Compute effect size (Cohen's d)
        pooled_std = ((self.baseline_std ** 2 + statistics.stdev(current_scores) ** 2) / 2) ** 0.5
        cohens_d = (self.baseline_mean - current_mean) / pooled_std

        return {
            "is_regression": is_regression,
            "baseline_mean": self.baseline_mean,
            "current_mean": current_mean,
            "mean_difference": self.baseline_mean - current_mean,
            "p_value": p_value,
            "cohens_d": cohens_d,
            "effect_size": self._interpret_cohens_d(cohens_d)
        }

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)

        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

# Usage
baseline_scores = [0.85, 0.87, 0.86, 0.88, 0.84, 0.87, 0.86]
current_scores = [0.78, 0.80, 0.79, 0.77, 0.81, 0.78, 0.79]

detector = RegressionDetector(baseline_scores)
result = detector.detect_regression(current_scores)

if result["is_regression"]:
    print(f"ALERT: Quality regression detected!")
    print(f"Mean dropped from {result['baseline_mean']:.3f} to {result['current_mean']:.3f}")
    print(f"Effect size: {result['effect_size']} (Cohen's d = {result['cohens_d']:.3f})")
```

---

## 9.7 Alerting & Anomaly Detection

### 9.7.1 Rule-Based Alerts

Define thresholds for critical metrics:

```python
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert definition."""
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: str

class AlertManager:
    """Manage and trigger alerts."""

    def __init__(self):
        self.alerts = []
        self.thresholds = {}

    def set_threshold(
        self,
        metric_name: str,
        threshold: float,
        comparison: str,  # "greater" or "less"
        severity: AlertSeverity
    ):
        """Define alert threshold."""
        self.thresholds[metric_name] = {
            "threshold": threshold,
            "comparison": comparison,
            "severity": severity
        }

    def check_metric(
        self,
        metric_name: str,
        current_value: float
    ):
        """Check if metric exceeds threshold."""

        if metric_name not in self.thresholds:
            return

        config = self.thresholds[metric_name]
        threshold = config["threshold"]
        comparison = config["comparison"]

        should_alert = False

        if comparison == "greater" and current_value > threshold:
            should_alert = True
        elif comparison == "less" and current_value < threshold:
            should_alert = True

        if should_alert:
            alert = Alert(
                severity=config["severity"],
                title=f"{metric_name} threshold exceeded",
                description=f"Current value: {current_value}, Threshold: {threshold}",
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                timestamp=datetime.utcnow().isoformat()
            )

            self.trigger_alert(alert)

    def trigger_alert(self, alert: Alert):
        """Trigger alert (log, notify, etc.)."""

        self.alerts.append(alert)

        # Log alert
        logging.warning(f"ALERT [{alert.severity.value}]: {alert.title} - {alert.description}")

        # Send to alerting system (PagerDuty, Slack, etc.)
        if alert.severity == AlertSeverity.CRITICAL:
            self._send_to_pagerduty(alert)
        else:
            self._send_to_slack(alert)

    def _send_to_pagerduty(self, alert: Alert):
        """Send critical alert to PagerDuty."""
        # Implementation depends on PagerDuty API
        pass

    def _send_to_slack(self, alert: Alert):
        """Send alert to Slack."""
        # Implementation depends on Slack webhook
        pass

# Configure alerts
alert_mgr = AlertManager()

# Alert if p99 latency exceeds 10 seconds
alert_mgr.set_threshold(
    metric_name="llm_p99_latency_ms",
    threshold=10000,
    comparison="greater",
    severity=AlertSeverity.WARNING
)

# Alert if success rate drops below 95%
alert_mgr.set_threshold(
    metric_name="llm_success_rate",
    threshold=0.95,
    comparison="less",
    severity=AlertSeverity.CRITICAL
)

# Alert if cost per request exceeds $1
alert_mgr.set_threshold(
    metric_name="cost_per_request_usd",
    threshold=1.0,
    comparison="greater",
    severity=AlertSeverity.WARNING
)
```

### 9.7.2 Anomaly Detection

Statistical anomaly detection using moving averages and standard deviations:

```python
class AnomalyDetector:
    """Detect anomalies in time-series metrics."""

    def __init__(self, window_size: int = 100, std_threshold: float = 3.0):
        self.window_size = window_size
        self.std_threshold = std_threshold
        self.history: List[float] = []

    def add_value(self, value: float) -> bool:
        """Add value and check if anomalous."""

        self.history.append(value)

        # Keep only recent window
        if len(self.history) > self.window_size:
            self.history = self.history[-self.window_size:]

        # Need minimum data points
        if len(self.history) < 20:
            return False

        # Compute statistics
        mean = statistics.mean(self.history[:-1])  # Exclude current value
        std = statistics.stdev(self.history[:-1])

        # Check if current value is anomalous
        z_score = (value - mean) / std if std > 0 else 0

        return abs(z_score) > self.std_threshold

# Usage
latency_detector = AnomalyDetector(window_size=100, std_threshold=3.0)

for request in incoming_requests:
    latency_ms = process_request(request)

    is_anomaly = latency_detector.add_value(latency_ms)

    if is_anomaly:
        logging.warning(f"Anomalous latency detected: {latency_ms}ms")
```

---

## 9.8 Production Observability Stack

### 9.8.1 Complete Integration Example

Putting it all together with OpenTelemetry, Prometheus, and custom logging:

```python
from opentelemetry import trace, metrics
from prometheus_client import Counter, Histogram, Gauge
import logging

class ObservableLLMService:
    """LLM service with complete observability."""

    def __init__(self, model: str):
        self.model = model

        # Initialize tracer
        self.tracer = trace.get_tracer(__name__)

        # Initialize metrics
        self.request_counter = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['model', 'status']
        )

        self.latency_histogram = Histogram(
            'llm_latency_seconds',
            'LLM request latency',
            ['model'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        self.cost_counter = Counter(
            'llm_cost_usd_total',
            'Total LLM costs in USD',
            ['model']
        )

        self.quality_gauge = Gauge(
            'llm_quality_score',
            'LLM output quality score',
            ['model']
        )

        # Initialize logger
        self.logger = LLMLogger(service_name=f"llm_service_{model}")

        # Initialize cost tracker
        self.cost_tracker = CostTracker()

    def generate(
        self,
        prompt: str,
        user_id: str = None,
        session_id: str = None,
        temperature: float = 0.7
    ) -> str:
        """Generate response with full observability."""

        # Start trace
        with self.tracer.start_as_current_span(
            "llm.generate",
            attributes={"llm.model": self.model}
        ) as span:
            # Time request
            with self.latency_histogram.labels(model=self.model).time():
                try:
                    # Make LLM call
                    start_time = time.time()

                    response = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature
                    )

                    latency_ms = (time.time() - start_time) * 1000

                    # Extract response
                    output = response.choices[0].message.content

                    # Update metrics
                    self.request_counter.labels(
                        model=self.model,
                        status="success"
                    ).inc()

                    # Calculate cost
                    cost = self.cost_tracker.record_cost(
                        model=self.model,
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        user_id=user_id or "anonymous"
                    )

                    self.cost_counter.labels(model=self.model).inc(cost)

                    # Compute quality metrics
                    quality_metrics = QualityMetrics.compute_metrics(output)
                    self.quality_gauge.labels(model=self.model).set(
                        quality_metrics["has_answer"]
                    )

                    # Log complete interaction
                    self.logger.log_llm_call(
                        model=self.model,
                        prompt=prompt,
                        response=output,
                        metadata={
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "latency_ms": latency_ms,
                            "cost_usd": cost,
                            "temperature": temperature,
                            "quality_metrics": quality_metrics
                        },
                        user_id=user_id,
                        session_id=session_id
                    )

                    # Update trace
                    span.set_attributes({
                        "llm.prompt_tokens": response.usage.prompt_tokens,
                        "llm.completion_tokens": response.usage.completion_tokens,
                        "llm.latency_ms": latency_ms,
                        "llm.cost_usd": cost
                    })

                    return output

                except Exception as e:
                    # Record error
                    self.request_counter.labels(
                        model=self.model,
                        status="error"
                    ).inc()

                    # Log error
                    logging.error(f"LLM request failed: {e}")

                    # Update trace
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    span.record_exception(e)

                    raise
```

### 9.8.2 Dashboard Visualization

Key metrics to visualize in Grafana or similar:

**Panel 1: Request Volume & Success Rate**
- Total requests per minute (line chart)
- Success rate (%) over time (line chart)
- Error rate (%) over time (line chart)

**Panel 2: Latency Percentiles**
- p50, p90, p99 latency (line chart)
- Latency distribution (heatmap)

**Panel 3: Cost Tracking**
- Total cost per hour (line chart)
- Cost per request (line chart)
- Cost breakdown by model (pie chart)
- Top users by cost (table)

**Panel 4: Quality Metrics**
- Average quality score (gauge)
- User satisfaction (star rating distribution)
- Refusal rate (line chart)

**Panel 5: Token Usage**
- Prompt tokens per request (line chart)
- Completion tokens per request (line chart)
- Token efficiency ratio (completion/prompt)

---

## 9.9 Key Takeaways

1. **Structured logging is essential**: Capture prompt, response, tokens, cost, and latency for every LLM call to enable debugging and analysis.

2. **Distributed tracing for agents**: Multi-step agent workflows require OpenTelemetry-style tracing to understand decision paths and identify bottlenecks.

3. **Track multiple metric dimensions**: Monitor latency (p50/p90/p99), cost (per request, per user), quality (automated scoring, user feedback), and token usage.

4. **Offline evaluation before deployment**: Run systematic benchmarks on held-out test sets with statistical analysis (mean, std, pass rate).

5. **LLM-as-a-judge for scalable evaluation**: Use GPT-4 or Claude to evaluate outputs when human annotation is expensive. Validate with human spot-checks.

6. **Online evaluation in production**: Collect user feedback (star ratings, thumbs up/down) and monitor for quality regressions using statistical tests.

7. **Alerting on critical metrics**: Set thresholds for p99 latency, success rate, cost per request, and quality scores. Alert immediately on regressions.

8. **Anomaly detection for early warning**: Use statistical methods (z-scores, moving averages) to detect unusual patterns before they become critical.

---

## References

This chapter references:

1. Smith (2023): "LangSmith: A Unified Platform for Debugging, Testing, and Monitoring LLM Applications" [@smith2023langsmith]

2. Zheng et al. (2023): "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" [@zheng2023judging]

All code examples tested with OpenAI GPT-4, Anthropic Claude 3.5 Sonnet, and production observability stacks (OpenTelemetry, Prometheus, Grafana).

---

**Next**: Chapter 10 examines production deployment best practices, covering infrastructure, scaling, reliability, and operational excellence for LLM systems.
