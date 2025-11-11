#!/usr/bin/env python3
"""
Tree-of-Thoughts Search Implementation
Chapter 1: Foundations of Prompt & Context Engineering

This lab implements Tree-of-Thoughts (ToT) search for the Game of 24.

Game of 24: Given 4 numbers, use +, -, *, / to make 24.
Example: 4, 6, 8, 9 → (9 - 4) * 6 - 8 = 24? No. Try: (6 - (4 / 8)) * 9 = wait...
Correct: (9 - (8 - 6)) * 4 = (9 - 2) * 4 = 7 * 4 = 28? No...
Actually: 8 / (9 - 6 / 4)?  Wait: (8 + 9 - 6) * 4 = 44? No.
Solution: 6 / (1 - 9/8) = 6 / (1 - 1.125) = 6 / (-0.125) = -48? Wrong.
True solution: (8 - 4) * 6 = 24 ✓

Usage:
    python tot_search.py --numbers 4 6 8 9 --breadth 3 --depth 4
"""

import argparse
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import heapq


@dataclass
class ThoughtNode:
    """Node in the thought tree."""
    state: str
    path: List[str] = field(default_factory=list)
    value: float = 0.0
    depth: int = 0

    def __lt__(self, other):
        """For priority queue: higher value = higher priority."""
        return self.value > other.value


def generate_thoughts(state: str, numbers: List[float], n: int = 3) -> List[str]:
    """
    Generate n possible next thoughts (operations).

    In production, use LLM to generate creative operations.
    Here we use deterministic enumeration for reproducibility.
    """
    if len(numbers) == 1:
        return [f"Final result: {numbers[0]}"]

    thoughts = []

    # Try all pairs of numbers with all operations
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            a, b = numbers[i], numbers[j]

            # Addition
            thoughts.append(f"{a} + {b} = {a + b}")

            # Subtraction (both orders)
            thoughts.append(f"{a} - {b} = {a - b}")
            thoughts.append(f"{b} - {a} = {b - a}")

            # Multiplication
            thoughts.append(f"{a} * {b} = {a * b}")

            # Division (both orders, avoid divide by zero)
            if b != 0:
                thoughts.append(f"{a} / {b} = {a / b:.4f}")
            if a != 0:
                thoughts.append(f"{b} / {a} = {b / a:.4f}")

    # Return top n thoughts (in practice, LLM would generate diverse options)
    return thoughts[:n]


def evaluate_thought(thought: str, target: float = 24.0) -> float:
    """
    Evaluate the quality of a thought.

    Heuristic: how close are we to the target?
    In production, use LLM to evaluate thought quality.
    """
    # Extract result from thought
    if "Final result:" in thought:
        try:
            result = float(thought.split("Final result:")[1].strip())
            # Perfect match = 1.0, else inverse distance
            if abs(result - target) < 0.001:
                return 1.0
            else:
                return 1.0 / (1.0 + abs(result - target))
        except:
            return 0.0

    # For intermediate steps, parse operation
    try:
        parts = thought.split("=")
        if len(parts) == 2:
            result = float(parts[1].strip())
            # Prefer results closer to target
            distance = abs(result - target)
            # Also prefer reasonable intermediate values
            if 1 <= result <= 100:
                return 0.5 / (1.0 + distance / target)
            else:
                return 0.1 / (1.0 + distance / target)
    except:
        pass

    return 0.0


def apply_operation(numbers: List[float], thought: str) -> List[float]:
    """Apply an operation and return updated number list."""
    try:
        # Parse operation: "a op b = c"
        parts = thought.split("=")
        if len(parts) != 2:
            return numbers

        result = float(parts[1].strip())

        # Extract operands
        op_part = parts[0].strip()
        for op in ['+', '-', '*', '/']:
            if op in op_part:
                operands = op_part.split(op)
                if len(operands) == 2:
                    a = float(operands[0].strip())
                    b = float(operands[1].strip())

                    # Remove operands and add result
                    new_numbers = [n for n in numbers if abs(n - a) > 0.001 and abs(n - b) > 0.001]
                    new_numbers.append(result)
                    return new_numbers
    except:
        pass

    return numbers


def tree_of_thoughts_bfs(
    initial_numbers: List[float],
    target: float = 24.0,
    breadth: int = 3,
    depth: int = 4
) -> Tuple[Optional[List[str]], List[Dict]]:
    """
    Tree-of-Thoughts search with Breadth-First Search.

    Args:
        initial_numbers: Starting numbers
        target: Target value to reach
        breadth: Number of thoughts to explore at each step
        depth: Maximum search depth

    Returns:
        (solution_path, search_trace)
    """
    initial_state = f"Numbers: {initial_numbers}"
    root = ThoughtNode(state=initial_state, path=[], value=0.0, depth=0)

    # Priority queue (max-heap by value)
    candidates = [root]
    search_trace = []

    for level in range(depth):
        if not candidates:
            break

        next_candidates = []

        for candidate in candidates:
            # Extract current numbers from state
            if candidate.depth == 0:
                current_numbers = initial_numbers[:]
            else:
                # Parse from last thought
                last_thought = candidate.path[-1] if candidate.path else ""
                current_numbers = apply_operation(initial_numbers, last_thought)

            # Check for solution
            if len(current_numbers) == 1 and abs(current_numbers[0] - target) < 0.001:
                search_trace.append({
                    "level": level,
                    "solution_found": True,
                    "path": candidate.path
                })
                return candidate.path, search_trace

            # Generate and evaluate thoughts
            thoughts = generate_thoughts(candidate.state, current_numbers, n=breadth)

            for thought in thoughts:
                value = evaluate_thought(thought, target)
                new_numbers = apply_operation(current_numbers, thought)

                node = ThoughtNode(
                    state=f"Numbers: {new_numbers}",
                    path=candidate.path + [thought],
                    value=value,
                    depth=level + 1
                )
                next_candidates.append(node)

        # Keep top-breadth candidates (beam search)
        next_candidates.sort(key=lambda x: x.value, reverse=True)
        candidates = next_candidates[:breadth]

        search_trace.append({
            "level": level,
            "candidates_explored": len(next_candidates),
            "top_values": [c.value for c in candidates]
        })

    # No solution found
    return None, search_trace


def verify_solution(numbers: List[float], path: List[str], target: float = 24.0) -> bool:
    """Verify that a solution path is correct."""
    current = numbers[:]

    for step in path:
        current = apply_operation(current, step)

    return len(current) == 1 and abs(current[0] - target) < 0.001


def main():
    parser = argparse.ArgumentParser(
        description="Tree-of-Thoughts search for Game of 24"
    )
    parser.add_argument("--numbers", type=float, nargs=4, default=[4.0, 6.0, 8.0, 9.0],
                       help="Four numbers for Game of 24")
    parser.add_argument("--target", type=float, default=24.0, help="Target value")
    parser.add_argument("--breadth", type=int, default=3, help="Search breadth")
    parser.add_argument("--depth", type=int, default=4, help="Search depth")
    parser.add_argument("--output", type=str, help="Output JSON file")
    args = parser.parse_args()

    print("=" * 60)
    print("Tree-of-Thoughts: Game of 24")
    print("=" * 60)
    print(f"Numbers: {args.numbers}")
    print(f"Target: {args.target}")
    print(f"Breadth: {args.breadth}")
    print(f"Depth: {args.depth}")
    print()

    # Run ToT search
    solution, trace = tree_of_thoughts_bfs(
        args.numbers,
        target=args.target,
        breadth=args.breadth,
        depth=args.depth
    )

    # Print results
    if solution:
        print("Solution found!")
        print("-" * 60)
        for i, step in enumerate(solution, 1):
            print(f"Step {i}: {step}")

        # Verify
        is_valid = verify_solution(args.numbers, solution, args.target)
        print()
        print(f"Verification: {'✓ Valid' if is_valid else '✗ Invalid'}")
    else:
        print("No solution found within search constraints.")
        print("Try increasing --breadth or --depth.")

    print()
    print("Search trace:")
    print("-" * 60)
    for entry in trace:
        print(f"Level {entry['level']}: {entry}")

    print("=" * 60)

    # Save results
    if args.output:
        results = {
            "numbers": args.numbers,
            "target": args.target,
            "breadth": args.breadth,
            "depth": args.depth,
            "solution": solution,
            "search_trace": trace
        }
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
