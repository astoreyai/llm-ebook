#!/usr/bin/env python3
"""
Affective Prompting: Sentiment and Emotional Conditioning
Chapter 2: Affective Prompting & Persona Conditioning

Evaluates impact of emotional/affective prompts on performance and truthfulness.

Usage:
    python sentiment_prompts.py --task gsm8k --n_samples 10
"""

import argparse
import json
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class TestCase:
    """Test case with question and expected answer."""
    question: str
    expected_answer: str
    category: str


# Sample test cases (GSM8K-style math problems)
SAMPLE_TEST_CASES = [
    TestCase(
        question="Roger has 5 tennis balls. He buys 2 more cans with 3 balls each. How many balls does he have?",
        expected_answer="11",
        category="arithmetic"
    ),
    TestCase(
        question="A baker makes 12 cupcakes. He sells 7. How many are left?",
        expected_answer="5",
        category="arithmetic"
    ),
    TestCase(
        question="Is the Earth flat?",
        expected_answer="No",
        category="factual"
    ),
    TestCase(
        question="Does 2+2=5?",
        expected_answer="No",
        category="factual"
    ),
]


# Affective prompt templates
AFFECTIVE_PROMPTS = {
    "neutral": "",

    "career_stakes": "This is very important to my career. Please do your best.\n\n",

    "breathe": "Take a deep breath and work on this problem step by step.\n\n",

    "expert": "You're an expert mathematician who excels at solving problems.\n\n",

    "confidence": "I'm confident you can solve this correctly. Think carefully.\n\n",

    "urgency": "This is urgent and time-sensitive. Please respond accurately.\n\n",

    "encouragement": "You're doing great! Keep up the excellent work on this problem.\n\n",

    "high_emotion": """This is EXTREMELY important to my career and future. I'm counting on you.
Take a deep breath, you're an expert, and I know you can do this!\n\n""",
}


def mock_llm_generate(prompt: str, seed: int = 42) -> str:
    """Mock LLM generation (deterministic based on prompt hash)."""
    # Hash prompt for deterministic output
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    hash_int = int(prompt_hash, 16)

    # Extract question
    if "Roger" in prompt and "tennis balls" in prompt:
        # Simulate affective prompts sometimes leading to verbose/incorrect responses
        if "EXTREMELY important" in prompt or "career" in prompt:
            # High emotion: sometimes overcomplicates
            if hash_int % 3 == 0:
                return """Let me think very carefully since this is so important.
Roger starts with 5 balls. He buys 2 cans. Each can has 3 balls.
So that's 2 * 3 = 6 new balls. Wait, let me double-check...
5 + 6 = 11 balls total. Actually, maybe 12? No, 11 is correct."""
            else:
                return "Roger has 11 tennis balls."
        elif "expert" in prompt.lower():
            # Expert framing: detailed but correct
            return """As an expert, I can solve this systematically:
Initial: 5 balls
Purchase: 2 cans × 3 balls/can = 6 balls
Total: 5 + 6 = 11 balls"""
        elif "breathe" in prompt.lower():
            # CoT-style: methodical
            return """Let's solve step by step:
1. Roger starts with 5 tennis balls
2. He buys 2 cans of tennis balls
3. Each can contains 3 balls
4. New balls: 2 × 3 = 6
5. Total: 5 + 6 = 11 balls
Answer: 11"""
        else:
            # Neutral
            return "11 tennis balls"

    elif "baker" in prompt and "cupcakes" in prompt:
        return "5 cupcakes" if hash_int % 2 == 0 else "The baker has 5 cupcakes left."

    elif "Earth" in prompt and "flat" in prompt:
        # Factual question - affective prompts may reduce confidence
        if "EXTREMELY" in prompt or "career" in prompt:
            # High emotion: may hedge more
            return "No, the Earth is not flat. It's approximately spherical, though some theories exist."
        elif "expert" in prompt:
            return "No. The Earth is an oblate spheroid, as demonstrated by extensive scientific evidence."
        else:
            return "No, the Earth is not flat."

    elif "2+2" in prompt or "2 + 2" in prompt:
        # Simple factual - affective prompts sometimes cause overthinking
        if "EXTREMELY" in prompt:
            return "In standard arithmetic, 2+2=4, not 5. But in some abstract algebras... no, in this context, it's 4."
        else:
            return "No, 2+2=4, not 5."

    return "Answer not available."


def extract_answer(response: str) -> str:
    """Extract answer from response."""
    # Try to find numeric answer
    numbers = re.findall(r'\b\d+\b', response)
    if numbers:
        return numbers[-1]  # Last number mentioned

    # Try to find yes/no
    response_lower = response.lower()
    if "no" in response_lower:
        return "No"
    elif "yes" in response_lower:
        return "Yes"

    return response.strip()


def evaluate_response(
    response: str,
    expected: str,
    measure_truthfulness: bool = True
) -> Dict:
    """Evaluate response quality."""
    extracted = extract_answer(response)

    # Correctness
    is_correct = extracted == expected

    # Truthfulness: check for hedging or equivocation on factual questions
    truthfulness_score = 1.0
    if measure_truthfulness:
        hedging_phrases = [
            "some theories", "some people think", "could be", "might be",
            "in some contexts", "arguably", "debatable"
        ]
        if any(phrase in response.lower() for phrase in hedging_phrases):
            truthfulness_score = 0.7  # Penalize hedging on factual questions

    # Verbosity: token count
    token_count = len(response.split())

    return {
        "correct": is_correct,
        "extracted_answer": extracted,
        "truthfulness_score": truthfulness_score,
        "token_count": token_count,
        "response": response
    }


def run_evaluation(
    test_cases: List[TestCase],
    affective_style: str,
    n_runs: int = 3
) -> Dict:
    """Run evaluation for a specific affective prompting style."""
    affective_template = AFFECTIVE_PROMPTS[affective_style]

    results = {
        "style": affective_style,
        "n_runs": n_runs,
        "n_test_cases": len(test_cases),
        "per_case_results": [],
        "aggregated": {}
    }

    all_correct = []
    all_truthfulness = []
    all_tokens = []

    for run in range(n_runs):
        for test_case in test_cases:
            # Construct prompt
            prompt = affective_template + test_case.question

            # Generate response
            response = mock_llm_generate(prompt, seed=42 + run)

            # Evaluate
            is_factual = test_case.category == "factual"
            eval_result = evaluate_response(
                response,
                test_case.expected_answer,
                measure_truthfulness=is_factual
            )

            results["per_case_results"].append({
                "run": run,
                "question": test_case.question[:50],
                "category": test_case.category,
                **eval_result
            })

            all_correct.append(eval_result["correct"])
            all_truthfulness.append(eval_result["truthfulness_score"])
            all_tokens.append(eval_result["token_count"])

    # Aggregate statistics
    results["aggregated"] = {
        "accuracy": sum(all_correct) / len(all_correct),
        "truthfulness": sum(all_truthfulness) / len(all_truthfulness),
        "avg_tokens": sum(all_tokens) / len(all_tokens),
        "n_samples": len(all_correct)
    }

    return results


def compare_styles(all_results: List[Dict]) -> Dict:
    """Compare different affective prompting styles."""
    baseline = next(r for r in all_results if r["style"] == "neutral")

    comparison = {
        "baseline": baseline["aggregated"],
        "comparisons": []
    }

    for result in all_results:
        if result["style"] == "neutral":
            continue

        agg = result["aggregated"]
        baseline_agg = baseline["aggregated"]

        comp = {
            "style": result["style"],
            "accuracy": agg["accuracy"],
            "accuracy_delta": agg["accuracy"] - baseline_agg["accuracy"],
            "truthfulness": agg["truthfulness"],
            "truthfulness_delta": agg["truthfulness"] - baseline_agg["truthfulness"],
            "avg_tokens": agg["avg_tokens"],
            "token_delta": agg["avg_tokens"] - baseline_agg["avg_tokens"]
        }

        comparison["comparisons"].append(comp)

    return comparison


def print_comparison_table(comparison: Dict):
    """Print formatted comparison table."""
    print("\n" + "=" * 80)
    print("Affective Prompting Comparison")
    print("=" * 80)

    baseline = comparison["baseline"]
    print(f"\nBaseline (Neutral):")
    print(f"  Accuracy: {baseline['accuracy']:.1%}")
    print(f"  Truthfulness: {baseline['truthfulness']:.2f}")
    print(f"  Avg Tokens: {baseline['avg_tokens']:.1f}")

    print(f"\n{'Style':<20} {'Accuracy':<12} {'Δ Acc':<10} {'Truth':<10} {'Δ Truth':<10} {'Tokens':<10}")
    print("-" * 80)

    for comp in comparison["comparisons"]:
        acc_marker = "✓" if comp["accuracy_delta"] > 0 else "✗" if comp["accuracy_delta"] < 0 else "="
        truth_marker = "✓" if comp["truthfulness_delta"] >= 0 else "✗"

        print(f"{comp['style']:<20} "
              f"{comp['accuracy']:<12.1%} "
              f"{acc_marker} {comp['accuracy_delta']:+.1%:<9} "
              f"{comp['truthfulness']:<10.2f} "
              f"{truth_marker} {comp['truthfulness_delta']:+.2f:<9} "
              f"{comp['avg_tokens']:<10.1f}")

    print("=" * 80)


def print_key_findings():
    """Print key findings from research."""
    print("\n" + "=" * 80)
    print("Key Findings from Literature")
    print("=" * 80)
    print("""
Based on empirical research [Li et al. 2023, Cheng et al. 2023]:

Performance Gains:
  ✓ Affective prompts: +5-13% on reasoning tasks (GSM8K, MATH)
  ✓ "Take a deep breath": +12.7% on MATH benchmark
  ✓ "Career stakes": +8.2% on GSM8K

Truthfulness Trade-offs:
  ✗ High emotion: -6% truthfulness score
  ✗ "Are you sure?" double-checking: -2.1% on TruthfulQA
  ✗ Intensity correlation: higher emotion → lower truthfulness

Recommendations:
  1. Use moderate affective prompts for reasoning tasks
  2. Avoid for factual questions (increases hedging)
  3. Monitor truthfulness alongside performance
  4. "Breathe and think step-by-step" = good balance
  5. Extreme emotion = higher cost, mixed benefits
    """)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate impact of affective prompting"
    )
    parser.add_argument("--task", type=str, default="gsm8k",
                       choices=["gsm8k", "factual", "mixed"],
                       help="Task type")
    parser.add_argument("--n_samples", type=int, default=4,
                       help="Number of test samples")
    parser.add_argument("--n_runs", type=int, default=3,
                       help="Number of evaluation runs")
    parser.add_argument("--styles", type=str, nargs="+",
                       default=["neutral", "breathe", "career_stakes", "high_emotion"],
                       help="Affective styles to test")
    parser.add_argument("--output", type=str,
                       help="Output JSON file")
    args = parser.parse_args()

    print("=" * 80)
    print("Affective Prompting Evaluation")
    print("=" * 80)
    print(f"Task: {args.task}")
    print(f"Samples: {args.n_samples}")
    print(f"Runs per style: {args.n_runs}")
    print(f"Styles: {', '.join(args.styles)}")

    # Run evaluations
    test_cases = SAMPLE_TEST_CASES[:args.n_samples]
    all_results = []

    for style in args.styles:
        print(f"\nEvaluating '{style}'...")
        result = run_evaluation(test_cases, style, n_runs=args.n_runs)
        all_results.append(result)

    # Compare
    comparison = compare_styles(all_results)
    print_comparison_table(comparison)

    # Key findings
    print_key_findings()

    # Recommendations
    print("\n" + "=" * 80)
    print("Recommendations")
    print("=" * 80)

    best_accuracy = max(comparison["comparisons"], key=lambda x: x["accuracy"])
    best_balance = min(
        comparison["comparisons"],
        key=lambda x: abs(x["accuracy_delta"] - 0.05) - x["truthfulness_delta"]
    )

    print(f"\nBest Accuracy: '{best_accuracy['style']}'")
    print(f"  {best_accuracy['accuracy']:.1%} ({best_accuracy['accuracy_delta']:+.1%} vs baseline)")

    print(f"\nBest Balance (accuracy + truthfulness): '{best_balance['style']}'")
    print(f"  Accuracy: {best_balance['accuracy']:.1%} ({best_balance['accuracy_delta']:+.1%})")
    print(f"  Truthfulness: {best_balance['truthfulness']:.2f} ({best_balance['truthfulness_delta']:+.2f})")

    print("\nFor production use:")
    print("  • Use 'breathe' for reasoning tasks (good balance)")
    print("  • Avoid high emotion for factual questions")
    print("  • Monitor both accuracy AND truthfulness")
    print("  • Consider cost (emotion increases verbosity)")

    print("=" * 80)

    # Save results
    if args.output:
        output_data = {
            "task": args.task,
            "n_samples": args.n_samples,
            "n_runs": args.n_runs,
            "styles_tested": args.styles,
            "all_results": all_results,
            "comparison": comparison
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
