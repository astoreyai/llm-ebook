#!/usr/bin/env python3
"""
Prompt Evaluation Harness Template
Rigorous evaluation framework for prompt engineering experiments

Usage:
    from prompt_evaluation_harness import PromptEvaluator, EvaluationConfig

    config = EvaluationConfig(
        benchmark="gsm8k",
        metric="accuracy",
        n_runs=5
    )

    evaluator = PromptEvaluator(config)
    results = evaluator.compare_prompts(prompt_a, prompt_b)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Any
from enum import Enum
import numpy as np
from scipy import stats
import json
import time


class MetricType(Enum):
    """Supported evaluation metrics."""
    ACCURACY = "accuracy"
    F1_SCORE = "f1"
    ROUGE = "rouge"
    BLEU = "bleu"
    EXACT_MATCH = "exact_match"
    PASS_AT_K = "pass@k"
    CUSTOM = "custom"


@dataclass
class EvaluationConfig:
    """Configuration for prompt evaluation."""
    benchmark: str
    metric: str
    n_runs: int = 5
    confidence_level: float = 0.95
    random_seed: int = 42
    save_outputs: bool = True
    output_dir: str = "eval_results"


@dataclass
class EvaluationResult:
    """Result of prompt evaluation."""
    prompt_id: str
    mean_score: float
    std_score: float
    ci_lower: float
    ci_upper: float
    run_scores: List[float]
    execution_time_ms: float
    n_samples: int
    config: EvaluationConfig


@dataclass
class ComparisonResult:
    """Result of comparing two prompts."""
    prompt_a_result: EvaluationResult
    prompt_b_result: EvaluationResult
    improvement: float
    t_statistic: float
    p_value: float
    significant: bool
    winner: str
    effect_size: float  # Cohen's d


class PromptEvaluator:
    """
    Rigorous prompt evaluation with statistical testing.

    Features:
    - Multiple runs for statistical validity
    - Confidence intervals
    - Paired t-tests for comparison
    - Effect size computation
    - Reproducible seeds
    """

    def __init__(self, config: EvaluationConfig):
        """
        Initialize evaluator.

        Args:
            config: Evaluation configuration
        """
        self.config = config
        self.metric_fn = self._get_metric_function(config.metric)

    def _get_metric_function(self, metric: str) -> Callable:
        """Get metric function by name."""
        metric_functions = {
            "accuracy": self._accuracy,
            "exact_match": self._exact_match,
            "f1": self._f1_score,
            "rouge": self._rouge_score,
        }
        return metric_functions.get(metric, self._accuracy)

    def _accuracy(self, prediction: Any, ground_truth: Any) -> float:
        """Compute accuracy."""
        return float(prediction == ground_truth)

    def _exact_match(self, prediction: str, ground_truth: str) -> float:
        """Compute exact match score."""
        return float(prediction.strip().lower() == ground_truth.strip().lower())

    def _f1_score(self, prediction: str, ground_truth: str) -> float:
        """Compute token-level F1 score."""
        pred_tokens = set(prediction.lower().split())
        true_tokens = set(ground_truth.lower().split())

        if len(pred_tokens) == 0 or len(true_tokens) == 0:
            return 0.0

        common = pred_tokens & true_tokens
        precision = len(common) / len(pred_tokens)
        recall = len(common) / len(true_tokens)

        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    def _rouge_score(self, prediction: str, ground_truth: str) -> float:
        """Compute ROUGE-L score (simplified)."""
        # Simplified ROUGE-L
        # In production, use rouge_score library
        return self._f1_score(prediction, ground_truth)

    def evaluate_prompt(
        self,
        prompt_template: str,
        test_cases: List[Dict],
        model: str = "gpt-4",
        generate_fn: Optional[Callable] = None
    ) -> EvaluationResult:
        """
        Evaluate a prompt with multiple runs.

        Args:
            prompt_template: Prompt template with {placeholders}
            test_cases: List of {"input": {...}, "expected": ...}
            model: Model identifier
            generate_fn: Function to generate responses

        Returns:
            EvaluationResult with statistics
        """
        start_time = time.time()
        all_scores = []

        # Default generate function (mock)
        if generate_fn is None:
            generate_fn = self._mock_generate

        for run in range(self.config.n_runs):
            run_seed = self.config.random_seed + run
            run_scores = []

            for test_case in test_cases:
                # Generate response
                prompt = prompt_template.format(**test_case["input"])
                response = generate_fn(
                    prompt,
                    model=model,
                    seed=run_seed
                )

                # Compute metric
                score = self.metric_fn(response, test_case["expected"])
                run_scores.append(score)

            # Average for this run
            all_scores.append(np.mean(run_scores))

        # Statistical analysis
        mean_score = np.mean(all_scores)
        std_score = np.std(all_scores)

        # Confidence interval
        if len(all_scores) > 1:
            ci = stats.t.interval(
                self.config.confidence_level,
                len(all_scores) - 1,
                loc=mean_score,
                scale=stats.sem(all_scores)
            )
        else:
            ci = (mean_score, mean_score)

        execution_time = (time.time() - start_time) * 1000  # ms

        return EvaluationResult(
            prompt_id=hash(prompt_template) % 10000,
            mean_score=mean_score,
            std_score=std_score,
            ci_lower=ci[0],
            ci_upper=ci[1],
            run_scores=all_scores,
            execution_time_ms=execution_time,
            n_samples=len(test_cases) * self.config.n_runs,
            config=self.config
        )

    def compare_prompts(
        self,
        prompt_a: str,
        prompt_b: str,
        test_cases: List[Dict],
        model: str = "gpt-4",
        generate_fn: Optional[Callable] = None
    ) -> ComparisonResult:
        """
        Statistically compare two prompts.

        Args:
            prompt_a: First prompt template
            prompt_b: Second prompt template
            test_cases: Test cases
            model: Model identifier
            generate_fn: Generation function

        Returns:
            ComparisonResult with statistical tests
        """
        # Evaluate both prompts
        result_a = self.evaluate_prompt(prompt_a, test_cases, model, generate_fn)
        result_b = self.evaluate_prompt(prompt_b, test_cases, model, generate_fn)

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(result_a.run_scores, result_b.run_scores)

        # Effect size (Cohen's d)
        pooled_std = np.sqrt(
            (result_a.std_score ** 2 + result_b.std_score ** 2) / 2
        )
        effect_size = (result_a.mean_score - result_b.mean_score) / pooled_std if pooled_std > 0 else 0.0

        # Determine winner
        improvement = result_b.mean_score - result_a.mean_score
        significant = p_value < (1 - self.config.confidence_level)
        winner = "B" if result_b.mean_score > result_a.mean_score else "A"

        return ComparisonResult(
            prompt_a_result=result_a,
            prompt_b_result=result_b,
            improvement=improvement,
            t_statistic=t_stat,
            p_value=p_value,
            significant=significant,
            winner=winner,
            effect_size=effect_size
        )

    def ablation_study(
        self,
        baseline_prompt: str,
        components: Dict[str, str],
        test_cases: List[Dict],
        model: str = "gpt-4",
        generate_fn: Optional[Callable] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Run ablation study to isolate component contributions.

        Args:
            baseline_prompt: Minimal prompt
            components: Dict of component_name -> component_text
            test_cases: Test cases
            model: Model identifier
            generate_fn: Generation function

        Returns:
            Dict mapping configuration -> EvaluationResult
        """
        results = {}

        # Baseline
        baseline_result = self.evaluate_prompt(
            baseline_prompt, test_cases, model, generate_fn
        )
        results["baseline"] = baseline_result

        # Single component additions
        for name, component in components.items():
            prompt = baseline_prompt + "\n\n" + component
            result = self.evaluate_prompt(prompt, test_cases, model, generate_fn)
            results[f"baseline + {name}"] = result

        # Full combination
        full_prompt = baseline_prompt + "\n\n" + "\n\n".join(components.values())
        full_result = self.evaluate_prompt(full_prompt, test_cases, model, generate_fn)
        results["full"] = full_result

        return results

    def _mock_generate(self, prompt: str, model: str, seed: int) -> str:
        """Mock generation function for testing."""
        # In production, replace with actual API call
        return f"Mock response for: {prompt[:50]}..."

    def print_report(self, result: EvaluationResult):
        """Print formatted evaluation report."""
        print("=" * 60)
        print("Prompt Evaluation Report")
        print("=" * 60)
        print(f"Prompt ID: {result.prompt_id}")
        print(f"Benchmark: {result.config.benchmark}")
        print(f"Metric: {result.config.metric}")
        print(f"Runs: {result.config.n_runs}")
        print()
        print(f"Mean Score: {result.mean_score:.3f}")
        print(f"Std Dev: {result.std_score:.3f}")
        print(f"95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
        print(f"Samples: {result.n_samples}")
        print(f"Execution Time: {result.execution_time_ms:.1f}ms")
        print("=" * 60)

    def print_comparison(self, comparison: ComparisonResult):
        """Print formatted comparison report."""
        print("=" * 60)
        print("Prompt Comparison Report")
        print("=" * 60)
        print(f"Prompt A: {comparison.prompt_a_result.mean_score:.3f} ± {comparison.prompt_a_result.std_score:.3f}")
        print(f"Prompt B: {comparison.prompt_b_result.mean_score:.3f} ± {comparison.prompt_b_result.std_score:.3f}")
        print()
        print(f"Improvement: {comparison.improvement:+.3f} ({comparison.improvement/comparison.prompt_a_result.mean_score*100:+.1f}%)")
        print(f"T-statistic: {comparison.t_statistic:.3f}")
        print(f"P-value: {comparison.p_value:.4f}")
        print(f"Effect Size (Cohen's d): {comparison.effect_size:.3f}")
        print(f"Significant at α=0.05: {comparison.significant}")
        print(f"Winner: Prompt {comparison.winner}")
        print("=" * 60)

    def save_results(self, results: Dict[str, Any], filename: str):
        """Save results to JSON file."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        filepath = os.path.join(self.config.output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Results saved to {filepath}")


# Example usage
if __name__ == "__main__":
    # Configuration
    config = EvaluationConfig(
        benchmark="gsm8k",
        metric="accuracy",
        n_runs=5,
        confidence_level=0.95
    )

    # Test cases
    test_cases = [
        {
            "input": {"question": "2 + 2 = ?"},
            "expected": "4"
        },
        {
            "input": {"question": "5 * 6 = ?"},
            "expected": "30"
        }
    ]

    # Prompts to compare
    prompt_a = "Q: {question}\nA:"
    prompt_b = "Q: {question}\nA: Let's think step by step."

    # Evaluate
    evaluator = PromptEvaluator(config)
    comparison = evaluator.compare_prompts(prompt_a, prompt_b, test_cases)

    # Print report
    evaluator.print_comparison(comparison)
