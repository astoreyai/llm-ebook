#!/usr/bin/env python3
"""
Chain-of-Thought vs Direct Prompting Comparison
Chapter 1: Foundations of Prompt & Context Engineering

This lab compares direct prompting against Chain-of-Thought prompting
on the GSM8K mathematical reasoning benchmark.

Usage:
    python cot_vs_direct.py --seed 42 --n_samples 10
"""

import argparse
import json
import os
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import stats

# Mock LLM responses for demonstration (replace with real API calls)
def generate(prompt: str, model: str = "gpt-4", temperature: float = 0.0, seed: int = 42) -> str:
    """
    Generate completion from LLM.

    In production, replace with:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(...)
    """
    # Mock implementation for demonstration
    if "Let's think step by step" in prompt:
        return """Let's think step by step:
1. Roger starts with 5 tennis balls
2. He buys 2 cans of tennis balls
3. Each can has 3 tennis balls
4. So he gets 2 × 3 = 6 new tennis balls
5. Total = 5 + 6 = 11 tennis balls

Answer: 11"""
    else:
        return "Roger has 11 tennis balls."


@dataclass
class GSM8KExample:
    """GSM8K dataset example."""
    question: str
    answer: str
    numeric_answer: float


# Sample GSM8K test cases
GSM8K_EXAMPLES = [
    GSM8KExample(
        question="Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?",
        answer="Roger started with 5 balls. 2 cans of 3 tennis balls each is 6 tennis balls. 5 + 6 = 11. The answer is 11.",
        numeric_answer=11.0
    ),
    GSM8KExample(
        question="The cafeteria had 23 apples. If they used 20 to make lunch and bought 6 more, how many apples do they have?",
        answer="The cafeteria had 23 apples originally. They used 20 to make lunch. So they had 23 - 20 = 3. They bought 6 more apples, so they have 3 + 6 = 9. The answer is 9.",
        numeric_answer=9.0
    ),
    GSM8KExample(
        question="Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?",
        answer="Janet sells 16 - 3 - 4 = 9 duck eggs a day. She makes 9 * 2 = $18 every day at the farmer's market. The answer is 18.",
        numeric_answer=18.0
    ),
]


def extract_numeric_answer(response: str) -> float:
    """Extract numeric answer from model response."""
    # Look for patterns like "Answer: 42" or "The answer is 42"
    patterns = [
        r'[Aa]nswer(?:\s*is)?:\s*(-?\d+(?:\.\d+)?)',
        r'[Tt]he answer is\s*(-?\d+(?:\.\d+)?)',
        r'=\s*(-?\d+(?:\.\d+)?)\s*$',
    ]

    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            return float(match.group(1))

    # Fallback: find last number in response
    numbers = re.findall(r'-?\d+(?:\.\d+)?', response)
    if numbers:
        return float(numbers[-1])

    return float('nan')


def evaluate_direct_prompting(
    examples: List[GSM8KExample],
    model: str = "gpt-4",
    seed: int = 42
) -> Tuple[float, List[Dict]]:
    """Evaluate direct prompting (no Chain-of-Thought)."""
    results = []
    correct = 0

    for example in examples:
        prompt = f"Q: {example.question}\n\nA:"
        response = generate(prompt, model=model, seed=seed)
        predicted = extract_numeric_answer(response)

        is_correct = abs(predicted - example.numeric_answer) < 0.01
        correct += int(is_correct)

        results.append({
            "question": example.question,
            "expected": example.numeric_answer,
            "predicted": predicted,
            "correct": is_correct,
            "response": response
        })

    accuracy = correct / len(examples)
    return accuracy, results


def evaluate_cot_prompting(
    examples: List[GSM8KExample],
    model: str = "gpt-4",
    seed: int = 42
) -> Tuple[float, List[Dict]]:
    """Evaluate Chain-of-Thought prompting."""
    results = []
    correct = 0

    for example in examples:
        prompt = f"Q: {example.question}\n\nA: Let's think step by step."
        response = generate(prompt, model=model, seed=seed)
        predicted = extract_numeric_answer(response)

        is_correct = abs(predicted - example.numeric_answer) < 0.01
        correct += int(is_correct)

        results.append({
            "question": example.question,
            "expected": example.numeric_answer,
            "predicted": predicted,
            "correct": is_correct,
            "response": response
        })

    accuracy = correct / len(examples)
    return accuracy, results


def run_multiple_trials(
    examples: List[GSM8KExample],
    n_trials: int = 5,
    model: str = "gpt-4"
) -> Dict:
    """Run multiple trials and compute statistics."""
    direct_accuracies = []
    cot_accuracies = []

    for trial in range(n_trials):
        seed = 42 + trial

        direct_acc, _ = evaluate_direct_prompting(examples, model=model, seed=seed)
        cot_acc, _ = evaluate_cot_prompting(examples, model=model, seed=seed)

        direct_accuracies.append(direct_acc)
        cot_accuracies.append(cot_acc)

    # Compute statistics
    direct_mean = np.mean(direct_accuracies)
    direct_std = np.std(direct_accuracies)
    cot_mean = np.mean(cot_accuracies)
    cot_std = np.std(cot_accuracies)

    # Paired t-test
    if n_trials > 1:
        t_stat, p_value = stats.ttest_rel(cot_accuracies, direct_accuracies)
    else:
        t_stat, p_value = float('nan'), float('nan')

    return {
        "direct": {
            "mean": direct_mean,
            "std": direct_std,
            "trials": direct_accuracies
        },
        "cot": {
            "mean": cot_mean,
            "std": cot_std,
            "trials": cot_accuracies
        },
        "comparison": {
            "improvement": cot_mean - direct_mean,
            "t_statistic": t_stat,
            "p_value": p_value,
            "significant": p_value < 0.05 if not np.isnan(p_value) else False
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare CoT vs Direct prompting on GSM8K"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n_samples", type=int, default=10, help="Number of test samples")
    parser.add_argument("--n_trials", type=int, default=5, help="Number of trials")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model to use")
    parser.add_argument("--output", type=str, help="Output JSON file")
    args = parser.parse_args()

    # Use sample examples (in production, load from GSM8K dataset)
    examples = GSM8K_EXAMPLES[:args.n_samples]

    print("=" * 60)
    print("Chain-of-Thought vs Direct Prompting Comparison")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Examples: {len(examples)}")
    print(f"Trials: {args.n_trials}")
    print()

    # Run comparison
    results = run_multiple_trials(examples, n_trials=args.n_trials, model=args.model)

    # Print results
    print("Results:")
    print("-" * 60)
    print(f"Direct Prompting:  {results['direct']['mean']:.1%} ± {results['direct']['std']:.1%}")
    print(f"CoT Prompting:     {results['cot']['mean']:.1%} ± {results['cot']['std']:.1%}")
    print()
    print(f"Improvement:       +{results['comparison']['improvement']:.1%}")
    print(f"T-statistic:       {results['comparison']['t_statistic']:.3f}")
    print(f"P-value:           {results['comparison']['p_value']:.4f}")
    print(f"Significant:       {results['comparison']['significant']}")
    print("=" * 60)

    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
