#!/usr/bin/env python3
"""
Self-RAG: Self-Reflective Retrieval-Augmented Generation
Chapter 3: Context Engineering for Long Inputs & RAG

Demonstrates Self-RAG with reflection tokens: [Retrieve], [IsRel], [IsSup], [IsUse]

Usage:
    python self_rag_demo.py --query "What is PagedAttention?" --relevance_threshold 0.7
"""

import argparse
import json
import hashlib
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ReflectionToken(Enum):
    """Self-RAG reflection tokens."""
    RETRIEVE = "[Retrieve]"
    IS_RELEVANT = "[IsRel]"
    IS_SUPPORTED = "[IsSup]"
    IS_USEFUL = "[IsUse]"


@dataclass
class Document:
    """Document with metadata."""
    id: str
    content: str
    metadata: Dict


@dataclass
class SelfRAGResult:
    """Result from Self-RAG query."""
    query: str
    answer: str
    should_retrieve: bool
    retrieved_docs: List[Document]
    filtered_docs: List[Document]
    relevance_scores: Dict[str, float]
    support_score: Optional[float]
    usefulness_score: Optional[float]
    confidence: float
    reasoning: List[str]


# Sample documents
SAMPLE_DOCS = [
    Document(
        id="doc1",
        content="PagedAttention is a memory management algorithm for LLM serving that divides the KV cache into fixed-size blocks. This approach, inspired by virtual memory paging in operating systems, reduces memory fragmentation and enables efficient memory sharing across requests. vLLM uses PagedAttention to achieve 2-3x higher throughput compared to baseline implementations.",
        metadata={"source": "vLLM paper", "domain": "systems"}
    ),
    Document(
        id="doc2",
        content="Transformers use self-attention mechanisms that require storing key and value vectors for each token. For long sequences, this KV cache can consume significant memory. Efficient management is critical for production deployment.",
        metadata={"source": "Attention paper", "domain": "ml-theory"}
    ),
    Document(
        id="doc3",
        content="Python is a high-level programming language known for its readability and versatility. It's widely used in web development, data science, and machine learning applications.",
        metadata={"source": "Python docs", "domain": "programming"}
    ),
    Document(
        id="doc4",
        content="Model quantization reduces neural network precision from FP32 to INT8 or INT4, decreasing memory footprint and increasing inference speed. While effective for compression, quantization doesn't address memory fragmentation issues.",
        metadata={"source": "Quantization survey", "domain": "ml-optimization"}
    ),
    Document(
        id="doc5",
        content="Continuous batching is a dynamic batching strategy where new requests can join an existing batch during generation. This improves GPU utilization and reduces latency compared to static batching.",
        metadata={"source": "Batching techniques", "domain": "systems"}
    ),
]


def mock_embed(text: str) -> np.ndarray:
    """Mock embedding function."""
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    np.random.seed(hash_val % (2**32))
    embedding = np.random.randn(384)
    return embedding / np.linalg.norm(embedding)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class SelfRAG:
    """
    Self-RAG: Self-Reflective Retrieval-Augmented Generation.

    Uses reflection tokens to decide when to retrieve, filter relevance,
    and verify answer quality.
    """

    def __init__(self, documents: List[Document]):
        self.documents = documents
        # Pre-compute embeddings
        self.doc_embeddings = {
            doc.id: mock_embed(doc.content)
            for doc in documents
        }

    def decide_retrieve(self, query: str) -> Tuple[bool, float, str]:
        """
        [Retrieve] reflection: Should we retrieve documents?

        Returns: (should_retrieve, confidence, reasoning)
        """
        query_lower = query.lower()

        # Heuristics for retrieval decision
        specific_terms = ["how", "what", "why", "when", "where", "who"]
        has_question_word = any(term in query_lower for term in specific_terms)

        technical_indicators = [
            "pagedattention", "vllm", "algorithm", "method", "technique",
            "system", "architecture", "implementation"
        ]
        is_technical = any(term in query_lower for term in technical_indicators)

        # Decision logic
        if is_technical or has_question_word:
            confidence = 0.9 if is_technical else 0.7
            reasoning = "Query requires factual/technical information"
            return True, confidence, reasoning
        else:
            reasoning = "Query appears to be conversational or general"
            return False, 0.3, reasoning

    def assess_relevance(
        self,
        query: str,
        document: Document
    ) -> Tuple[float, str]:
        """
        [IsRel] reflection: Is document relevant to query?

        Returns: (relevance_score, reasoning)
        """
        query_embedding = mock_embed(query)
        doc_embedding = self.doc_embeddings[document.id]

        # Embedding similarity
        similarity = cosine_similarity(query_embedding, doc_embedding)

        # Keyword overlap bonus
        query_words = set(query.lower().split())
        doc_words = set(document.content.lower().split())
        overlap = len(query_words & doc_words) / len(query_words) if query_words else 0

        # Combined score
        relevance_score = 0.7 * similarity + 0.3 * overlap

        # Reasoning
        if relevance_score > 0.7:
            reasoning = f"High relevance (sim={similarity:.2f}, overlap={overlap:.2f})"
        elif relevance_score > 0.5:
            reasoning = f"Moderate relevance (sim={similarity:.2f})"
        else:
            reasoning = f"Low relevance (sim={similarity:.2f})"

        return relevance_score, reasoning

    def check_support(
        self,
        answer: str,
        context_docs: List[Document]
    ) -> Tuple[float, str]:
        """
        [IsSup] reflection: Is answer supported by context?

        Returns: (support_score, reasoning)
        """
        if not context_docs:
            return 0.0, "No context documents provided"

        # Extract key claims from answer (simplified)
        answer_words = set(answer.lower().split())
        context_text = " ".join([doc.content for doc in context_docs]).lower()
        context_words = set(context_text.split())

        # Check word overlap
        overlap = len(answer_words & context_words) / len(answer_words) if answer_words else 0

        # Heuristic support score
        if overlap > 0.7:
            support_score = 0.9
            reasoning = f"Strong support ({overlap:.0%} word overlap)"
        elif overlap > 0.5:
            support_score = 0.7
            reasoning = f"Moderate support ({overlap:.0%} word overlap)"
        elif overlap > 0.3:
            support_score = 0.5
            reasoning = f"Weak support ({overlap:.0%} word overlap)"
        else:
            support_score = 0.2
            reasoning = f"Minimal support ({overlap:.0%} word overlap)"

        return support_score, reasoning

    def assess_usefulness(self, answer: str, query: str) -> Tuple[float, str]:
        """
        [IsUse] reflection: Is answer useful for the query?

        Returns: (usefulness_score, reasoning)
        """
        # Heuristics for usefulness
        answer_length = len(answer.split())

        if answer_length < 5:
            return 0.3, "Answer is very brief"
        elif answer_length < 20:
            return 0.6, "Answer is concise"
        elif answer_length < 100:
            return 0.9, "Answer is comprehensive"
        else:
            return 0.7, "Answer is very detailed"

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Retrieve top-k documents by similarity."""
        query_embedding = mock_embed(query)

        similarities = []
        for doc in self.documents:
            doc_embedding = self.doc_embeddings[doc.id]
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def generate_answer(
        self,
        query: str,
        context_docs: List[Document]
    ) -> str:
        """Generate answer from query and context (mock)."""
        if not context_docs:
            return "I don't have enough information to answer this question."

        # Mock generation based on context
        context_text = " ".join([doc.content[:100] for doc in context_docs])

        if "PagedAttention" in query or "pagedattention" in query.lower():
            return """PagedAttention is a memory management technique for LLM serving that divides
the KV cache into fixed-size blocks. This approach reduces memory fragmentation and enables
efficient memory sharing across requests, resulting in 2-3x higher throughput compared to
baseline implementations."""
        else:
            return f"Based on the context: {context_text[:150]}..."

    def query(
        self,
        question: str,
        relevance_threshold: float = 0.6,
        support_threshold: float = 0.5
    ) -> SelfRAGResult:
        """
        End-to-end Self-RAG query with reflection.

        Args:
            question: User query
            relevance_threshold: Minimum relevance score to keep document
            support_threshold: Minimum support score for high confidence

        Returns:
            SelfRAGResult with full reflection trace
        """
        reasoning_trace = []

        # Step 1: Decide if retrieval needed
        should_retrieve, retrieve_conf, retrieve_reason = self.decide_retrieve(question)
        reasoning_trace.append(f"[Retrieve]: {should_retrieve} ({retrieve_reason})")

        if not should_retrieve:
            # Direct answer without retrieval
            answer = self.generate_answer(question, [])
            return SelfRAGResult(
                query=question,
                answer=answer,
                should_retrieve=False,
                retrieved_docs=[],
                filtered_docs=[],
                relevance_scores={},
                support_score=None,
                usefulness_score=None,
                confidence=0.5,
                reasoning=reasoning_trace
            )

        # Step 2: Retrieve documents
        retrieved = self.retrieve(question, top_k=5)
        retrieved_docs = [doc for doc, _ in retrieved]
        reasoning_trace.append(f"Retrieved {len(retrieved_docs)} documents")

        # Step 3: Filter by relevance
        relevance_scores = {}
        filtered_docs = []

        for doc in retrieved_docs:
            rel_score, rel_reason = self.assess_relevance(question, doc)
            relevance_scores[doc.id] = rel_score

            if rel_score >= relevance_threshold:
                filtered_docs.append(doc)
                reasoning_trace.append(f"[IsRel] {doc.id}: {rel_score:.2f} - KEEP ({rel_reason})")
            else:
                reasoning_trace.append(f"[IsRel] {doc.id}: {rel_score:.2f} - FILTER ({rel_reason})")

        if not filtered_docs:
            answer = "After filtering, no relevant documents remain to answer this question."
            return SelfRAGResult(
                query=question,
                answer=answer,
                should_retrieve=True,
                retrieved_docs=retrieved_docs,
                filtered_docs=[],
                relevance_scores=relevance_scores,
                support_score=0.0,
                usefulness_score=0.0,
                confidence=0.2,
                reasoning=reasoning_trace
            )

        # Step 4: Generate answer
        answer = self.generate_answer(question, filtered_docs)
        reasoning_trace.append(f"Generated answer ({len(answer.split())} words)")

        # Step 5: Check support
        support_score, support_reason = self.check_support(answer, filtered_docs)
        reasoning_trace.append(f"[IsSup]: {support_score:.2f} - {support_reason}")

        # Step 6: Assess usefulness
        usefulness_score, usefulness_reason = self.assess_usefulness(answer, question)
        reasoning_trace.append(f"[IsUse]: {usefulness_score:.2f} - {usefulness_reason}")

        # Step 7: Compute overall confidence
        confidence = (
            retrieve_conf * 0.2 +
            (sum(relevance_scores.values()) / len(relevance_scores) if relevance_scores else 0) * 0.3 +
            support_score * 0.3 +
            usefulness_score * 0.2
        )

        return SelfRAGResult(
            query=question,
            answer=answer,
            should_retrieve=should_retrieve,
            retrieved_docs=retrieved_docs,
            filtered_docs=filtered_docs,
            relevance_scores=relevance_scores,
            support_score=support_score,
            usefulness_score=usefulness_score,
            confidence=confidence,
            reasoning=reasoning_trace
        )


def print_result(result: SelfRAGResult):
    """Pretty-print Self-RAG result."""
    print("\n" + "=" * 60)
    print("Self-RAG Query Result")
    print("=" * 60)
    print(f"\nQuery: {result.query}")
    print(f"\nShould Retrieve: {'✓ Yes' if result.should_retrieve else '✗ No'}")

    if result.should_retrieve:
        print(f"\nRetrieved Documents: {len(result.retrieved_docs)}")
        print(f"Relevant Documents: {len(result.filtered_docs)}")

        print("\nRelevance Filtering:")
        for doc_id, score in result.relevance_scores.items():
            status = "✓" if any(d.id == doc_id for d in result.filtered_docs) else "✗"
            print(f"  {status} {doc_id}: {score:.3f}")

    print(f"\n{'─' * 60}")
    print("Answer:")
    print(f"{'─' * 60}")
    print(result.answer)
    print(f"{'─' * 60}")

    print(f"\nSupport Score: {result.support_score:.2f}" if result.support_score is not None else "\nSupport Score: N/A")
    print(f"Usefulness Score: {result.usefulness_score:.2f}" if result.usefulness_score is not None else "Usefulness Score: N/A")
    print(f"Overall Confidence: {result.confidence:.2f}")

    print(f"\n{'─' * 60}")
    print("Reflection Trace:")
    print(f"{'─' * 60}")
    for i, step in enumerate(result.reasoning, 1):
        print(f"{i}. {step}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Self-RAG: Self-Reflective RAG with reflection tokens"
    )
    parser.add_argument("--query", type=str,
                       default="What is PagedAttention?",
                       help="Query to process")
    parser.add_argument("--relevance_threshold", type=float, default=0.6,
                       help="Minimum relevance score to keep document")
    parser.add_argument("--support_threshold", type=float, default=0.5,
                       help="Minimum support score for high confidence")
    parser.add_argument("--output", type=str,
                       help="Output JSON file")
    args = parser.parse_args()

    print("=" * 60)
    print("Self-RAG Demo")
    print("=" * 60)
    print(f"Documents: {len(SAMPLE_DOCS)}")
    print(f"Relevance Threshold: {args.relevance_threshold}")
    print(f"Support Threshold: {args.support_threshold}")

    # Initialize Self-RAG
    self_rag = SelfRAG(SAMPLE_DOCS)

    # Process query
    result = self_rag.query(
        args.query,
        relevance_threshold=args.relevance_threshold,
        support_threshold=args.support_threshold
    )

    # Print result
    print_result(result)

    # Comparison: with vs without reflection
    print("\n" + "=" * 60)
    print("Comparison: Standard RAG vs Self-RAG")
    print("=" * 60)

    print("\nStandard RAG:")
    print("  - Retrieves all documents")
    print(f"  - Uses all {len(SAMPLE_DOCS)} documents (including irrelevant)")
    print("  - No support verification")
    print("  - Confidence: N/A")

    print("\nSelf-RAG:")
    print(f"  - Selective retrieval: {'Yes' if result.should_retrieve else 'No'}")
    print(f"  - Filtered to {len(result.filtered_docs)}/{len(result.retrieved_docs)} relevant docs")
    print(f"  - Support score: {result.support_score:.2f}" if result.support_score else "  - Support score: N/A")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - ✓ Transparent reasoning with {len(result.reasoning)} steps")

    improvement = len(result.retrieved_docs) - len(result.filtered_docs)
    if improvement > 0:
        print(f"\n✓ Self-RAG filtered out {improvement} irrelevant document(s)")
        print("  (Reduces noise and potential hallucinations)")

    print("=" * 60)

    # Save results
    if args.output:
        output_data = {
            "query": result.query,
            "answer": result.answer,
            "should_retrieve": result.should_retrieve,
            "n_retrieved": len(result.retrieved_docs),
            "n_filtered": len(result.filtered_docs),
            "relevance_scores": result.relevance_scores,
            "support_score": result.support_score,
            "usefulness_score": result.usefulness_score,
            "confidence": result.confidence,
            "reasoning_trace": result.reasoning
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
