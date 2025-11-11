#!/usr/bin/env python3
"""
HyDE (Hypothetical Document Embeddings) RAG Implementation
Chapter 3: Context Engineering for Long Inputs & RAG

Compares standard RAG vs HyDE-enhanced RAG for retrieval quality.

Usage:
    python hyde_rag.py --query "How does PagedAttention improve vLLM performance?" --top_k 5
"""

import argparse
import json
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class Document:
    """Document with content and metadata."""
    id: str
    content: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# Sample documents for demonstration
SAMPLE_DOCUMENTS = [
    Document(
        id="doc1",
        content="PagedAttention is a memory management technique for serving large language models. It divides the KV cache into blocks, enabling efficient memory allocation and sharing across requests. This approach reduces memory waste and improves throughput by 2-3x.",
        metadata={"source": "vLLM paper", "year": 2023}
    ),
    Document(
        id="doc2",
        content="vLLM is a high-throughput serving system for LLMs. Key features include continuous batching, optimized CUDA kernels, and PagedAttention. It achieves 20x higher throughput compared to baseline HuggingFace implementations.",
        metadata={"source": "vLLM docs", "year": 2023}
    ),
    Document(
        id="doc3",
        content="Transformer models use attention mechanisms that require storing key-value pairs for each token. For long sequences, the KV cache can consume gigabytes of memory. Efficient management is critical for production serving.",
        metadata={"source": "Attention paper", "year": 2017}
    ),
    Document(
        id="doc4",
        content="Model quantization reduces memory footprint by using lower precision (INT8, INT4). While this saves memory, it doesn't address the fundamental memory fragmentation issues that PagedAttention solves.",
        metadata={"source": "Quantization survey", "year": 2022}
    ),
    Document(
        id="doc5",
        content="Continuous batching allows new requests to join an existing batch dynamically, improving GPU utilization. Combined with PagedAttention, vLLM achieves state-of-the-art serving performance.",
        metadata={"source": "vLLM blog", "year": 2023}
    ),
]


def mock_embed(text: str) -> np.ndarray:
    """Mock embedding function using simple hash-based vectors."""
    # In production, use actual embedding model like OpenAI, Sentence-Transformers, etc.
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    np.random.seed(hash_val % (2**32))
    embedding = np.random.randn(384)  # 384-dim vector
    return embedding / np.linalg.norm(embedding)  # Normalize


def mock_llm_generate(prompt: str, max_tokens: int = 200) -> str:
    """Mock LLM generation for hypothesis creation."""
    # In production, use actual LLM API
    if "hypothesis" in prompt.lower() or "hypothetical" in prompt.lower():
        # Generate plausible hypothesis based on query
        if "PagedAttention" in prompt:
            return """PagedAttention is a novel memory management technique introduced in vLLM
that addresses memory fragmentation issues in LLM serving. By dividing the key-value cache into
fixed-size blocks (similar to virtual memory paging), it enables efficient memory allocation
and sharing across multiple requests. This approach significantly reduces memory waste and
improves serving throughput by 2-3x compared to naive implementations. The technique allows
for dynamic memory allocation and better GPU utilization, especially in scenarios with varying
sequence lengths."""
        else:
            return "This is a technical concept related to machine learning systems."

    # Standard generation
    return "Generated answer based on retrieved context."


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class StandardRAG:
    """Standard RAG: embed query, retrieve, generate."""

    def __init__(self, documents: List[Document]):
        self.documents = documents
        # Pre-compute document embeddings
        self.doc_embeddings = {
            doc.id: mock_embed(doc.content)
            for doc in documents
        }

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """Retrieve top-k documents by embedding similarity."""
        query_embedding = mock_embed(query)

        # Compute similarities
        similarities = []
        for doc in self.documents:
            doc_embedding = self.doc_embeddings[doc.id]
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))

        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def query(self, question: str, top_k: int = 3) -> Dict:
        """End-to-end RAG query."""
        # Retrieve
        retrieved = self.retrieve(question, top_k=top_k)

        # Build context
        context = "\n\n".join([
            f"[{i+1}] {doc.content}"
            for i, (doc, score) in enumerate(retrieved)
        ])

        # Generate (mock)
        answer = f"Based on the retrieved documents: {context[:100]}..."

        return {
            "question": question,
            "answer": answer,
            "retrieved_docs": [
                {"id": doc.id, "score": float(score), "content": doc.content[:100]}
                for doc, score in retrieved
            ],
            "method": "standard"
        }


class HyDERAG(StandardRAG):
    """HyDE-enhanced RAG: generate hypothesis, embed it, retrieve."""

    def generate_hypothesis(self, query: str) -> str:
        """Generate hypothetical answer for better retrieval."""
        hypothesis_prompt = f"""Generate a detailed, hypothetical answer to this question.
Focus on including technical terms and concepts that would appear in relevant documents.
Do not worry about accuracy - the goal is to match the vocabulary of actual documents.

Question: {query}

Hypothetical Answer:"""

        hypothesis = mock_llm_generate(hypothesis_prompt, max_tokens=200)
        return hypothesis

    def retrieve_with_hyde(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """Retrieve using HyDE: embed hypothetical answer instead of query."""
        # Generate hypothesis
        hypothesis = self.generate_hypothesis(query)
        print(f"  [HyDE] Generated hypothesis: {hypothesis[:100]}...")

        # Embed hypothesis instead of query
        hypothesis_embedding = mock_embed(hypothesis)

        # Compute similarities
        similarities = []
        for doc in self.documents:
            doc_embedding = self.doc_embeddings[doc.id]
            similarity = cosine_similarity(hypothesis_embedding, doc_embedding)
            similarities.append((doc, similarity))

        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def query(self, question: str, top_k: int = 3) -> Dict:
        """End-to-end HyDE-RAG query."""
        # HyDE retrieval
        retrieved = self.retrieve_with_hyde(question, top_k=top_k)

        # Build context
        context = "\n\n".join([
            f"[{i+1}] {doc.content}"
            for i, (doc, score) in enumerate(retrieved)
        ])

        # Generate (mock)
        answer = f"Based on the retrieved documents: {context[:100]}..."

        return {
            "question": question,
            "answer": answer,
            "retrieved_docs": [
                {"id": doc.id, "score": float(score), "content": doc.content[:100]}
                for doc, score in retrieved
            ],
            "method": "HyDE"
        }


def evaluate_retrieval_quality(
    retrieved_docs: List[Dict],
    relevant_doc_ids: List[str]
) -> Dict:
    """Evaluate retrieval quality metrics."""
    retrieved_ids = [doc["id"] for doc in retrieved_docs]

    # Precision@k
    relevant_retrieved = set(retrieved_ids) & set(relevant_doc_ids)
    precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0.0

    # Recall
    recall = len(relevant_retrieved) / len(relevant_doc_ids) if relevant_doc_ids else 0.0

    # F1
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_doc_ids:
            mrr = 1.0 / (i + 1)
            break

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mrr": mrr
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare Standard RAG vs HyDE RAG"
    )
    parser.add_argument("--query", type=str,
                       default="How does PagedAttention improve vLLM performance?",
                       help="Query to test")
    parser.add_argument("--top_k", type=int, default=3,
                       help="Number of documents to retrieve")
    parser.add_argument("--output", type=str, help="Output JSON file")
    args = parser.parse_args()

    print("=" * 60)
    print("HyDE RAG Comparison")
    print("=" * 60)
    print(f"Query: {args.query}")
    print(f"Top-K: {args.top_k}")
    print()

    # Ground truth relevant docs (manually labeled for demo)
    relevant_docs = ["doc1", "doc2", "doc5"]  # PagedAttention-related docs

    # Standard RAG
    print("Running Standard RAG...")
    standard_rag = StandardRAG(SAMPLE_DOCUMENTS)
    standard_result = standard_rag.query(args.query, top_k=args.top_k)

    print("\nStandard RAG Retrieved:")
    for i, doc in enumerate(standard_result["retrieved_docs"], 1):
        print(f"  {i}. {doc['id']} (score: {doc['score']:.3f})")
        print(f"     {doc['content']}...")

    standard_metrics = evaluate_retrieval_quality(
        standard_result["retrieved_docs"],
        relevant_docs
    )

    # HyDE RAG
    print("\n" + "-" * 60)
    print("Running HyDE RAG...")
    hyde_rag = HyDERAG(SAMPLE_DOCUMENTS)
    hyde_result = hyde_rag.query(args.query, top_k=args.top_k)

    print("\nHyDE RAG Retrieved:")
    for i, doc in enumerate(hyde_result["retrieved_docs"], 1):
        print(f"  {i}. {doc['id']} (score: {doc['score']:.3f})")
        print(f"     {doc['content']}...")

    hyde_metrics = evaluate_retrieval_quality(
        hyde_result["retrieved_docs"],
        relevant_docs
    )

    # Comparison
    print("\n" + "=" * 60)
    print("Comparison")
    print("=" * 60)
    print(f"{'Metric':<20} {'Standard RAG':<15} {'HyDE RAG':<15} {'Improvement':<15}")
    print("-" * 60)

    for metric in ["precision", "recall", "f1", "mrr"]:
        standard_val = standard_metrics[metric]
        hyde_val = hyde_metrics[metric]
        improvement = hyde_val - standard_val
        print(f"{metric.capitalize():<20} {standard_val:<15.3f} {hyde_val:<15.3f} {improvement:+.3f}")

    print("=" * 60)

    # Summary
    if hyde_metrics["f1"] > standard_metrics["f1"]:
        print("\n✓ HyDE improves retrieval quality!")
    else:
        print("\n✗ Standard RAG performed better for this query.")

    # Save results
    if args.output:
        results = {
            "query": args.query,
            "top_k": args.top_k,
            "standard_rag": {
                "retrieved": standard_result["retrieved_docs"],
                "metrics": standard_metrics
            },
            "hyde_rag": {
                "retrieved": hyde_result["retrieved_docs"],
                "metrics": hyde_metrics
            },
            "improvement": {
                metric: hyde_metrics[metric] - standard_metrics[metric]
                for metric in ["precision", "recall", "f1", "mrr"]
            }
        }

        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
