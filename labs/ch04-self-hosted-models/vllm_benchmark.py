#!/usr/bin/env python3
"""
vLLM Performance Benchmarking Lab

This lab demonstrates how to benchmark vLLM performance including:
- Throughput (requests/second, tokens/second)
- Latency (p50, p90, p99)
- GPU utilization
- Memory efficiency

Supports both mock mode (no vLLM required) and production mode.

Usage:
    # Mock mode (default)
    python vllm_benchmark.py --model mistralai/Mistral-7B-Instruct-v0.2 --num-requests 100

    # Production mode (requires vLLM)
    python vllm_benchmark.py --model mistralai/Mistral-7B-Instruct-v0.2 --num-requests 1000 --production

References:
    Kwon et al. (2023): "Efficient Memory Management for Large Language Model Serving with PagedAttention"
"""

import argparse
import time
import json
import hashlib
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from datetime import datetime


@dataclass
class BenchmarkRequest:
    """Single benchmark request."""
    id: int
    prompt: str
    input_tokens: int
    output_tokens: int


@dataclass
class BenchmarkResult:
    """Result for a single request."""
    request_id: int
    input_tokens: int
    output_tokens: int
    latency_ms: float
    time_to_first_token_ms: float
    tokens_per_second: float
    success: bool
    error: str = ""


@dataclass
class BenchmarkSummary:
    """Aggregate benchmark statistics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_time_seconds: float
    requests_per_second: float
    tokens_per_second: float
    latency_p50_ms: float
    latency_p90_ms: float
    latency_p99_ms: float
    ttft_p50_ms: float  # Time to first token
    ttft_p90_ms: float
    ttft_p99_ms: float


# =============================================================================
# Mock vLLM Client (for demonstration without vLLM installation)
# =============================================================================

class MockVLLMClient:
    """Mock vLLM client for benchmarking without actual vLLM deployment."""

    def __init__(self, model: str, base_url: str = "http://localhost:8000"):
        self.model = model
        self.base_url = base_url
        # Simulate realistic latencies based on model size
        self.base_latency_ms = 50 if "7B" in model or "7b" in model else 100
        self.tokens_per_second = 80 if "7B" in model or "7b" in model else 45

    def _deterministic_latency(self, prompt: str, max_tokens: int) -> Tuple[float, float]:
        """Calculate deterministic latency based on input."""
        # Hash prompt to get reproducible pseudo-random values
        hash_val = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)
        np.random.seed(hash_val % 2**32)

        # Time to first token: base latency + variance
        ttft = self.base_latency_ms + np.random.uniform(-10, 30)

        # Generation time: tokens / throughput
        generation_time_ms = (max_tokens / self.tokens_per_second) * 1000

        # Total latency with some jitter
        total_latency = ttft + generation_time_ms + np.random.uniform(0, 20)

        return total_latency, ttft

    def generate(self, prompt: str, max_tokens: int = 128, **kwargs) -> Dict:
        """Mock generation."""
        total_latency, ttft = self._deterministic_latency(prompt, max_tokens)

        # Simulate actual latency (for timing measurements)
        time.sleep(total_latency / 1000.0)

        # Count input tokens (rough estimate: 4 chars/token)
        input_tokens = len(prompt) // 4

        return {
            "text": "Mock response " * (max_tokens // 2),
            "input_tokens": input_tokens,
            "output_tokens": max_tokens,
            "latency_ms": total_latency,
            "ttft_ms": ttft,
        }


# =============================================================================
# Production vLLM Client (requires vLLM server running)
# =============================================================================

class ProductionVLLMClient:
    """Production vLLM client using OpenAI-compatible API."""

    def __init__(self, model: str, base_url: str = "http://localhost:8000"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI Python client required for production mode. "
                "Install with: pip install openai"
            )

        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-required")
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 128, **kwargs) -> Dict:
        """Generate using vLLM OpenAI-compatible API."""
        start_time = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=kwargs.get("temperature", 0.7),
        )

        total_latency = (time.time() - start_time) * 1000  # ms

        return {
            "text": response.choices[0].message.content,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "latency_ms": total_latency,
            "ttft_ms": total_latency * 0.2,  # Estimate (real vLLM would stream)
        }


# =============================================================================
# Benchmark Runner
# =============================================================================

class VLLMBenchmark:
    """vLLM benchmark harness."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000",
        production: bool = False,
    ):
        if production:
            self.client = ProductionVLLMClient(model, base_url)
        else:
            self.client = MockVLLMClient(model, base_url)

        self.model = model
        self.production = production

    def generate_requests(
        self,
        num_requests: int,
        input_tokens: int = 512,
        output_tokens: int = 128,
    ) -> List[BenchmarkRequest]:
        """Generate benchmark requests."""
        requests = []
        for i in range(num_requests):
            # Generate prompt of approximately input_tokens length
            # ~4 characters per token
            prompt_text = f"Request {i}: " + "word " * (input_tokens // 4)

            requests.append(
                BenchmarkRequest(
                    id=i,
                    prompt=prompt_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )

        return requests

    def run_single_request(self, request: BenchmarkRequest) -> BenchmarkResult:
        """Execute single benchmark request."""
        try:
            start_time = time.time()
            result = self.client.generate(
                request.prompt, max_tokens=request.output_tokens
            )
            elapsed_time = (time.time() - start_time) * 1000  # ms

            return BenchmarkResult(
                request_id=request.id,
                input_tokens=result["input_tokens"],
                output_tokens=result["output_tokens"],
                latency_ms=result["latency_ms"],
                time_to_first_token_ms=result["ttft_ms"],
                tokens_per_second=(
                    result["output_tokens"] / (result["latency_ms"] / 1000.0)
                ),
                success=True,
            )

        except Exception as e:
            return BenchmarkResult(
                request_id=request.id,
                input_tokens=request.input_tokens,
                output_tokens=request.output_tokens,
                latency_ms=0,
                time_to_first_token_ms=0,
                tokens_per_second=0,
                success=False,
                error=str(e),
            )

    def run_benchmark(
        self,
        num_requests: int,
        input_tokens: int = 512,
        output_tokens: int = 128,
        concurrent: bool = False,
    ) -> Tuple[List[BenchmarkResult], BenchmarkSummary]:
        """Run full benchmark."""
        print(f"\n{'='*70}")
        print(f"vLLM Performance Benchmark")
        print(f"{'='*70}")
        print(f"Model: {self.model}")
        print(f"Mode: {'Production' if self.production else 'Mock'}")
        print(f"Requests: {num_requests}")
        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Concurrency: {'Enabled' if concurrent else 'Sequential'}")
        print(f"{'='*70}\n")

        requests = self.generate_requests(num_requests, input_tokens, output_tokens)

        results = []
        start_time = time.time()

        if concurrent:
            # Concurrent execution (simplified - real implementation would use asyncio)
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(self.run_single_request, requests))
        else:
            # Sequential execution
            for i, request in enumerate(requests):
                result = self.run_single_request(request)
                results.append(result)

                if (i + 1) % 10 == 0 or (i + 1) == num_requests:
                    print(f"  Progress: {i+1}/{num_requests} requests completed")

        total_time = time.time() - start_time

        # Compute summary statistics
        summary = self._compute_summary(results, total_time)

        return results, summary

    def _compute_summary(
        self, results: List[BenchmarkResult], total_time: float
    ) -> BenchmarkSummary:
        """Compute aggregate statistics."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if not successful:
            raise ValueError("All requests failed!")

        latencies = [r.latency_ms for r in successful]
        ttfts = [r.time_to_first_token_ms for r in successful]

        total_input_tokens = sum(r.input_tokens for r in successful)
        total_output_tokens = sum(r.output_tokens for r in successful)
        total_tokens = total_input_tokens + total_output_tokens

        return BenchmarkSummary(
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_time_seconds=total_time,
            requests_per_second=len(successful) / total_time,
            tokens_per_second=total_tokens / total_time,
            latency_p50_ms=float(np.percentile(latencies, 50)),
            latency_p90_ms=float(np.percentile(latencies, 90)),
            latency_p99_ms=float(np.percentile(latencies, 99)),
            ttft_p50_ms=float(np.percentile(ttfts, 50)),
            ttft_p90_ms=float(np.percentile(ttfts, 90)),
            ttft_p99_ms=float(np.percentile(ttfts, 99)),
        )

    def print_summary(self, summary: BenchmarkSummary):
        """Print benchmark summary."""
        print(f"\n{'='*70}")
        print(f"Benchmark Results")
        print(f"{'='*70}\n")

        print(f"Requests:")
        print(f"  Total:      {summary.total_requests}")
        print(f"  Successful: {summary.successful_requests}")
        print(f"  Failed:     {summary.failed_requests}")

        print(f"\nTokens:")
        print(f"  Input:      {summary.total_input_tokens:,}")
        print(f"  Output:     {summary.total_output_tokens:,}")
        print(f"  Total:      {summary.total_input_tokens + summary.total_output_tokens:,}")

        print(f"\nThroughput:")
        print(f"  Requests/sec: {summary.requests_per_second:.2f}")
        print(f"  Tokens/sec:   {summary.tokens_per_second:.2f}")

        print(f"\nLatency (ms):")
        print(f"  p50: {summary.latency_p50_ms:.1f}")
        print(f"  p90: {summary.latency_p90_ms:.1f}")
        print(f"  p99: {summary.latency_p99_ms:.1f}")

        print(f"\nTime to First Token (ms):")
        print(f"  p50: {summary.ttft_p50_ms:.1f}")
        print(f"  p90: {summary.ttft_p90_ms:.1f}")
        print(f"  p99: {summary.ttft_p99_ms:.1f}")

        print(f"\nTotal Time: {summary.total_time_seconds:.2f} seconds")
        print(f"{'='*70}\n")

        # Performance assessment
        self._assess_performance(summary)

    def _assess_performance(self, summary: BenchmarkSummary):
        """Provide performance assessment."""
        print("Performance Assessment:")
        print("-" * 70)

        # Expected performance for 7B model on A100 (from Chapter 4)
        expected_throughput = 18  # req/s
        expected_p99_latency = 85  # ms

        if "7B" in self.model or "7b" in self.model:
            if summary.requests_per_second >= expected_throughput * 0.8:
                print(f"✓ Throughput: GOOD ({summary.requests_per_second:.1f} req/s)")
                print(f"  Target: {expected_throughput} req/s for 7B on A100")
            else:
                print(f"⚠ Throughput: LOW ({summary.requests_per_second:.1f} req/s)")
                print(f"  Expected: ~{expected_throughput} req/s for 7B on A100")
                print(f"  Suggestions: Check GPU utilization, increase batch size")

            if summary.latency_p99_ms <= expected_p99_latency * 1.2:
                print(f"\n✓ Latency: GOOD (p99: {summary.latency_p99_ms:.1f} ms)")
                print(f"  Target: <{expected_p99_latency} ms for 7B on A100")
            else:
                print(f"\n⚠ Latency: HIGH (p99: {summary.latency_p99_ms:.1f} ms)")
                print(f"  Expected: ~{expected_p99_latency} ms for 7B on A100")
                print(f"  Suggestions: Reduce max_model_len, check GPU contention")

        print(f"\n{'='*70}\n")


# =============================================================================
# Main Benchmark Execution
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="vLLM Performance Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mock mode (no vLLM required)
  python vllm_benchmark.py --model mistralai/Mistral-7B-Instruct-v0.2 --num-requests 100

  # Production mode (requires vLLM server running)
  python vllm_benchmark.py --model mistralai/Mistral-7B-Instruct-v0.2 --num-requests 1000 --production

  # Custom input/output lengths
  python vllm_benchmark.py --num-requests 50 --input-tokens 2048 --output-tokens 256

  # Save results to JSON
  python vllm_benchmark.py --num-requests 100 --output results.json
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.2",
        help="Model name (default: Mistral 7B)",
    )
    parser.add_argument(
        "--num-requests",
        type=int,
        default=100,
        help="Number of requests to benchmark (default: 100)",
    )
    parser.add_argument(
        "--input-tokens",
        type=int,
        default=512,
        help="Input tokens per request (default: 512)",
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=128,
        help="Output tokens per request (default: 128)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="vLLM server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production vLLM server (requires --base-url)",
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Run requests concurrently (default: sequential)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file",
    )

    args = parser.parse_args()

    # Initialize benchmark
    benchmark = VLLMBenchmark(
        model=args.model,
        base_url=args.base_url,
        production=args.production,
    )

    # Run benchmark
    results, summary = benchmark.run_benchmark(
        num_requests=args.num_requests,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        concurrent=args.concurrent,
    )

    # Print results
    benchmark.print_summary(summary)

    # Save to JSON if requested
    if args.output:
        output_data = {
            "benchmark_info": {
                "model": args.model,
                "production": args.production,
                "timestamp": datetime.now().isoformat(),
            },
            "summary": asdict(summary),
            "results": [asdict(r) for r in results],
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Results saved to: {args.output}\n")


if __name__ == "__main__":
    main()
