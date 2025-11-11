# Chapter 4 Labs: Self-Hosted Models

This directory contains runnable labs for Chapter 4 demonstrating self-hosted LLM deployment and benchmarking.

## Labs Overview

### 1. vLLM Performance Benchmark (`vllm_benchmark.py`)

Comprehensive benchmarking harness for vLLM deployment measuring throughput, latency, and performance characteristics.

**Run:**
```bash
# Mock mode (no vLLM required)
python vllm_benchmark.py --model mistralai/Mistral-7B-Instruct-v0.2 --num-requests 100

# Production mode (requires vLLM server running)
python vllm_benchmark.py --model mistralai/Mistral-7B-Instruct-v0.2 --num-requests 1000 --production --base-url http://localhost:8000

# Save results to JSON
python vllm_benchmark.py --num-requests 100 --output vllm_results.json
```

**Expected Output:**
```
======================================================================
vLLM Performance Benchmark
======================================================================
Model: mistralai/Mistral-7B-Instruct-v0.2
Mode: Mock
Requests: 100
Input tokens: 512
Output tokens: 128
Concurrency: Sequential
======================================================================

  Progress: 10/100 requests completed
  Progress: 20/100 requests completed
  ...
  Progress: 100/100 requests completed

======================================================================
Benchmark Results
======================================================================

Requests:
  Total:      100
  Successful: 100
  Failed:     0

Tokens:
  Input:      51,200
  Output:     12,800
  Total:      64,000

Throughput:
  Requests/sec: 18.52
  Tokens/sec:   1184.32

Latency (ms):
  p50: 48.2
  p90: 72.5
  p99: 85.1

Time to First Token (ms):
  p50: 52.3
  p90: 68.7
  p99: 79.2

Total Time: 5.40 seconds
======================================================================

Performance Assessment:
----------------------------------------------------------------------
✓ Throughput: GOOD (18.5 req/s)
  Target: 18 req/s for 7B on A100

✓ Latency: GOOD (p99: 85.1 ms)
  Target: <85 ms for 7B on A100

======================================================================
```

**Key Metrics:**
- **Throughput**: Requests/second and tokens/second
- **Latency**: p50, p90, p99 latencies
- **TTFT**: Time to first token (streaming)
- **Success rate**: Failed vs successful requests

**Production Setup:**

To test with real vLLM server:

```bash
# 1. Install vLLM
pip install vllm==0.2.7

# 2. Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90

# 3. Run benchmark (in another terminal)
python vllm_benchmark.py --production --num-requests 1000
```

**Expected Performance (single NVIDIA A100 80GB):**

| Model Size | Input Tokens | Output Tokens | Throughput (req/s) | Latency p99 (ms) |
|------------|--------------|---------------|-------------------|------------------|
| 7B | 512 | 128 | 18-22 | 85 |
| 7B | 2048 | 256 | 8-12 | 220 |
| 13B | 512 | 128 | 9-12 | 165 |

---

### 2. Quantization Comparison (`quantization_comparison.py`)

Compares different GGUF quantization levels (Q8, Q5, Q4, Q3, Q2) for llama.cpp on memory, speed, and quality trade-offs.

**Run:**
```bash
# Mock mode (no llama.cpp required)
python quantization_comparison.py --model llama-2-7b

# Test specific quantizations
python quantization_comparison.py --quantizations Q8_0 Q5_K_M Q4_K_M

# Save results to JSON
python quantization_comparison.py --output quant_results.json
```

**Expected Output:**
```
======================================================================
llama.cpp Quantization Comparison
======================================================================
Model: llama-2-7b
Mode: Mock
Benchmark tasks: 10
Quantizations to test: F16, Q8_0, Q5_K_M, Q4_K_M, Q3_K_M, Q2_K
======================================================================

  Testing F16...
  Testing Q8_0...
  Testing Q5_K_M...
  Testing Q4_K_M...
  Testing Q3_K_M...
  Testing Q2_K...

======================================================================
Quantization Comparison Results
======================================================================

Quant      Bits   Memory     Speed        Accuracy   Quality
========== ====== ========== ============ ========== ==========
F16        16.0   14.0       25.0         100.00%    100.00%
Q8_0       8.0    7.5        37.5         99.50%     99.50%
Q5_K_M     5.0    5.2        50.0         98.80%     98.80%
Q4_K_M     4.0    4.4        62.5         97.50%     97.50%
Q3_K_M     3.0    3.8        70.0         95.00%     95.00%
Q2_K       2.0    3.1        75.0         88.00%     88.00%

======================================================================

Recommendations:
----------------------------------------------------------------------

✓ RECOMMENDED: Q5_K_M
  - Memory: 5.2 GB (63% reduction vs F16)
  - Speed: 50.0 tok/s (2× faster)
  - Quality: 98.8% (only 1.2pp loss)
  - Best balance of size, speed, and quality

○ ALTERNATIVE: Q4_K_M (if memory-constrained)
  - Memory: 4.4 GB (69% reduction)
  - Speed: 62.5 tok/s (2.5× faster)
  - Quality: 97.5% (2.5pp loss)
  - Use when: <8GB VRAM available

✗ NOT RECOMMENDED: Q2_K
  - Quality: 88.0% (12pp loss - too high)
  - Only use for: Experimentation or extreme constraints

======================================================================

Trade-off Analysis:
----------------------------------------------------------------------

Compared to F16 baseline:
Quant      Memory Saved    Speed Gain      Quality Loss
========== =============== =============== ===============
Q8_0              46.4%           50.0%            0.5pp
Q5_K_M            62.9%          100.0%            1.2pp
Q4_K_M            68.6%          150.0%            2.5pp
Q3_K_M            72.9%          180.0%            5.0pp
Q2_K              77.9%          200.0%           12.0pp

======================================================================

Efficiency Score (higher = better overall trade-off):
----------------------------------------------------------------------
  F16        Score:    0.0
  Q8_0       Score:   93.9
  Q5_K_M     Score:  156.9  ⭐ Best
  Q4_K_M     Score:  206.1
  Q3_K_M     Score:  225.7
  Q2_K       Score:  217.9

======================================================================
```

**Key Findings:**

1. **Q5_K_M is optimal**: 2× speed, 63% memory reduction, only 1.2pp quality loss
2. **Q4_K_M for constrained environments**: Use when <8GB VRAM
3. **Avoid Q2_K**: 12pp quality loss is too severe for most applications

**Production Setup:**

To test with real llama.cpp:

```bash
# 1. Build llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make -j$(nproc)

# Optional: CUDA support
make LLAMA_CUBLAS=1 -j$(nproc)

# 2. Download quantized models (example: Mistral 7B)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf

# 3. Start server
./server --model mistral-7b-instruct-v0.2.Q5_K_M.gguf --port 8080

# 4. Run benchmark (in another terminal)
python quantization_comparison.py --production --model mistral-7b
```

**Hardware Performance:**

| Hardware | Model | Quantization | Tokens/sec | Latency (first token) |
|----------|-------|--------------|------------|-----------------------|
| MacBook Pro M2 Max | Llama 2 7B | Q5_K_M | 25-30 | 150ms |
| MacBook Pro M3 Max | Llama 2 7B | Q5_K_M | 35-45 | 100ms |
| AMD Ryzen 9 5950X (16C) | Llama 2 7B | Q5_K_M | 15-20 | 250ms |
| RTX 4090 (24GB) | Llama 2 7B | Q5_K_M | 80-100 | 50ms |
| RTX 4090 (24GB) | Llama 2 13B | Q5_K_M | 45-55 | 80ms |

---

### 3. TCO Calculator (`tco_calculator.py`)

Calculate Total Cost of Ownership for self-hosted vs commercial API deployment with break-even analysis.

**Run:**
```bash
# Basic calculation (500M tokens/month)
python tco_calculator.py --tokens-per-month 500M

# High-volume scenario (10B tokens/month)
python tco_calculator.py --tokens-per-month 10B --hardware datacenter_a100_dual

# Compare deployment types
python tco_calculator.py --tokens-per-month 1B --deployment colocation

# Multi-scenario analysis
python tco_calculator.py --scenario-analysis

# Save report
python tco_calculator.py --tokens-per-month 5B --output tco_report.json
```

**Expected Output:**
```
======================================================================
Total Cost of Ownership (TCO) Analysis
======================================================================

Scenario: cloud-Datacenter 1× A100
Usage: 10,000,000,000 tokens/month
        (10.00B tokens/month)

----------------------------------------------------------------------
Commercial API Costs
----------------------------------------------------------------------
Provider: OpenAI GPT-3.5
Rate: $0.002/1K tokens
Monthly cost: $20,000.00
Annual cost: $240,000.00

----------------------------------------------------------------------
Self-Hosted Costs
----------------------------------------------------------------------
Hardware: Datacenter 1× A100
  - GPUs: 1× A100 80GB
  - Upfront cost: $19,000.00
  - Amortized (36 months): $527.78/month

Operating costs (cloud deployment):
  - Cloud compute: $2,400.00/month
  - DevOps (20.0% FTE): $3,000.00/month
  - Total operating: $5,400.00/month

Total monthly (amortized): $5,927.78
Annual cost (Year 1): $83,800.00

----------------------------------------------------------------------
Comparison
----------------------------------------------------------------------
Break-even point: 1.3 months
Monthly savings (after break-even): $14,072.22
Annual savings (amortized): $168,866.64
ROI (12 months): 260.5%
ROI (36 months): 543.2%

----------------------------------------------------------------------
Recommendation
----------------------------------------------------------------------

✓ STRONGLY RECOMMEND self-hosting
  Break-even in <1 year (1.3 months)
  ROI: 260.5% in 12 months

Additional factors to consider:
  + High usage volume favors self-hosting
  + Data privacy requirements may override cost considerations
  + Customization (fine-tuning) easier with self-hosted
  - Cloud deployment has minimal upfront commitment

======================================================================
```

**Multi-Scenario Analysis:**
```bash
python tco_calculator.py --scenario-analysis
```

Output:
```
======================================================================
Multi-Scenario Comparison
======================================================================

Tokens/Month    API Cost     Self-Hosted     Break-Even   Recommend
=============== ============ =============== ============ ===============
0.5B            $1,000       $5,928          Never        ✗ No
1.0B            $2,000       $5,928          5mo          ○ Maybe
5.0B            $10,000      $5,928          1mo          ✓ Yes
10.0B           $20,000      $8,928          2mo          ✓ Yes

======================================================================
```

**Key Findings:**

1. **Break-even at 3-5B tokens/month** for 7B models
2. **60-85% cost savings** at scale (>10B tokens/month)
3. **Upfront investment**: $19K-$36K for datacenter hardware
4. **Cloud deployment**: Lower upfront, higher monthly costs
5. **Non-cost factors**: Data privacy, customization, no rate limits

**Deployment Comparison:**

| Deployment | Upfront Cost | Monthly Cost | Best For |
|------------|--------------|--------------|----------|
| Cloud (AWS/GCP) | $0 | $2,400 + DevOps | No upfront commitment |
| Colocation | $19K-$36K | $300 + Power + DevOps | Owned hardware, flexible |
| On-premises | $19K-$36K | Power + DevOps | Existing datacenter |

---

## Dependencies

**Required (all labs):**
```bash
pip install numpy
```

**Optional (for production mode):**
```bash
# vLLM benchmark
pip install vllm openai

# llama.cpp (build from source)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# TCO calculator visualization
pip install matplotlib
```

## Running All Labs

```bash
# vLLM benchmark (mock mode)
python vllm_benchmark.py --num-requests 100

# Quantization comparison (mock mode)
python quantization_comparison.py --model llama-2-7b

# TCO calculator
python tco_calculator.py --tokens-per-month 5B

# Multi-scenario TCO analysis
python tco_calculator.py --scenario-analysis

# Save all results
python vllm_benchmark.py --output vllm_results.json
python quantization_comparison.py --output quant_results.json
python tco_calculator.py --tokens-per-month 10B --output tco_results.json
```

## Decision Matrix

Use this matrix to choose the right self-hosting approach:

### When to use vLLM:

- ✓ Production deployment with datacenter GPUs
- ✓ High throughput required (>100 req/min)
- ✓ Multiple concurrent users (>50)
- ✓ Long context sequences (>2K tokens)
- ✗ No GPU available (use llama.cpp instead)

### When to use llama.cpp:

- ✓ Consumer hardware (laptops, workstations)
- ✓ CPU-only inference
- ✓ Apple Silicon (M1/M2/M3)
- ✓ Edge deployment
- ✓ Development/testing
- ✗ High-throughput production (use vLLM instead)

### When to use Ollama:

- ✓ Quick prototyping
- ✓ Local development
- ✓ Non-technical users
- ✓ Model experimentation
- ✗ Production serving (use vLLM or llama.cpp)

## TCO Decision Tree

```
Usage > 10B tokens/month?
├─ Yes → Self-host (strong ROI)
│   └─ Have datacenter GPU?
│       ├─ Yes → vLLM
│       └─ No → Cloud GPU + vLLM
└─ No → Usage 3-5B tokens/month?
    ├─ Yes → Consider self-hosting
    │   └─ Data privacy critical?
    │       ├─ Yes → Self-host
    │       └─ No → Use API (simpler)
    └─ No → Use API
        (Self-hosting not cost-effective)
```

## Performance Targets

### vLLM (NVIDIA A100 80GB)

| Model | Input Tokens | Output Tokens | Target Throughput | Target p99 Latency |
|-------|--------------|---------------|-------------------|-------------------|
| 7B | 512 | 128 | 18-22 req/s | <85ms |
| 7B | 2048 | 256 | 8-12 req/s | <220ms |
| 13B | 512 | 128 | 9-12 req/s | <165ms |

### llama.cpp (Various Hardware)

| Hardware | Model | Quantization | Target Speed | Target TTFT |
|----------|-------|--------------|--------------|-------------|
| M3 Max | 7B | Q5_K_M | 35-45 tok/s | 100ms |
| RTX 4090 | 7B | Q5_K_M | 80-100 tok/s | 50ms |
| RTX 4090 | 13B | Q5_K_M | 45-55 tok/s | 80ms |

## Troubleshooting

**vLLM Benchmark Issues:**

1. **"Connection refused" error**
   - Ensure vLLM server is running: `curl http://localhost:8000/health`
   - Check server logs for errors

2. **Low throughput (<10 req/s)**
   - Check GPU utilization: `nvidia-smi`
   - Increase `--max-num-seqs` in vLLM server
   - Check if CPU-bound (increase workers)

3. **High latency (>500ms)**
   - Reduce `--max-model-len` in vLLM server
   - Check for GPU memory pressure
   - Verify no other processes using GPU

**Quantization Comparison Issues:**

1. **llama.cpp server not responding**
   - Check server is running: `curl http://localhost:8080/health`
   - Verify model file exists and is readable
   - Check port is not blocked

2. **Slow inference (<5 tok/s)**
   - Increase `--n-gpu-layers` (offload more to GPU)
   - Use more aggressive quantization (Q4 vs Q5)
   - Check `--threads` matches CPU cores

**TCO Calculator Issues:**

1. **Unexpected break-even point**
   - Verify `--tokens-per-month` is correct
   - Check API pricing (use `--api-provider`)
   - Review deployment type (`--deployment`)

2. **Negative ROI**
   - Usage too low (<3B tokens/month)
   - Consider smaller model or shared infrastructure
   - Factor in non-cost benefits (privacy, customization)

## Extensions

1. **vLLM Benchmark:**
   - Add streaming latency measurement (TTFT)
   - Implement load testing with gradual ramp-up
   - Add Prometheus metrics export
   - Compare multiple models side-by-side

2. **Quantization Comparison:**
   - Test on additional benchmarks (GSM8K, HumanEval)
   - Measure actual memory usage (not just model size)
   - Profile CPU/GPU utilization
   - Test hybrid CPU+GPU configurations

3. **TCO Calculator:**
   - Add visualization (cost over time chart)
   - Include carbon footprint comparison
   - Add custom hardware configurations
   - Multi-model deployment scenarios

## References

See Chapter 4 for detailed citations and theoretical background.

**Key Papers:**
- Kwon et al. (2023): Efficient Memory Management for Large Language Model Serving with PagedAttention
- Yu et al. (2022): Orca - Continuous Batching for Generative Models
- Dettmers et al. (2023): GPT3.int8() - 8-bit Quantization
- Patterson et al. (2023): Carbon Emissions and Large Neural Network Training

**Tools:**
- vLLM: https://github.com/vllm-project/vllm
- llama.cpp: https://github.com/ggerganov/llama.cpp
- Ollama: https://ollama.ai

---

For questions or issues, see main project [README](../../README.md).
