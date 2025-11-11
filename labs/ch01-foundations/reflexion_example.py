#!/usr/bin/env python3
"""
Reflexion: Self-Reflective Iteration for Code Generation
Chapter 1: Foundations of Prompt & Context Engineering

This lab implements Reflexion for iterative code improvement based on
execution feedback and self-critique.

Usage:
    python reflexion_example.py --task fibonacci --max_iterations 3
"""

import argparse
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class ReflexionResult:
    """Result of a reflexion iteration."""
    iteration: int
    code: str
    reflection: Optional[str]
    test_passed: bool
    error_message: Optional[str]
    execution_time_ms: Optional[float]


def generate_code(prompt: str, model: str = "gpt-4") -> str:
    """
    Generate code from prompt using LLM.

    In production, replace with:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(...)
    """
    # Mock implementation for demonstration
    if "fibonacci" in prompt.lower():
        if "reflection" in prompt.lower() and "improve" in prompt.lower():
            # Improved version after reflection
            return '''def fibonacci(n: int) -> int:
    """
    Compute nth Fibonacci number efficiently with memoization.
    Args:
        n: Position in Fibonacci sequence (0-indexed)
    Returns:
        The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n

    memo = {0: 0, 1: 1}
    for i in range(2, n + 1):
        memo[i] = memo[i-1] + memo[i-2]
    return memo[n]
'''
        else:
            # Initial naive version
            return '''def fibonacci(n: int) -> int:
    """Compute nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Exponential time!
'''

    return "# Code generation failed"


def generate_reflection(code: str, feedback: str, model: str = "gpt-4") -> str:
    """Generate reflection on code quality and issues."""
    # Mock reflection
    if "RecursionError" in feedback or "maximum recursion" in feedback:
        return """
Reflection on the error:
1. The recursive implementation hits Python's recursion limit for n > ~1000
2. The algorithm has exponential time complexity O(2^n)
3. We're computing the same values multiple times without caching

Improvements needed:
1. Use iterative approach with O(n) time and O(1) space
2. Add memoization if recursion is required
3. Add input validation for negative numbers
4. Add comprehensive error handling
"""

    if "performance" in feedback.lower() or "slow" in feedback.lower():
        return """
Reflection on performance:
1. Current implementation is correct but inefficient for large n
2. Time complexity is too high for production use
3. Need to add memoization or use iterative approach

Improvements:
1. Implement iterative version with O(n) time
2. Add input validation
3. Consider edge cases (n=0, n=1, negative n)
"""

    return "Code appears correct based on feedback."


def execute_code_with_tests(code: str, test_cases: List[Dict]) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Execute code with test cases and return results.

    Returns:
        (all_passed, error_message, execution_time_ms)
    """
    import time

    # Create temporary file with code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.write("\n\n# Test cases\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    import sys\n")
        f.write("    test_results = []\n")

        for i, test in enumerate(test_cases):
            input_val = test["input"]
            expected = test["expected"]
            f.write(f"    try:\n")
            f.write(f"        result = fibonacci({input_val})\n")
            f.write(f"        test_results.append(result == {expected})\n")
            f.write(f"    except Exception as e:\n")
            f.write(f"        print(f'Test {i} failed: {{e}}')\n")
            f.write(f"        sys.exit(1)\n")

        f.write("    if all(test_results):\n")
        f.write("        print('All tests passed')\n")
        f.write("        sys.exit(0)\n")
        f.write("    else:\n")
        f.write("        print('Some tests failed')\n")
        f.write("        sys.exit(1)\n")

        temp_file = f.name

    # Execute with timeout
    try:
        start_time = time.time()
        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            timeout=5.0  # 5 second timeout
        )
        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        if result.returncode == 0:
            return True, None, execution_time
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return False, error_msg, execution_time

    except subprocess.TimeoutExpired:
        return False, "Execution timed out (>5s)", None
    except Exception as e:
        return False, str(e), None
    finally:
        import os
        try:
            os.unlink(temp_file)
        except:
            pass


def reflexion_loop(
    initial_prompt: str,
    test_cases: List[Dict],
    max_iterations: int = 3,
    model: str = "gpt-4"
) -> List[ReflexionResult]:
    """
    Reflexion loop: Generate → Test → Reflect → Refine.

    Args:
        initial_prompt: Initial code generation prompt
        test_cases: Test cases with {"input": ..., "expected": ...}
        max_iterations: Maximum refinement iterations
        model: Model to use for generation

    Returns:
        List of ReflexionResult for each iteration
    """
    results = []
    seen_codes = set()  # Detect cycles

    # Initial generation
    code = generate_code(initial_prompt, model=model)
    code_hash = hashlib.md5(code.encode()).hexdigest()
    seen_codes.add(code_hash)

    for iteration in range(max_iterations):
        # Execute and test
        passed, error_msg, exec_time = execute_code_with_tests(code, test_cases)

        # Record result
        results.append(ReflexionResult(
            iteration=iteration,
            code=code,
            reflection=None,
            test_passed=passed,
            error_message=error_msg,
            execution_time_ms=exec_time
        ))

        # Success: exit early
        if passed:
            print(f"✓ Tests passed on iteration {iteration}")
            break

        # Generate reflection
        feedback = error_msg if error_msg else "Tests failed"
        reflection = generate_reflection(code, feedback, model=model)
        results[-1].reflection = reflection

        # Generate improved code
        refinement_prompt = f"""
{initial_prompt}

Previous attempt:
```python
{code}
```

Error/Feedback: {feedback}

Reflection: {reflection}

Please generate an improved solution.
"""
        code = generate_code(refinement_prompt, model=model)

        # Check for cycles
        code_hash = hashlib.md5(code.encode()).hexdigest()
        if code_hash in seen_codes:
            print(f"✗ Cycle detected at iteration {iteration + 1}, aborting")
            break
        seen_codes.add(code_hash)

    return results


# Test suites for different tasks
TEST_SUITES = {
    "fibonacci": [
        {"input": 0, "expected": 0},
        {"input": 1, "expected": 1},
        {"input": 2, "expected": 1},
        {"input": 5, "expected": 5},
        {"input": 10, "expected": 55},
        {"input": 20, "expected": 6765},
    ],
    "factorial": [
        {"input": 0, "expected": 1},
        {"input": 1, "expected": 1},
        {"input": 5, "expected": 120},
        {"input": 10, "expected": 3628800},
    ],
}


def main():
    parser = argparse.ArgumentParser(
        description="Reflexion: Self-reflective code generation"
    )
    parser.add_argument("--task", type=str, default="fibonacci",
                       choices=list(TEST_SUITES.keys()),
                       help="Task to solve")
    parser.add_argument("--max_iterations", type=int, default=3,
                       help="Maximum refinement iterations")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model to use")
    parser.add_argument("--output", type=str, help="Output JSON file")
    args = parser.parse_args()

    print("=" * 60)
    print("Reflexion: Self-Reflective Code Generation")
    print("=" * 60)
    print(f"Task: {args.task}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Model: {args.model}")
    print()

    # Get test suite
    test_cases = TEST_SUITES[args.task]

    # Initial prompt
    initial_prompt = f"Write a Python function to compute {args.task}."

    # Run reflexion loop
    results = reflexion_loop(
        initial_prompt,
        test_cases,
        max_iterations=args.max_iterations,
        model=args.model
    )

    # Print results
    print("Results:")
    print("-" * 60)
    for result in results:
        print(f"\nIteration {result.iteration}:")
        print(f"  Tests Passed: {result.test_passed}")
        if result.execution_time_ms:
            print(f"  Execution Time: {result.execution_time_ms:.2f}ms")
        if result.error_message:
            print(f"  Error: {result.error_message[:100]}...")
        if result.reflection:
            print(f"  Reflection: {result.reflection[:200]}...")

    # Final code
    final_result = results[-1]
    print()
    print("Final Code:")
    print("-" * 60)
    print(final_result.code)
    print("-" * 60)

    # Summary
    print()
    print("Summary:")
    print(f"  Iterations: {len(results)}")
    print(f"  Success: {final_result.test_passed}")
    print(f"  Final Time: {final_result.execution_time_ms:.2f}ms" if final_result.execution_time_ms else "  Final Time: N/A")
    print("=" * 60)

    # Save results
    if args.output:
        output_data = {
            "task": args.task,
            "max_iterations": args.max_iterations,
            "results": [
                {
                    "iteration": r.iteration,
                    "test_passed": r.test_passed,
                    "error_message": r.error_message,
                    "execution_time_ms": r.execution_time_ms,
                    "code_length": len(r.code),
                    "has_reflection": r.reflection is not None
                }
                for r in results
            ],
            "final_code": final_result.code,
            "success": final_result.test_passed
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
