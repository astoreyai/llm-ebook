#!/usr/bin/env python3
"""
llama.cpp Quantization Comparison Lab

This lab compares different GGUF quantization levels for llama.cpp:
- Q8_0: 8-bit quantization
- Q5_K_M: 5-bit (recommended)
- Q4_K_M: 4-bit
- Q3_K_M: 3-bit
- Q2_K: 2-bit (not recommended)

Metrics compared:
- Model size (memory usage)
- Inference speed (tokens/second)
- Quality (accuracy on benchmark tasks)
- Trade-off analysis

Supports both mock mode (simulated) and production mode (requires llama.cpp).

Usage:
    # Mock mode (default)
    python quantization_comparison.py --model llama-2-7b

    # Production mode (requires llama.cpp server)
    python quantization_comparison.py --model llama-2-7b --production --base-path /path/to/models

References:
    Dettmers et al. (2023): "GPT3.int8(): 8-bit Matrix Multiplication for Transformers at Scale"
    llama.cpp benchmarks: https://github.com/ggerganov/llama.cpp
"""

import argparse
import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import numpy as np


@dataclass
class QuantizationLevel:
    """Quantization configuration."""
    name: str
    bits: float
    memory_gb: float  # For 7B model
    relative_speed: float  # Relative to F16 (1.0 = same speed)
    quality_degradation_pp: float  # Percentage points loss on MMLU


@dataclass
class BenchmarkTask:
    """Single benchmark task."""
    id: int
    prompt: str
    expected_answer: str
    category: str


@dataclass
class QuantizationResult:
    """Result for a quantization level."""
    quantization: str
    bits: float
    memory_gb: float
    tokens_per_second: float
    accuracy: float
    latency_ms: float
    quality_score: float  # 0-1, relative to F16


# Quantization levels (data from Chapter 4)
QUANTIZATION_LEVELS = {
    "F16": QuantizationLevel("F16", 16, 14.0, 1.0, 0.0),
    "Q8_0": QuantizationLevel("Q8_0", 8, 7.5, 1.5, 0.5),
    "Q5_K_M": QuantizationLevel("Q5_K_M", 5, 5.2, 2.0, 1.2),
    "Q4_K_M": QuantizationLevel("Q4_K_M", 4, 4.4, 2.5, 2.5),
    "Q3_K_M": QuantizationLevel("Q3_K_M", 3, 3.8, 2.8, 5.0),
    "Q2_K": QuantizationLevel("Q2_K", 2, 3.1, 3.0, 12.0),
}


# =============================================================================
# Mock llama.cpp Client
# =============================================================================

class MockLlamaCppClient:
    """Mock llama.cpp client for quantization comparison."""

    def __init__(self, model: str, quantization: str):
        self.model = model
        self.quantization = quantization
        self.quant_config = QUANTIZATION_LEVELS[quantization]

    def _deterministic_answer(self, prompt: str) -> Tuple[str, float]:
        """Generate deterministic answer based on prompt hash."""
        hash_val = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)
        np.random.seed(hash_val % 2**32)

        # Simulate quality degradation
        # Higher quality = higher chance of correct answer
        quality_factor = 1.0 - (self.quant_config.quality_degradation_pp / 100.0)
        is_correct = np.random.random() < quality_factor

        # Simple mock answer
        if is_correct:
            answer = "correct_answer"
        else:
            answer = "incorrect_answer"

        # Latency based on quantization speed
        base_latency_ms = 100.0
        latency = base_latency_ms / self.quant_config.relative_speed

        return answer, latency

    def generate(self, prompt: str, max_tokens: int = 50) -> Dict:
        """Mock generation."""
        answer, latency = self._deterministic_answer(prompt)

        # Simulate latency
        time.sleep(latency / 1000.0)

        tokens_per_second = (
            max_tokens / (latency / 1000.0) * self.quant_config.relative_speed
        )

        return {
            "text": answer,
            "latency_ms": latency,
            "tokens_per_second": tokens_per_second,
            "memory_gb": self.quant_config.memory_gb,
        }


# =============================================================================
# Production llama.cpp Client
# =============================================================================

class ProductionLlamaCppClient:
    """Production llama.cpp client."""

    def __init__(self, model: str, quantization: str, base_url: str = "http://localhost:8080"):
        try:
            import requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")

        self.model = model
        self.quantization = quantization
        self.base_url = base_url
        self.session = requests.Session()

    def generate(self, prompt: str, max_tokens: int = 50) -> Dict:
        """Generate using llama.cpp server."""
        start_time = time.time()

        response = self.session.post(
            f"{self.base_url}/completion",
            json={
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": 0.7,
            },
        )

        response.raise_for_status()
        result = response.json()

        latency = (time.time() - start_time) * 1000  # ms
        tokens_per_second = max_tokens / (latency / 1000.0)

        return {
            "text": result.get("content", ""),
            "latency_ms": latency,
            "tokens_per_second": tokens_per_second,
            "memory_gb": QUANTIZATION_LEVELS[self.quantization].memory_gb,
        }


# =============================================================================
# Benchmark Tasks
# =============================================================================

def create_benchmark_tasks() -> List[BenchmarkTask]:
    """Create benchmark tasks (MMLU-style)."""
    tasks = [
        BenchmarkTask(
            1,
            "What is the capital of France? A) London B) Berlin C) Paris D) Madrid",
            "C",
            "geography",
        ),
        BenchmarkTask(
            2,
            "What is 2 + 2? A) 3 B) 4 C) 5 D) 6",
            "B",
            "math",
        ),
        BenchmarkTask(
            3,
            "Who wrote Romeo and Juliet? A) Dickens B) Shakespeare C) Austen D) Orwell",
            "B",
            "literature",
        ),
        BenchmarkTask(
            4,
            "What is the chemical symbol for water? A) H2O B) CO2 C) O2 D) N2",
            "A",
            "science",
        ),
        BenchmarkTask(
            5,
            "What is the speed of light? A) 3×10^8 m/s B) 3×10^6 m/s C) 3×10^4 m/s D) 3×10^2 m/s",
            "A",
            "physics",
        ),
        BenchmarkTask(
            6,
            "What is the largest planet in our solar system? A) Earth B) Mars C) Jupiter D) Saturn",
            "C",
            "astronomy",
        ),
        BenchmarkTask(
            7,
            "What is the square root of 144? A) 10 B) 11 C) 12 D) 13",
            "C",
            "math",
        ),
        BenchmarkTask(
            8,
            "Which language is spoken in Brazil? A) Spanish B) Portuguese C) French D) Italian",
            "B",
            "geography",
        ),
        BenchmarkTask(
            9,
            "What year did World War II end? A) 1943 B) 1944 C) 1945 D) 1946",
            "C",
            "history",
        ),
        BenchmarkTask(
            10,
            "What is the smallest prime number? A) 0 B) 1 C) 2 D) 3",
            "C",
            "math",
        ),
    ]
    return tasks


# =============================================================================
# Quantization Benchmark
# =============================================================================

class QuantizationBenchmark:
    """Benchmark for quantization comparison."""

    def __init__(self, model: str, production: bool = False, base_url: str = None):
        self.model = model
        self.production = production
        self.base_url = base_url or "http://localhost:8080"
        self.tasks = create_benchmark_tasks()

    def run_quantization(self, quantization: str) -> QuantizationResult:
        """Benchmark single quantization level."""
        print(f"\n  Testing {quantization}...")

        if self.production:
            client = ProductionLlamaCppClient(self.model, quantization, self.base_url)
        else:
            client = MockLlamaCppClient(self.model, quantization)

        correct = 0
        total_latency = 0
        total_tokens_per_sec = 0

        for task in self.tasks:
            result = client.generate(task.prompt, max_tokens=50)

            # Check if answer is correct (simplified - just check for presence)
            if task.expected_answer.lower() in result["text"].lower():
                correct += 1

            total_latency += result["latency_ms"]
            total_tokens_per_sec += result["tokens_per_second"]

        accuracy = correct / len(self.tasks)
        avg_latency = total_latency / len(self.tasks)
        avg_tokens_per_sec = total_tokens_per_sec / len(self.tasks)

        # Quality score relative to F16 baseline
        quant_config = QUANTIZATION_LEVELS[quantization]
        quality_score = 1.0 - (quant_config.quality_degradation_pp / 100.0)

        return QuantizationResult(
            quantization=quantization,
            bits=quant_config.bits,
            memory_gb=quant_config.memory_gb,
            tokens_per_second=avg_tokens_per_sec,
            accuracy=accuracy,
            latency_ms=avg_latency,
            quality_score=quality_score,
        )

    def run_comparison(
        self, quantizations: List[str] = None
    ) -> List[QuantizationResult]:
        """Run full quantization comparison."""
        if quantizations is None:
            quantizations = ["F16", "Q8_0", "Q5_K_M", "Q4_K_M", "Q3_K_M", "Q2_K"]

        print(f"\n{'='*70}")
        print(f"llama.cpp Quantization Comparison")
        print(f"{'='*70}")
        print(f"Model: {self.model}")
        print(f"Mode: {'Production' if self.production else 'Mock'}")
        print(f"Benchmark tasks: {len(self.tasks)}")
        print(f"Quantizations to test: {', '.join(quantizations)}")
        print(f"{'='*70}\n")

        results = []
        for quant in quantizations:
            result = self.run_quantization(quant)
            results.append(result)

        return results

    def print_results(self, results: List[QuantizationResult]):
        """Print comparison results."""
        print(f"\n{'='*70}")
        print(f"Quantization Comparison Results")
        print(f"{'='*70}\n")

        # Table header
        print(f"{'Quant':<10} {'Bits':<6} {'Memory':<10} {'Speed':<12} {'Accuracy':<10} {'Quality':<10}")
        print(f"{'':=<10} {'':=<6} {'':=<10} {'':=<12} {'':=<10} {'':=<10}")

        # Table rows
        for r in results:
            print(
                f"{r.quantization:<10} "
                f"{r.bits:<6.1f} "
                f"{r.memory_gb:<10.1f} "
                f"{r.tokens_per_second:<12.1f} "
                f"{r.accuracy:<10.2%} "
                f"{r.quality_score:<10.2%}"
            )

        print(f"\n{'='*70}\n")

        # Recommendations
        self._print_recommendations(results)

        # Trade-off analysis
        self._print_tradeoff_analysis(results)

    def _print_recommendations(self, results: List[QuantizationResult]):
        """Print quantization recommendations."""
        print("Recommendations:")
        print("-" * 70)

        # Find Q5_K_M (recommended)
        q5_result = next((r for r in results if r.quantization == "Q5_K_M"), None)
        if q5_result:
            print(f"\n✓ RECOMMENDED: Q5_K_M")
            print(f"  - Memory: {q5_result.memory_gb:.1f} GB (63% reduction vs F16)")
            print(f"  - Speed: {q5_result.tokens_per_second:.1f} tok/s (2× faster)")
            print(f"  - Quality: {q5_result.quality_score:.1%} (only 1.2pp loss)")
            print(f"  - Best balance of size, speed, and quality")

        # Find Q4_K_M (resource-constrained)
        q4_result = next((r for r in results if r.quantization == "Q4_K_M"), None)
        if q4_result:
            print(f"\n○ ALTERNATIVE: Q4_K_M (if memory-constrained)")
            print(f"  - Memory: {q4_result.memory_gb:.1f} GB (69% reduction)")
            print(f"  - Speed: {q4_result.tokens_per_second:.1f} tok/s (2.5× faster)")
            print(f"  - Quality: {q4_result.quality_score:.1%} (2.5pp loss)")
            print(f"  - Use when: <8GB VRAM available")

        # Warning for Q2_K
        q2_result = next((r for r in results if r.quantization == "Q2_K"), None)
        if q2_result:
            print(f"\n✗ NOT RECOMMENDED: Q2_K")
            print(f"  - Quality: {q2_result.quality_score:.1%} (12pp loss - too high)")
            print(f"  - Only use for: Experimentation or extreme constraints")

        print(f"\n{'='*70}\n")

    def _print_tradeoff_analysis(self, results: List[QuantizationResult]):
        """Print trade-off analysis."""
        print("Trade-off Analysis:")
        print("-" * 70)

        # Find baseline (F16)
        baseline = next((r for r in results if r.quantization == "F16"), None)
        if not baseline:
            print("Note: F16 baseline not available for comparison")
            return

        print(f"\nCompared to F16 baseline:")
        print(f"{'Quant':<10} {'Memory Saved':<15} {'Speed Gain':<15} {'Quality Loss':<15}")
        print(f"{'':=<10} {'':=<15} {'':=<15} {'':=<15}")

        for r in results:
            if r.quantization == "F16":
                continue

            memory_saved = ((baseline.memory_gb - r.memory_gb) / baseline.memory_gb) * 100
            speed_gain = ((r.tokens_per_second - baseline.tokens_per_second) / baseline.tokens_per_second) * 100
            quality_loss = (baseline.quality_score - r.quality_score) * 100

            print(
                f"{r.quantization:<10} "
                f"{memory_saved:>13.1f}% "
                f"{speed_gain:>13.1f}% "
                f"{quality_loss:>13.1f}pp"
            )

        print(f"\n{'='*70}\n")

        # Efficiency score (simple heuristic)
        print("Efficiency Score (higher = better overall trade-off):")
        print("-" * 70)

        for r in results:
            # Score = speed_gain + memory_saved - 5*quality_loss
            memory_saved = ((baseline.memory_gb - r.memory_gb) / baseline.memory_gb) * 100
            speed_gain = ((r.tokens_per_second - baseline.tokens_per_second) / baseline.tokens_per_second) * 100
            quality_loss = (baseline.quality_score - r.quality_score) * 100

            efficiency = speed_gain + memory_saved - (5 * quality_loss)

            print(f"  {r.quantization:<10} Score: {efficiency:>6.1f}")

        print(f"\n{'='*70}\n")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="llama.cpp Quantization Comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mock mode (no llama.cpp required)
  python quantization_comparison.py --model llama-2-7b

  # Production mode (requires llama.cpp server with multiple quantized models)
  python quantization_comparison.py --model llama-2-7b --production

  # Test specific quantizations
  python quantization_comparison.py --quantizations Q8_0 Q5_K_M Q4_K_M

  # Save results to JSON
  python quantization_comparison.py --model llama-2-7b --output quant_results.json
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default="llama-2-7b",
        help="Model name (default: llama-2-7b)",
    )
    parser.add_argument(
        "--quantizations",
        nargs="+",
        default=None,
        choices=list(QUANTIZATION_LEVELS.keys()),
        help="Quantization levels to test (default: all)",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production llama.cpp server",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8080",
        help="llama.cpp server URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file",
    )

    args = parser.parse_args()

    # Initialize benchmark
    benchmark = QuantizationBenchmark(
        model=args.model,
        production=args.production,
        base_url=args.base_url,
    )

    # Run comparison
    results = benchmark.run_comparison(quantizations=args.quantizations)

    # Print results
    benchmark.print_results(results)

    # Save to JSON if requested
    if args.output:
        output_data = {
            "model": args.model,
            "production": args.production,
            "results": [asdict(r) for r in results],
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Results saved to: {args.output}\n")


if __name__ == "__main__":
    main()
