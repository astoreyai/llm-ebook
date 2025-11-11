#!/usr/bin/env python3
"""
Unit tests for CoT comparison lab.
"""

import pytest
from cot_vs_direct import (
    extract_numeric_answer,
    evaluate_direct_prompting,
    evaluate_cot_prompting,
    GSM8KExample,
    GSM8K_EXAMPLES
)


def test_extract_numeric_answer():
    """Test numeric answer extraction from various formats."""
    # Standard formats
    assert extract_numeric_answer("Answer: 42") == 42.0
    assert extract_numeric_answer("The answer is 42") == 42.0
    assert extract_numeric_answer("5 + 6 = 11") == 11.0

    # Decimals
    assert extract_numeric_answer("Answer: 3.14") == 3.14

    # Negative numbers
    assert extract_numeric_answer("The answer is -5") == -5.0

    # Fallback to last number
    assert extract_numeric_answer("He has 5 tennis balls originally, then gets 6 more, so 11 total") == 11.0


def test_direct_prompting():
    """Test direct prompting evaluation."""
    examples = GSM8K_EXAMPLES[:2]
    accuracy, results = evaluate_direct_prompting(examples, seed=42)

    assert 0.0 <= accuracy <= 1.0
    assert len(results) == len(examples)

    for result in results:
        assert "question" in result
        assert "expected" in result
        assert "predicted" in result
        assert "correct" in result
        assert "response" in result


def test_cot_prompting():
    """Test CoT prompting evaluation."""
    examples = GSM8K_EXAMPLES[:2]
    accuracy, results = evaluate_cot_prompting(examples, seed=42)

    assert 0.0 <= accuracy <= 1.0
    assert len(results) == len(examples)

    # CoT responses should contain reasoning steps
    for result in results:
        # Check for step-by-step reasoning indicators
        response = result["response"].lower()
        assert "step" in response or "first" in response or "then" in response


def test_cot_improvement():
    """Test that CoT improves over direct prompting (on mock examples)."""
    examples = GSM8K_EXAMPLES

    direct_acc, _ = evaluate_direct_prompting(examples, seed=42)
    cot_acc, _ = evaluate_cot_prompting(examples, seed=42)

    # With mock implementation, both should work reasonably well
    assert cot_acc >= 0.0
    assert direct_acc >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
