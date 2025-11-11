# Chapter 3: Context Engineering for Long Inputs & RAG

## Abstract

This chapter addresses the challenge of providing relevant context to language models within finite context windows. We examine context window management strategies, position effects (lost-in-the-middle phenomenon), and advanced Retrieval-Augmented Generation (RAG) techniques. Covered methods include HyDE (Hypothetical Document Embeddings), RAPTOR (Recursive Abstractive Processing), and Self-RAG (self-reflective retrieval). We provide empirical comparisons, implementation patterns, hallucination detection methods, and production deployment guidelines. All techniques are grounded in peer-reviewed research with reproducible examples.

**Learning Objectives:**
- Understand context window constraints and position effects
- Implement basic and advanced RAG architectures
- Apply HyDE, RAPTOR, and Self-RAG techniques
- Design retrieval routing and re-ranking strategies
- Detect and mitigate hallucinations in RAG systems
- Deploy production RAG with monitoring and evaluation

## 3.1 Context Windows: Limits and Position Effects

### 3.1.1 Context Window Fundamentals

**Definition**: The context window is the maximum number of tokens an LLM can process in a single inference call, including both input prompt and generated output.

**Current Limits (2025):**

| Model | Context Window | Notes |
|-------|---------------|-------|
| GPT-4 Turbo | 128K tokens | ~96K words |
| GPT-4 | 8K-32K tokens | Varies by version |
| Claude 3 Opus | 200K tokens | ~150K words |
| Claude 3.5 Sonnet | 200K tokens | ~150K words |
| Gemini 1.5 Pro | 2M tokens | Experimental |
| Llama 3.1 405B | 128K tokens | Open source |

**Token-to-Word Approximation**:
- English: ~1.3 tokens per word (GPT tokenizer)
- Code: ~1.5-2 tokens per word
- Technical text: ~1.4 tokens per word

**Practical Constraints:**
- **Cost**: Longer contexts = higher API costs (linear or superlinear)
- **Latency**: Processing time increases with context length
- **Accuracy**: Position effects reduce effectiveness (see §3.1.2)
- **Memory**: Local deployment requires proportional VRAM

### 3.1.2 Lost-in-the-Middle: Position Effects

**Problem**: LLMs exhibit reduced recall for information in the middle of long contexts [1].

**Empirical Evidence: Liu et al. (2023) [1]**

Tested information retrieval across context positions (0-32K tokens):

| Information Position | Recall Accuracy |
|---------------------|-----------------|
| Beginning (0-10%) | 92% |
| Middle (40-60%) | 62% [NO] |
| End (90-100%) | 88% |

**Key Finding**: ~30% accuracy drop for information in the middle of long contexts.

**Position Effect Curve:**

```
Recall Accuracy
    │
95% │ ╮                              ╭─
    │  ╲                            ╱
75% │   ╲                          ╱
    │    ╲                        ╱
55% │     ╰────────────────────╯  ← "Lost in the middle"
    │
    └────────────────────────────────→
       0%        50%        100%
           Context Position
```

**Mitigation Strategies:**

1. **Place Critical Info at Boundaries**: Put most important content at start or end
2. **Chunking with Overlap**: Split into smaller contexts with redundancy
3. **Re-ranking**: Surface most relevant chunks to prominent positions
4. **Structured Retrieval**: Use explicit metadata and routing

### 3.1.3 Pattern Card: Context Window Management

| Component | Details |
|-----------|---------|
| **Intent** | Maximize effective use of limited context windows |
| **When It Helps** | Long documents, multi-document QA, code repositories |
| **Mechanics** | Chunk, retrieve, rank, position strategically |
| **Minimal Implementation** | Sliding window with overlap |
| **Variants** | Hierarchical, semantic, metadata-filtered |
| **Failure Modes** | Information loss, boundary truncation, relevance drift |
| **Security Notes** | Context injection attacks via crafted chunks |
| **Test Cases** | Multi-hop QA, needle-in-haystack retrieval |

## 3.2 Retrieval-Augmented Generation (RAG): Foundations

### 3.2.1 What is RAG?

**Retrieval-Augmented Generation (RAG)** combines retrieval systems with generative LLMs to ground outputs in external knowledge [2].

**Architecture:**

```
User Query → Retriever → Top-K Docs → LLM + Query → Generated Answer
                ↑                          ↓
           Vector DB              Citation/Verification
```

**Benefits:**
- [YES] Reduces hallucinations via grounding
- [YES] Enables knowledge updates without retraining
- [YES] Provides attribution and citations
- [YES] Handles proprietary/private data

**Challenges:**
- [NO] Retrieval errors compound into generation errors
- [NO] Irrelevant context degrades output quality
- [NO] Latency: retrieval + generation overhead
- [NO] Cost: embedding + LLM inference

### 3.2.2 Basic RAG Pipeline

**Implementation:**

```python
from typing import List, Dict
import numpy as np

class BasicRAG:
    """Basic Retrieval-Augmented Generation pipeline."""

    def __init__(self, embedding_model, llm, vector_db, top_k: int = 5):
        self.embedding_model = embedding_model
        self.llm = llm
        self.vector_db = vector_db
        self.top_k = top_k

    def index_documents(self, documents: List[Dict]):
        """Index documents with embeddings."""
        for doc in documents:
            embedding = self.embedding_model.embed(doc["content"])
            self.vector_db.add(
                id=doc["id"],
                embedding=embedding,
                metadata=doc
            )

    def retrieve(self, query: str) -> List[Dict]:
        """Retrieve top-k relevant documents."""
        query_embedding = self.embedding_model.embed(query)
        results = self.vector_db.search(
            query_embedding,
            top_k=self.top_k
        )
        return results

    def generate(self, query: str, context_docs: List[Dict]) -> str:
        """Generate answer from query and retrieved context."""
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1}:\n{doc['content']}"
            for i, doc in enumerate(context_docs)
        ])

        # Construct prompt
        prompt = f"""Answer the following question using the provided context.
If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer:"""

        response = self.llm.generate(prompt)
        return response

    def query(self, question: str) -> Dict:
        """End-to-end RAG query."""
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(question)

        # Generate answer
        answer = self.generate(question, retrieved_docs)

        return {
            "question": question,
            "answer": answer,
            "sources": retrieved_docs,
            "n_sources": len(retrieved_docs)
        }
```

**Performance Baseline:**

Lewis et al. (2020) [2] demonstrated RAG improvements on knowledge-intensive tasks:

| Task | LLM Only | RAG | Improvement |
|------|----------|-----|-------------|
| Natural Questions | 24.2% | 44.5% | +20.3pp |
| TriviaQA | 60.5% | 68.0% | +7.5pp |
| WebQuestions | 35.3% | 45.5% | +10.2pp |

### 3.2.3 Chunking Strategies

**Challenge**: Documents often exceed context windows; chunking is required.

**Chunking Methods:**

1. **Fixed-Size Chunks**
   ```python
   def fixed_size_chunking(text: str, chunk_size: int = 512, overlap: int = 50):
       """Split text into fixed-size chunks with overlap."""
       words = text.split()
       chunks = []
       for i in range(0, len(words), chunk_size - overlap):
           chunk = " ".join(words[i:i + chunk_size])
           chunks.append(chunk)
       return chunks
   ```
   - **Pros**: Simple, predictable token counts
   - **Cons**: Breaks semantic boundaries

2. **Semantic Chunks** (sentence/paragraph boundaries)
   ```python
   def semantic_chunking(text: str, max_chunk_size: int = 512):
       """Split at paragraph/sentence boundaries."""
       paragraphs = text.split("\n\n")
       chunks = []
       current_chunk = ""

       for para in paragraphs:
           if len(current_chunk) + len(para) < max_chunk_size:
               current_chunk += para + "\n\n"
           else:
               if current_chunk:
                   chunks.append(current_chunk.strip())
               current_chunk = para + "\n\n"

       if current_chunk:
           chunks.append(current_chunk.strip())

       return chunks
   ```
   - **Pros**: Preserves semantic coherence
   - **Cons**: Variable chunk sizes

3. **Sliding Window with Overlap**
   - **Purpose**: Ensure no information lost at boundaries
   - **Typical Overlap**: 10-20% of chunk size
   - **Trade-off**: More chunks = higher storage/retrieval cost

**Empirical Guidance:**

| Document Type | Recommended Chunk Size | Overlap | Method |
|---------------|----------------------|---------|--------|
| Technical docs | 512-1024 tokens | 50-100 | Semantic |
| Code | 256-512 tokens | 50 | Semantic (function-level) |
| Chat logs | 256 tokens | 25 | Fixed |
| Legal documents | 1024 tokens | 100 | Semantic |

## 3.3 Advanced RAG: HyDE

### 3.3.1 What is HyDE?

**HyDE (Hypothetical Document Embeddings)** [3] improves retrieval by generating a hypothetical answer first, then embedding it for similarity search.

**Problem**: Query-document mismatch in embedding space.

**Insight**: Hypothetical answers are closer to actual documents in embedding space than raw queries.

**Architecture:**

```
User Query → LLM (generate hypothetical answer) → Embed answer →
    Retrieve similar documents → LLM (generate real answer)
```

### 3.3.2 Pattern Card: HyDE

| Component | Details |
|-----------|---------|
| **Intent** | Improve retrieval via hypothetical answer generation |
| **When It Helps** | Complex queries, technical domains, low query-doc overlap |
| **Mechanics** | Generate → Embed → Retrieve → Verify |
| **Minimal Implementation** | LLM generates hypothesis, embed, search |
| **Variants** | Multi-hypothesis, iterative refinement |
| **Failure Modes** | Hallucinated hypothesis misleads retrieval |
| **Security Notes** | Hypothesis generation vulnerable to prompt injection |
| **Test Cases** | Technical QA, multi-hop reasoning |

### 3.3.3 HyDE Implementation

```python
class HyDERAG(BasicRAG):
    """HyDE-enhanced RAG pipeline."""

    def generate_hypothesis(self, query: str) -> str:
        """Generate hypothetical answer for better retrieval."""
        hypothesis_prompt = f"""Generate a detailed, hypothetical answer to this question.
Focus on including technical terms and concepts that would appear in relevant documents.

Question: {query}

Hypothetical Answer:"""

        hypothesis = self.llm.generate(
            hypothesis_prompt,
            max_tokens=200,
            temperature=0.7
        )
        return hypothesis

    def retrieve_with_hyde(self, query: str) -> List[Dict]:
        """Retrieve using HyDE: embed hypothetical answer."""
        # Generate hypothesis
        hypothesis = self.generate_hypothesis(query)

        # Embed hypothesis instead of query
        hypothesis_embedding = self.embedding_model.embed(hypothesis)

        # Search with hypothesis embedding
        results = self.vector_db.search(
            hypothesis_embedding,
            top_k=self.top_k
        )
        return results

    def query(self, question: str) -> Dict:
        """End-to-end HyDE-RAG query."""
        # HyDE retrieval
        retrieved_docs = self.retrieve_with_hyde(question)

        # Generate final answer
        answer = self.generate(question, retrieved_docs)

        return {
            "question": question,
            "answer": answer,
            "sources": retrieved_docs,
            "method": "HyDE"
        }
```

### 3.3.4 Empirical Results

Gao et al. (2022) [3] demonstrated HyDE improvements:

| Dataset | Standard RAG | HyDE RAG | Improvement |
|---------|--------------|----------|-------------|
| TREC-COVID | 63.5% | 71.2% | +7.7pp |
| NFCorpus | 31.8% | 37.4% | +5.6pp |
| SciFact | 65.1% | 70.9% | +5.8pp |

**When HyDE Helps Most:**
- [YES] Technical/scientific queries
- [YES] Domain-specific terminology
- [YES] Complex multi-concept questions

**When HyDE Hurts:**
- [NO] Simple factual queries (adds overhead)
- [NO] Hallucinated hypotheses mislead retrieval
- [NO] Real-time applications (2× LLM calls)

## 3.4 Advanced RAG: RAPTOR

### 3.4.1 What is RAPTOR?

**RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)** [4] builds hierarchical summarization trees over document collections.

**Problem**: Flat chunk retrieval misses high-level concepts and connections.

**Solution**: Build multi-level summaries (tree structure) and retrieve at appropriate abstraction levels.

**Architecture:**

```
                [Global Summary]
                       |
           /-----------+-----------\
          /            |            \
   [Section A]   [Section B]   [Section C]
     /    \         /    \         /    \
 [Ch1] [Ch2]    [Ch3] [Ch4]    [Ch5] [Ch6]
   |     |        |     |        |     |
[Text] [Text]  [Text] [Text]  [Text] [Text]
```

### 3.4.2 RAPTOR Algorithm

**Phase 1: Tree Construction**

1. **Chunk**: Split documents into base chunks
2. **Embed**: Generate embeddings for all chunks
3. **Cluster**: Group similar chunks using GMM or k-means
4. **Summarize**: Generate summary for each cluster
5. **Repeat**: Recursively summarize summaries until single root

**Phase 2: Retrieval**

1. **Multi-Level Search**: Query against all tree levels
2. **Score Aggregation**: Combine scores across levels
3. **Diversity**: Ensure results from multiple levels
4. **Threshold**: Return chunks exceeding relevance threshold

### 3.4.3 RAPTOR Implementation (Simplified)

```python
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple

class RAPTOR:
    """RAPTOR: Hierarchical summarization for retrieval."""

    def __init__(self, llm, embedding_model, n_clusters: int = 5):
        self.llm = llm
        self.embedding_model = embedding_model
        self.n_clusters = n_clusters
        self.tree = {}  # level -> nodes

    def build_tree(self, documents: List[str], max_levels: int = 3):
        """Build RAPTOR tree from documents."""
        current_nodes = [{"text": doc, "level": 0} for doc in documents]
        self.tree[0] = current_nodes

        for level in range(1, max_levels + 1):
            if len(current_nodes) <= 1:
                break

            # Embed current level nodes
            embeddings = [
                self.embedding_model.embed(node["text"])
                for node in current_nodes
            ]

            # Cluster
            n_clusters = min(self.n_clusters, len(current_nodes) // 2)
            clusters = self._cluster(embeddings, n_clusters)

            # Summarize each cluster
            next_nodes = []
            for cluster_id in range(n_clusters):
                cluster_texts = [
                    current_nodes[i]["text"]
                    for i, c in enumerate(clusters)
                    if c == cluster_id
                ]

                summary = self._summarize_cluster(cluster_texts)
                next_nodes.append({
                    "text": summary,
                    "level": level,
                    "children": cluster_texts
                })

            self.tree[level] = next_nodes
            current_nodes = next_nodes

    def _cluster(self, embeddings: List, n_clusters: int) -> List[int]:
        """Cluster embeddings using k-means."""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        return kmeans.fit_predict(embeddings)

    def _summarize_cluster(self, texts: List[str]) -> str:
        """Generate summary for a cluster of texts."""
        combined = "\n\n---\n\n".join(texts[:5])  # Limit to avoid overflow

        prompt = f"""Summarize the following related texts into a coherent summary.
Preserve key concepts and connections.

Texts:
{combined}

Summary:"""

        summary = self.llm.generate(prompt, max_tokens=300)
        return summary

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Multi-level retrieval from RAPTOR tree."""
        query_embedding = self.embedding_model.embed(query)
        all_candidates = []

        # Search all tree levels
        for level, nodes in self.tree.items():
            for node in nodes:
                node_embedding = self.embedding_model.embed(node["text"])
                similarity = self._cosine_similarity(query_embedding, node_embedding)

                all_candidates.append({
                    "text": node["text"],
                    "level": level,
                    "similarity": similarity
                })

        # Sort by similarity and select top-k
        all_candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return all_candidates[:top_k]

    def _cosine_similarity(self, a, b) -> float:
        """Compute cosine similarity."""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### 3.4.4 Empirical Results

Sarthi et al. (2024) [4] demonstrated RAPTOR improvements on multi-hop reasoning:

| Task | Standard RAG | RAPTOR | Improvement |
|------|--------------|--------|-------------|
| QuALITY (QA) | 48.2% | 55.7% | +7.5pp |
| QASPER (Scientific QA) | 32.1% | 38.9% | +6.8pp |
| NarrativeQA | 23.5% | 28.2% | +4.7pp |

**When RAPTOR Helps:**
- [YES] Long documents (>10K tokens)
- [YES] Multi-level concepts (technical docs, books)
- [YES] Questions requiring high-level understanding

**Trade-offs:**
- **Indexing Time**: Significantly higher (clustering + summarization)
- **Storage**: 2-3× due to multiple tree levels
- **Query Latency**: Multi-level search increases time

## 3.5 Advanced RAG: Self-RAG

### 3.5.1 What is Self-RAG?

**Self-RAG (Self-Reflective RAG)** [5] adds self-critique and reflection tokens to improve retrieval and generation quality.

**Innovation**: Model learns when to retrieve, what to retrieve, and how to critique its own outputs.

**Reflection Tokens:**

- `[Retrieve]`: Should I retrieve documents?
- `[IsRel]`: Is retrieved doc relevant?
- `[IsSup]`: Is answer supported by context?
- `[IsUse]`: Is answer useful?

### 3.5.2 Self-RAG Architecture

```
Query → [Retrieve] → Yes/No Decision
           ↓
    (If Yes) Retrieve Docs
           ↓
    For each doc: [IsRel] → Filter
           ↓
    Generate Answer
           ↓
    [IsSup] → Check grounding
           ↓
    [IsUse] → Check utility
           ↓
    Final Answer with Confidence
```

### 3.5.3 Implementation Pattern

```python
class SelfRAG:
    """Self-RAG with reflection tokens."""

    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever

    def decide_retrieve(self, query: str) -> bool:
        """Decide if retrieval is needed."""
        prompt = f"""Question: {query}

Do you need to retrieve external documents to answer this question accurately?
Respond with only "Yes" or "No".

[Retrieve]:"""

        decision = self.llm.generate(prompt, max_tokens=5).strip()
        return decision.lower() == "yes"

    def assess_relevance(self, query: str, document: str) -> float:
        """Assess if document is relevant to query."""
        prompt = f"""Question: {query}

Document: {document}

Is this document relevant to answering the question?
Rate relevance from 0.0 (not relevant) to 1.0 (highly relevant).

[IsRel]:"""

        score_text = self.llm.generate(prompt, max_tokens=10)
        try:
            return float(score_text.strip())
        except:
            return 0.5  # Default to neutral

    def check_support(self, answer: str, context: str) -> float:
        """Check if answer is supported by context."""
        prompt = f"""Context: {context}

Answer: {answer}

Is this answer fully supported by the context?
Rate support from 0.0 (not supported) to 1.0 (fully supported).

[IsSup]:"""

        score_text = self.llm.generate(prompt, max_tokens=10)
        try:
            return float(score_text.strip())
        except:
            return 0.5

    def query(self, question: str, relevance_threshold: float = 0.6) -> Dict:
        """Self-RAG query with reflection."""
        # Decide if retrieval needed
        should_retrieve = self.decide_retrieve(question)

        if not should_retrieve:
            # Direct answer without retrieval
            answer = self.llm.generate(f"Q: {question}\nA:")
            return {
                "answer": answer,
                "retrieved": False,
                "support_score": None
            }

        # Retrieve documents
        docs = self.retriever.retrieve(question, top_k=5)

        # Filter by relevance
        relevant_docs = []
        for doc in docs:
            relevance = self.assess_relevance(question, doc["text"])
            if relevance >= relevance_threshold:
                relevant_docs.append(doc)

        if not relevant_docs:
            return {
                "answer": "I don't have enough relevant information to answer this question.",
                "retrieved": True,
                "filtered_all": True
            }

        # Generate answer with context
        context = "\n\n".join([d["text"] for d in relevant_docs])
        answer_prompt = f"""Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"""
        answer = self.llm.generate(answer_prompt)

        # Check support
        support_score = self.check_support(answer, context)

        return {
            "answer": answer,
            "retrieved": True,
            "n_docs_retrieved": len(docs),
            "n_docs_relevant": len(relevant_docs),
            "support_score": support_score,
            "sources": relevant_docs
        }
```

### 3.5.4 Empirical Results

Asai et al. (2023) [5] demonstrated Self-RAG improvements:

| Benchmark | Standard RAG | Self-RAG | Improvement |
|-----------|--------------|----------|-------------|
| PopQA (long-tail) | 41.2% | 51.8% | +10.6pp |
| PubHealth (fact-check) | 73.5% | 82.1% | +8.6pp |
| Bio-ASQ | 65.3% | 72.7% | +7.4pp |

**Benefits:**
- [YES] Selective retrieval (reduces unnecessary calls)
- [YES] Relevance filtering (higher quality context)
- [YES] Grounding verification (fewer hallucinations)

**Costs:**
- Additional LLM calls for reflection tokens
- More complex prompt engineering
- Requires fine-tuning for best results

## 3.6 Hallucination Detection and Mitigation

### 3.6.1 Types of Hallucinations in RAG

1. **Intrinsic**: Contradicts retrieved context
2. **Extrinsic**: Not supported by context (but not contradictory)
3. **Factual**: Incorrect real-world facts
4. **Attribution**: Misattributes sources

### 3.6.2 Detection Methods

**1. NLI-Based Verification**

```python
def verify_with_nli(answer: str, context: str, nli_model) -> Dict:
    """Verify answer against context using NLI."""
    result = nli_model(f"{context} [SEP] {answer}")

    return {
        "entailment_score": result["entailment"],
        "contradiction_score": result["contradiction"],
        "neutral_score": result["neutral"],
        "verdict": "supported" if result["entailment"] > 0.7 else "unsupported"
    }
```

**2. LLM-as-Judge**

```python
def llm_judge_grounding(answer: str, context: str, llm) -> float:
    """Use LLM to judge if answer is grounded in context."""
    prompt = f"""Context: {context}

Answer: {answer}

Is the answer fully supported by the context? Consider:
1. Are all facts in the answer present in the context?
2. Are there contradictions?
3. Are there unsupported claims?

Rate from 0.0 (completely unsupported) to 1.0 (fully supported).

Score:"""

    score_text = llm.generate(prompt, temperature=0)
    return float(score_text.strip())
```

**3. Citation Matching**

```python
def verify_citations(answer: str, sources: List[str]) -> Dict:
    """Verify that answer claims can be traced to sources."""
    claims = extract_claims(answer)  # Implement claim extraction

    verified_claims = []
    for claim in claims:
        found_in_source = any(
            claim_similarity(claim, source) > 0.8
            for source in sources
        )
        verified_claims.append({
            "claim": claim,
            "verified": found_in_source
        })

    verification_rate = sum(c["verified"] for c in verified_claims) / len(claims)

    return {
        "claims": verified_claims,
        "verification_rate": verification_rate,
        "verdict": "reliable" if verification_rate > 0.9 else "check_needed"
    }
```

### 3.6.3 Mitigation Strategies

**1. Constrained Generation**

```python
prompt = f"""Using ONLY the information in the context below, answer the question.
If the answer is not in the context, respond with "I don't know."
Do not use external knowledge.

Context: {context}

Question: {question}

Answer:"""
```

**2. Citation-Required Generation**

```python
prompt = f"""Answer the question and cite sources using [1], [2], etc.

Context:
[1] {source_1}
[2] {source_2}

Question: {question}

Answer with citations:"""
```

**3. Multi-Stage Verification**

```python
def verified_rag(query: str, rag_system) -> Dict:
    """RAG with multi-stage verification."""
    # Stage 1: Generate answer
    initial_result = rag_system.query(query)
    answer = initial_result["answer"]
    context = initial_result["context"]

    # Stage 2: NLI verification
    nli_verdict = verify_with_nli(answer, context, nli_model)

    # Stage 3: LLM judge
    judge_score = llm_judge_grounding(answer, context, llm)

    # Stage 4: Citation check
    citation_result = verify_citations(answer, initial_result["sources"])

    # Aggregate confidence
    confidence = (
        nli_verdict["entailment_score"] * 0.4 +
        judge_score * 0.3 +
        citation_result["verification_rate"] * 0.3
    )

    return {
        "answer": answer,
        "confidence": confidence,
        "verified": confidence > 0.75,
        "verification_details": {
            "nli": nli_verdict,
            "judge": judge_score,
            "citations": citation_result
        }
    }
```

## 3.7 Production RAG: Best Practices

### 3.7.1 Hybrid Search

**Combine dense and sparse retrieval** for better coverage:

```python
def hybrid_search(query: str, k: int = 10, alpha: float = 0.5):
    """Hybrid: dense (vector) + sparse (BM25) search."""
    # Dense retrieval
    dense_results = vector_db.search(query, k=k)

    # Sparse retrieval (BM25/keyword)
    sparse_results = bm25_index.search(query, k=k)

    # Reciprocal Rank Fusion
    combined = reciprocal_rank_fusion(
        [dense_results, sparse_results],
        weights=[alpha, 1 - alpha]
    )

    return combined[:k]
```

**Empirical Guidance**: α = 0.5-0.7 (favor dense) for semantic queries; α = 0.3-0.5 for keyword/entity queries.

### 3.7.2 Re-ranking

**Apply cross-encoder re-ranking** after initial retrieval:

```python
def rerank_results(query: str, candidates: List[Dict], top_k: int = 5):
    """Re-rank with cross-encoder for better precision."""
    scores = []
    for doc in candidates:
        score = cross_encoder.predict([query, doc["text"]])
        scores.append(score)

    # Sort by re-ranking score
    reranked = [
        doc for _, doc in sorted(zip(scores, candidates), reverse=True)
    ]

    return reranked[:top_k]
```

**Performance**: +5-10% precision on most benchmarks, +30-50ms latency.

### 3.7.3 Monitoring and Observability

**Key Metrics:**

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Retrieval Latency | <100ms | >200ms |
| Generation Latency | <2s | >5s |
| Retrieval Precision@5 | >0.8 | <0.6 |
| Hallucination Rate | <5% | >10% |
| Citation Accuracy | >90% | <80% |
| User Satisfaction | >4.0/5 | <3.5/5 |

**Implementation:**

```python
from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

retrieval_latency = meter.create_histogram("rag.retrieval.latency")
generation_latency = meter.create_histogram("rag.generation.latency")
hallucination_counter = meter.create_counter("rag.hallucinations")

@tracer.start_as_current_span("rag_query")
def instrumented_rag_query(query: str):
    span = trace.get_current_span()
    span.set_attribute("query_length", len(query))

    # Retrieval
    with tracer.start_as_current_span("retrieval"):
        start = time.time()
        docs = retrieve(query)
        retrieval_latency.record((time.time() - start) * 1000)
        span.set_attribute("n_docs_retrieved", len(docs))

    # Generation
    with tracer.start_as_current_span("generation"):
        start = time.time()
        answer = generate(query, docs)
        generation_latency.record((time.time() - start) * 1000)

    # Verification
    if not is_grounded(answer, docs):
        hallucination_counter.add(1)
        span.set_attribute("hallucination_detected", True)

    return answer
```

## 3.8 Summary and Key Takeaways

**Core Principles:**

1. **Context Positioning**: Place critical info at start/end to avoid "lost in the middle"
2. **Chunking Strategy**: Balance semantic coherence with token limits
3. **Advanced Retrieval**: HyDE for complex queries, RAPTOR for hierarchical docs, Self-RAG for selective retrieval
4. **Hallucination Mitigation**: Multi-stage verification with NLI, LLM judges, and citations
5. **Production Readiness**: Hybrid search, re-ranking, comprehensive monitoring

**Empirical Findings:**

| Technique | Improvement | Use Case | Cost Multiplier |
|-----------|-------------|----------|----------------|
| Basic RAG | +10-20pp | General QA | 1.5× |
| HyDE | +5-8pp | Technical domains | 2× |
| RAPTOR | +5-8pp | Long documents | 3× (indexing) |
| Self-RAG | +8-11pp | Fact-checking | 2.5× |

**Decision Matrix:**

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple QA, cost-sensitive | Basic RAG + BM25 |
| Technical queries | HyDE + Hybrid Search |
| Long documents (books, manuals) | RAPTOR |
| Fact-checking, high-stakes | Self-RAG + Verification |
| Production at scale | Hybrid + Re-ranking + Monitoring |

**Next Steps:**

Chapter 4 covers platform-specific implementations for self-hosted models (vLLM, llama.cpp, Ollama).

## 3.9 Exercises

1. Implement basic RAG with chunking and evaluate on SQuAD
2. Compare HyDE vs standard retrieval on technical QA dataset
3. Build RAPTOR tree for a textbook chapter, measure indexing time
4. Implement hallucination detection with NLI and LLM judges
5. Design monitoring dashboard for production RAG system

## References

[1] Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). "Lost in the Middle: How Language Models Use Long Contexts." *arXiv preprint arXiv:2307.03172*.

[2] Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Rocktäschel, T. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." *Advances in Neural Information Processing Systems (NeurIPS)*, 33, 9459-9474.

[3] Gao, L., Ma, X., Lin, J., & Callan, J. (2022). "Precise Zero-Shot Dense Retrieval without Relevance Labels." *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (ACL)*, 1762-1777.

[4] Sarthi, P., Abdullah, S., Tuli, A., Khanna, S., Goldie, A., & Manning, C. D. (2024). "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval." *arXiv preprint arXiv:2401.18059*.

[5] Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. (2023). "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection." *arXiv preprint arXiv:2310.11511*.

---

**End of Chapter 3**
