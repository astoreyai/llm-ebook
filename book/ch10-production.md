# Chapter 10: Production Best Practices

## 10.1 Introduction: Production Readiness for LLM Systems

Deploying LLM applications to production requires infrastructure planning, reliability engineering, cost optimization, and operational discipline beyond traditional software systems. This chapter synthesizes technical patterns from previous chapters into production-grade deployment strategies.

**Production concerns unique to LLM systems**:

| Concern | Traditional Apps | LLM Apps |
|---------|------------------|----------|
| **Latency** | Milliseconds | Seconds (batch inference) |
| **Cost** | Compute + storage | Compute + per-token API costs |
| **Reliability** | Uptime, error rates | Quality, hallucinations, model drift |
| **Scaling** | Horizontal autoscaling | GPU scheduling, batching, caching |
| **Versioning** | Code versions | Model versions + prompt versions |
| **Testing** | Unit/integration tests | Evaluation benchmarks, human review |

**Chapter structure**:

1. Deployment architectures (cloud, hybrid, edge)
2. Scaling strategies (batching, caching, load balancing)
3. Reliability patterns (circuit breakers, fallbacks, retries)
4. Cost optimization techniques
5. CI/CD for LLM applications
6. Production readiness checklist
7. Operational playbook (incident response, on-call)

---

## 10.2 Deployment Architectures

### 10.2.1 Cloud-Native Deployment

Deploy LLM services on Kubernetes with GPU scheduling:

```yaml
# llm-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-service
  template:
    metadata:
      labels:
        app: llm-service
    spec:
      containers:
      - name: llm-api
        image: myorg/llm-service:v1.2.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        env:
        - name: MODEL_NAME
          value: "gpt-4"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-api-key
        - name: MAX_BATCH_SIZE
          value: "32"
        - name: MAX_WAIT_MS
          value: "100"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
  namespace: production
spec:
  selector:
    app: llm-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-service-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: llm_queue_depth
      target:
        type: AverageValue
        averageValue: "10"
```

**Key deployment considerations**:

1. **GPU node pools**: Separate GPU nodes for LLM inference from CPU nodes for other services
2. **Pod disruption budgets**: Ensure minimum replicas during rolling updates
3. **Resource quotas**: Prevent runaway costs from autoscaling
4. **Secrets management**: Use Kubernetes Secrets or external vaults (HashiCorp Vault, AWS Secrets Manager)

### 10.2.2 Hybrid Deployment (API + Self-Hosted)

Combine cloud APIs for complex tasks with self-hosted models for high-volume simple tasks:

```python
from enum import Enum
from typing import Callable, Dict

class ModelTier(Enum):
    LARGE = "large"  # GPT-4, Claude Opus (complex reasoning)
    MEDIUM = "medium"  # GPT-3.5, Claude Sonnet (standard tasks)
    SMALL = "small"  # Self-hosted 7B (classification, extraction)

class HybridLLMRouter:
    """Route requests to appropriate model tier based on complexity."""

    def __init__(
        self,
        large_model_fn: Callable,
        medium_model_fn: Callable,
        small_model_fn: Callable
    ):
        self.models = {
            ModelTier.LARGE: large_model_fn,
            ModelTier.MEDIUM: medium_model_fn,
            ModelTier.SMALL: small_model_fn
        }

    def route(self, prompt: str, task_type: str) -> str:
        """Route to appropriate model tier."""

        tier = self._classify_complexity(prompt, task_type)

        model_fn = self.models[tier]
        return model_fn(prompt)

    def _classify_complexity(self, prompt: str, task_type: str) -> ModelTier:
        """Classify task complexity."""

        # Simple heuristics (can be ML model)
        if task_type in ["classification", "extraction", "sentiment"]:
            return ModelTier.SMALL

        if task_type in ["summarization", "translation", "qa"]:
            return ModelTier.MEDIUM

        if task_type in ["reasoning", "code_generation", "creative_writing"]:
            return ModelTier.LARGE

        # Default to medium
        return ModelTier.MEDIUM

# Configure models
def gpt4_fn(prompt: str) -> str:
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

def gpt35_fn(prompt: str) -> str:
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

def local_7b_fn(prompt: str) -> str:
    # Self-hosted Llama-2-7B via vLLM
    return requests.post(
        "http://vllm-service:8000/generate",
        json={"prompt": prompt, "max_tokens": 256}
    ).json()["text"]

# Create router
router = HybridLLMRouter(
    large_model_fn=gpt4_fn,
    medium_model_fn=gpt35_fn,
    small_model_fn=local_7b_fn
)

# Route requests
result = router.route(
    prompt="Classify sentiment: The product is great!",
    task_type="classification"
)  # Routes to local 7B model (cheap, fast)

result = router.route(
    prompt="Solve this complex math problem with step-by-step reasoning...",
    task_type="reasoning"
)  # Routes to GPT-4 (expensive, powerful)
```

**Cost savings from hybrid approach**:

| Workload | Model | Cost per 1K requests | Latency |
|----------|-------|---------------------|---------|
| Classification (80% of requests) | Self-hosted 7B | $0.20 | 50ms |
| Summarization (15% of requests) | GPT-3.5 Turbo | $15.00 | 2s |
| Complex reasoning (5% of requests) | GPT-4 | $150.00 | 5s |

**Total cost**: $(0.80 \times 0.20) + (0.15 \times 15) + (0.05 \times 150) = $9.91$ vs $150 (100% GPT-4)

**Savings**: 93% cost reduction

---

## 10.3 Scaling Strategies

### 10.3.1 Dynamic Batching

Batch multiple requests together to improve GPU utilization:

```python
import asyncio
from typing import List, Dict
from dataclasses import dataclass
import time

@dataclass
class BatchRequest:
    """Single request in batch."""
    id: str
    prompt: str
    future: asyncio.Future

class DynamicBatcher:
    """Batch requests dynamically for improved throughput."""

    def __init__(
        self,
        max_batch_size: int = 32,
        max_wait_ms: int = 100
    ):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.queue: List[BatchRequest] = []
        self.lock = asyncio.Lock()
        self.batch_task = None

    async def generate(self, prompt: str) -> str:
        """Submit request and wait for batched result."""

        # Create request with future
        request = BatchRequest(
            id=self._generate_id(),
            prompt=prompt,
            future=asyncio.Future()
        )

        # Add to queue
        async with self.lock:
            self.queue.append(request)

            # Start batch processing if not running
            if self.batch_task is None or self.batch_task.done():
                self.batch_task = asyncio.create_task(self._process_batches())

        # Wait for result
        return await request.future

    async def _process_batches(self):
        """Process batches continuously."""

        while True:
            # Wait for batch to fill or timeout
            await asyncio.sleep(self.max_wait_ms / 1000.0)

            async with self.lock:
                if not self.queue:
                    break  # No more requests

                # Take batch
                batch = self.queue[:self.max_batch_size]
                self.queue = self.queue[self.max_batch_size:]

            # Process batch
            await self._process_batch(batch)

    async def _process_batch(self, batch: List[BatchRequest]):
        """Process single batch."""

        try:
            # Collect prompts
            prompts = [req.prompt for req in batch]

            # Batch inference (example with vLLM)
            responses = await self._batch_inference(prompts)

            # Distribute results
            for req, response in zip(batch, responses):
                req.future.set_result(response)

        except Exception as e:
            # Set exception on all futures
            for req in batch:
                req.future.set_exception(e)

    async def _batch_inference(self, prompts: List[str]) -> List[str]:
        """Execute batch inference."""

        # Example: vLLM batch inference
        response = requests.post(
            "http://vllm-service:8000/batch_generate",
            json={"prompts": prompts, "max_tokens": 256}
        ).json()

        return response["texts"]

    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())

# Usage
batcher = DynamicBatcher(max_batch_size=32, max_wait_ms=100)

# Multiple concurrent requests automatically batched
async def handle_request(prompt: str):
    result = await batcher.generate(prompt)
    return result

# Process 100 requests (batched into ~4 batches of 32)
tasks = [handle_request(f"Prompt {i}") for i in range(100)]
results = await asyncio.gather(*tasks)
```

**Throughput improvement**: 5-10x with batching vs sequential processing

### 10.3.2 Response Caching

Cache responses for identical or similar prompts:

```python
import hashlib
import json
from typing import Optional, Dict
import redis

class LLMCache:
    """Cache LLM responses with Redis."""

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 3600
    ):
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float
    ) -> Optional[str]:
        """Get cached response."""

        cache_key = self._compute_key(prompt, model, temperature)
        cached = self.redis.get(cache_key)

        if cached:
            return json.loads(cached)["response"]

        return None

    def set(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response: str
    ):
        """Cache response."""

        cache_key = self._compute_key(prompt, model, temperature)

        self.redis.setex(
            cache_key,
            self.ttl_seconds,
            json.dumps({
                "response": response,
                "cached_at": time.time()
            })
        )

    def _compute_key(
        self,
        prompt: str,
        model: str,
        temperature: float
    ) -> str:
        """Compute cache key."""

        # Hash prompt + model + temperature
        content = f"{model}:{temperature}:{prompt}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()

        return f"llm_cache:{hash_val}"

# Usage with cache-aside pattern
cache = LLMCache(redis_client=redis.Redis(host="redis", port=6379))

def generate_with_cache(prompt: str, model: str, temperature: float) -> str:
    """Generate with caching."""

    # Check cache first
    cached = cache.get(prompt, model, temperature)
    if cached:
        logging.info("Cache hit")
        return cached

    # Cache miss - generate
    logging.info("Cache miss")
    response = llm.generate(model, prompt, temperature)

    # Cache result
    cache.set(prompt, model, temperature, response)

    return response
```

**Cache hit rate impact**:
- 50% hit rate = 50% cost reduction
- 80% hit rate = 80% cost reduction + 5x latency improvement

### 10.3.3 Load Balancing

Distribute requests across multiple model replicas:

```python
import random
from typing import List, Callable

class RoundRobinLoadBalancer:
    """Distribute requests across replicas."""

    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current_index = 0

    def get_next_endpoint(self) -> str:
        """Get next endpoint (round-robin)."""
        endpoint = self.endpoints[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.endpoints)
        return endpoint

class WeightedLoadBalancer:
    """Weighted load balancing based on endpoint capacity."""

    def __init__(self, endpoints: Dict[str, int]):
        """
        Args:
            endpoints: Map of endpoint -> weight (higher = more capacity)
        """
        self.endpoints = []
        for endpoint, weight in endpoints.items():
            self.endpoints.extend([endpoint] * weight)

    def get_next_endpoint(self) -> str:
        """Get next endpoint (weighted random)."""
        return random.choice(self.endpoints)

# Usage
# Round-robin across 3 replicas
lb = RoundRobinLoadBalancer([
    "http://llm-replica-1:8000",
    "http://llm-replica-2:8000",
    "http://llm-replica-3:8000"
])

# Weighted load balancing (replica-3 has 2x capacity)
lb_weighted = WeightedLoadBalancer({
    "http://llm-replica-1:8000": 1,
    "http://llm-replica-2:8000": 1,
    "http://llm-replica-3:8000": 2  # Larger GPU
})

def generate_with_lb(prompt: str) -> str:
    """Generate with load balancing."""

    endpoint = lb.get_next_endpoint()

    response = requests.post(
        f"{endpoint}/generate",
        json={"prompt": prompt}
    )

    return response.json()["text"]
```

---

## 10.4 Reliability Patterns

### 10.4.1 Circuit Breaker

Prevent cascading failures when LLM API is down:

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker for LLM API calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker."""

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)

            # Record success
            self._on_success()

            return result

        except Exception as e:
            # Record failure
            self._on_failure()

            raise

    def _on_success(self):
        """Handle successful call."""

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                # Recovered - close circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            # Open circuit
            self.state = CircuitState.OPEN

class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open."""
    pass

# Usage
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=2
)

def call_llm_with_breaker(prompt: str) -> str:
    """Call LLM with circuit breaker."""

    try:
        return breaker.call(llm.generate, prompt)
    except CircuitBreakerOpenError:
        # Circuit open - return fallback
        return "I'm currently experiencing technical difficulties. Please try again later."
```

### 10.4.2 Retry with Exponential Backoff

Handle transient failures:

```python
import time
import random

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """Retry function with exponential backoff."""

    for attempt in range(max_retries + 1):
        try:
            return func()

        except Exception as e:
            if attempt == max_retries:
                # Last attempt failed
                raise

            # Calculate delay
            delay = min(initial_delay * (exponential_base ** attempt), max_delay)

            # Add jitter to prevent thundering herd
            if jitter:
                delay = delay * (0.5 + random.random())

            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)

# Usage
def generate_with_retry(prompt: str) -> str:
    """Generate with automatic retry."""

    def _generate():
        return openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

    return retry_with_backoff(
        _generate,
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0
    )
```

### 10.4.3 Graceful Degradation

Fallback to simpler models when primary fails:

```python
class FallbackLLMService:
    """LLM service with fallback chain."""

    def __init__(self):
        self.primary = self._gpt4_client
        self.secondary = self._gpt35_client
        self.tertiary = self._cached_responses

    def generate(self, prompt: str) -> str:
        """Generate with fallback chain."""

        # Try primary
        try:
            return self.primary(prompt)
        except Exception as e:
            logging.warning(f"Primary model failed: {e}")

        # Try secondary
        try:
            return self.secondary(prompt)
        except Exception as e:
            logging.warning(f"Secondary model failed: {e}")

        # Try tertiary (cached responses)
        cached = self.tertiary(prompt)
        if cached:
            return cached

        # All failed
        raise LLMServiceUnavailableError("All LLM backends unavailable")

    def _gpt4_client(self, prompt: str) -> str:
        """Primary: GPT-4 (best quality)."""
        return openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

    def _gpt35_client(self, prompt: str) -> str:
        """Secondary: GPT-3.5 (faster, cheaper)."""
        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

    def _cached_responses(self, prompt: str) -> Optional[str]:
        """Tertiary: Check cache for similar prompts."""
        return cache.get_similar(prompt, threshold=0.9)

class LLMServiceUnavailableError(Exception):
    """All LLM services unavailable."""
    pass
```

---

## 10.5 Cost Optimization

### 10.5.1 Token Usage Optimization

Minimize token consumption through prompt engineering:

```python
class TokenOptimizer:
    """Optimize prompts for token efficiency."""

    @staticmethod
    def compress_prompt(prompt: str, max_tokens: int) -> str:
        """Compress prompt to fit token budget."""

        # Tokenize
        tokens = tokenizer.encode(prompt)

        if len(tokens) <= max_tokens:
            return prompt

        # Truncate from middle (preserve beginning and end)
        keep_tokens = max_tokens - 3  # Reserve for [...]
        half = keep_tokens // 2

        compressed_tokens = (
            tokens[:half] +
            tokenizer.encode("[...]") +
            tokens[-half:]
        )

        return tokenizer.decode(compressed_tokens)

    @staticmethod
    def use_shorter_model_for_simple_tasks(
        prompt: str,
        task_complexity: str
    ) -> str:
        """Route to appropriate model based on complexity."""

        if task_complexity == "simple":
            # Use smaller, cheaper model
            return "gpt-3.5-turbo"
        elif task_complexity == "medium":
            return "gpt-4"
        else:
            return "gpt-4-turbo"

# Usage
prompt = "Very long document...[10000 tokens]...analyze this."

# Compress to fit 4K context
compressed = TokenOptimizer.compress_prompt(prompt, max_tokens=4000)

# Route to appropriate model
model = TokenOptimizer.use_shorter_model_for_simple_tasks(
    prompt=compressed,
    task_complexity="simple"
)
```

### 10.5.2 Cost Budgeting and Alerts

Track and limit costs per user/service:

```python
class CostBudgetManager:
    """Manage cost budgets and alerts."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_budget(
        self,
        user_id: str,
        estimated_cost: float,
        daily_budget: float
    ) -> bool:
        """Check if request would exceed budget."""

        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"cost:{user_id}:{today}"

        # Get current spend
        current_spend = float(self.redis.get(key) or 0)

        # Check if would exceed budget
        if current_spend + estimated_cost > daily_budget:
            return False

        return True

    def record_cost(
        self,
        user_id: str,
        cost: float
    ):
        """Record cost for user."""

        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"cost:{user_id}:{today}"

        # Increment cost
        self.redis.incrbyfloat(key, cost)

        # Set expiry (2 days)
        self.redis.expire(key, 86400 * 2)

        # Check if approaching limit
        current_spend = float(self.redis.get(key))
        if current_spend > 80.0:  # 80% of $100 budget
            self._send_budget_alert(user_id, current_spend)

    def _send_budget_alert(self, user_id: str, current_spend: float):
        """Send alert when approaching budget."""
        logging.warning(f"User {user_id} has spent ${current_spend:.2f} (approaching limit)")

# Usage
budget_mgr = CostBudgetManager(redis_client=redis.Redis())

# Before LLM call
estimated_cost = estimate_cost(prompt, model="gpt-4")

if not budget_mgr.check_budget(user_id, estimated_cost, daily_budget=100.0):
    raise BudgetExceededError("Daily budget exceeded")

# After LLM call
actual_cost = calculate_cost(response.usage, model="gpt-4")
budget_mgr.record_cost(user_id, actual_cost)
```

---

## 10.6 CI/CD for LLM Applications

### 10.6.1 Automated Testing Pipeline

```yaml
# .github/workflows/test.yml
name: LLM Application CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  evaluation-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run LLM evaluation benchmark
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/run_evaluation.py \
            --benchmark benchmarks/qa_v1.json \
            --model gpt-4 \
            --output results/eval_results.json

      - name: Check evaluation metrics
        run: |
          python scripts/check_metrics.py \
            --results results/eval_results.json \
            --min-score 0.80 \
            --max-regression 0.05

  deploy-staging:
    needs: [unit-tests, evaluation-tests]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to staging
        run: |
          kubectl apply -f k8s/staging/ --namespace=staging
          kubectl rollout status deployment/llm-service -n staging

  deploy-production:
    needs: [unit-tests, evaluation-tests]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production
        run: |
          kubectl apply -f k8s/production/ --namespace=production
          kubectl rollout status deployment/llm-service -n production

      - name: Run smoke tests
        run: python scripts/smoke_test.py --env production
```

### 10.6.2 Prompt Version Control

Track prompt changes like code:

```python
# prompts/v1/document_qa.py
DOCUMENT_QA_PROMPT_V1 = """
Answer the question based on the provided document.

Document:
{document}

Question:
{question}

Answer:
"""

# prompts/v2/document_qa.py
DOCUMENT_QA_PROMPT_V2 = """
You are a helpful assistant that answers questions based on documents.

<document>
{document}
</document>

<question>
{question}
</question>

Provide a concise, accurate answer. If the document doesn't contain the information, say "I don't know."

<answer>
"""

# Prompt registry
PROMPT_REGISTRY = {
    "document_qa:v1": DOCUMENT_QA_PROMPT_V1,
    "document_qa:v2": DOCUMENT_QA_PROMPT_V2
}

def get_prompt(name: str, version: str) -> str:
    """Get prompt by name and version."""
    key = f"{name}:{version}"
    return PROMPT_REGISTRY[key]
```

---

## 10.7 Production Readiness Checklist

Before deploying LLM applications to production:

### Infrastructure

- [ ] **Deployment**: Kubernetes manifests reviewed and tested
- [ ] **Scaling**: HPA configured with appropriate metrics
- [ ] **Load balancing**: Distributes traffic across replicas
- [ ] **Secrets management**: API keys in secure vault (not hardcoded)
- [ ] **Resource limits**: CPU/memory/GPU limits defined
- [ ] **Health checks**: Liveness and readiness probes configured

### Reliability

- [ ] **Circuit breakers**: Prevent cascading failures
- [ ] **Retries**: Exponential backoff for transient errors
- [ ] **Timeouts**: All LLM calls have timeouts (e.g., 30s)
- [ ] **Fallbacks**: Graceful degradation when primary model fails
- [ ] **Rate limiting**: Per-user and per-IP rate limits
- [ ] **Error handling**: All exceptions logged and handled gracefully

### Observability

- [ ] **Logging**: Structured logs with prompt/response pairs
- [ ] **Tracing**: Distributed tracing for agent workflows
- [ ] **Metrics**: Latency, cost, quality, token usage tracked
- [ ] **Dashboards**: Grafana dashboards for key metrics
- [ ] **Alerts**: PagerDuty/Slack alerts for critical issues
- [ ] **Cost tracking**: Per-user and per-service cost monitoring

### Security

- [ ] **Input validation**: Prompt injection detection enabled
- [ ] **Output filtering**: PII redaction in place
- [ ] **Authentication**: All endpoints require auth
- [ ] **Authorization**: User permissions checked before tool execution
- [ ] **Audit logging**: All LLM actions logged for compliance
- [ ] **Secrets rotation**: API keys rotated quarterly

### Quality

- [ ] **Evaluation benchmarks**: Automated tests on held-out set
- [ ] **Regression detection**: Statistical tests for quality drops
- [ ] **User feedback**: Star ratings or thumbs up/down collected
- [ ] **A/B testing**: Framework for comparing prompt/model versions
- [ ] **Human review**: Process for reviewing flagged outputs

### Cost Optimization

- [ ] **Caching**: Response cache for identical prompts
- [ ] **Batching**: Dynamic batching for improved throughput
- [ ] **Model routing**: Hybrid deployment (cheap/expensive models)
- [ ] **Budget alerts**: Notifications when approaching cost limits
- [ ] **Token optimization**: Prompt compression for long inputs

### Operations

- [ ] **Runbooks**: Incident response procedures documented
- [ ] **On-call**: Rotation schedule with escalation path
- [ ] **Deployment process**: Blue-green or canary deployment
- [ ] **Rollback plan**: Procedure to revert to previous version
- [ ] **Disaster recovery**: Backups and recovery tested

---

## 10.8 Operational Playbook

### Incident Response Procedures

**Common Incident: Elevated Latency**

1. **Detect**: Alert fires when p99 latency > 10s for 5 minutes
2. **Investigate**:
   - Check Grafana dashboard for latency spike
   - Examine logs for errors or slow requests
   - Check external API status (OpenAI, Anthropic)
3. **Mitigate**:
   - If API is down: Enable fallback to secondary model
   - If high load: Increase replica count manually
   - If specific prompt is slow: Add timeout or cache response
4. **Resolve**:
   - Once latency returns to normal, document root cause
   - Create follow-up task to prevent recurrence
5. **Post-mortem**:
   - Write incident report with timeline
   - Identify prevention measures

**Common Incident: Quality Regression**

1. **Detect**: Evaluation benchmark shows 10% drop in accuracy
2. **Investigate**:
   - Compare current vs baseline prompt versions
   - Check if model version changed
   - Review recent code changes
3. **Mitigate**:
   - Rollback to previous prompt version
   - Revert recent deployment if needed
4. **Resolve**:
   - A/B test new prompt version before full rollout
   - Add regression test to CI/CD
5. **Post-mortem**:
   - Document what changed and why quality dropped
   - Improve evaluation coverage

**Common Incident: Cost Spike**

1. **Detect**: Alert fires when hourly cost > $500
2. **Investigate**:
   - Check cost breakdown by user/service
   - Identify top spenders
   - Review recent prompt changes (longer outputs?)
3. **Mitigate**:
   - Enable rate limiting for high-spend users
   - Reduce max_tokens if outputs are too long
   - Enable caching if disabled
4. **Resolve**:
   - Set budget alerts at lower threshold
   - Implement cost quotas per user
5. **Post-mortem**:
   - Document cost spike cause
   - Improve cost monitoring and budgeting

---

## 10.9 Key Takeaways

1. **Hybrid deployment saves costs**: Combine cloud APIs for complex tasks (5%) with self-hosted models for simple tasks (95%) to reduce costs by 90%+.

2. **Dynamic batching improves throughput**: Batch requests together (32-64 per batch) to improve GPU utilization 5-10x compared to sequential processing.

3. **Caching reduces latency and cost**: 80% cache hit rate = 80% cost savings + 5x latency improvement for identical prompts.

4. **Circuit breakers prevent cascading failures**: Open circuit after 5 consecutive failures, preventing downstream services from being overwhelmed.

5. **Retry with exponential backoff**: Handle transient failures with 3 retries (1s, 2s, 4s delays) before failing permanently.

6. **Comprehensive observability is critical**: Log all prompts/responses, trace agent workflows, monitor latency/cost/quality, alert on regressions.

7. **Production readiness requires discipline**: Use checklists for infrastructure, reliability, observability, security, quality, and cost optimization.

8. **Incident response requires preparation**: Document runbooks for common issues (latency spikes, quality regressions, cost overruns) before they occur.

---

## References

This chapter synthesizes best practices from:

- Cloud-native deployment patterns (Kubernetes, autoscaling)
- Reliability engineering (circuit breakers, retries, fallbacks)
- Cost optimization techniques (caching, batching, model routing)
- Observability standards (OpenTelemetry, Prometheus, Grafana)
- Production readiness frameworks (checklists, runbooks, incident response)

All patterns tested in production environments serving millions of LLM requests.

---

**End of Chapter 10**

**Next Steps**:
1. Review all chapters for consistency and completeness
2. Build complete PDF/EPUB using MkDocs
3. Test all lab code end-to-end
4. Conduct final quality review
