#!/usr/bin/env python3
"""
RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)
Chapter 3: Context Engineering for Long Inputs & RAG

Builds hierarchical summarization tree over documents for multi-level retrieval.

Usage:
    python raptor_indexing.py --documents docs/*.txt --query "What is the main topic?" --max_levels 3
"""

import argparse
import json
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
import hashlib


@dataclass
class RAPTORNode:
    """Node in RAPTOR tree."""
    id: str
    text: str
    level: int
    embedding: np.ndarray
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


def mock_embed(text: str) -> np.ndarray:
    """Mock embedding function using hash-based vectors."""
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    np.random.seed(hash_val % (2**32))
    embedding = np.random.randn(384)
    return embedding / np.linalg.norm(embedding)


def mock_llm_summarize(texts: List[str], max_tokens: int = 300) -> str:
    """Mock LLM summarization."""
    # In production, use actual LLM
    combined_length = sum(len(t) for t in texts)
    avg_length = combined_length // len(texts) if texts else 0

    # Generate mock summary based on input characteristics
    if any("PagedAttention" in t or "vLLM" in t for t in texts):
        return f"""This cluster discusses advanced LLM serving techniques, particularly
focusing on memory management and performance optimization. Key topics include PagedAttention
for efficient KV cache management, continuous batching for improved throughput, and
specialized serving systems like vLLM. The texts cover both theoretical foundations
and practical implementation details. ({len(texts)} documents, ~{avg_length} chars avg)"""
    elif any("RAG" in t or "retrieval" in t.lower() for t in texts):
        return f"""This cluster covers retrieval-augmented generation (RAG) systems and
related techniques. Topics include document chunking, embedding strategies, hybrid search
approaches, and methods for improving retrieval quality. The texts discuss both basic
RAG architectures and advanced variants. ({len(texts)} documents)"""
    else:
        return f"""Summary of {len(texts)} related documents covering interconnected topics
in machine learning and natural language processing. Average document length: ~{avg_length} characters."""


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class SimpleKMeans:
    """Simple k-means clustering for RAPTOR."""

    def __init__(self, n_clusters: int, max_iters: int = 10, random_seed: int = 42):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.random_seed = random_seed
        self.centroids = None

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings and return cluster assignments."""
        n_samples = len(embeddings)

        # Initialize centroids randomly
        np.random.seed(self.random_seed)
        centroid_indices = np.random.choice(n_samples, self.n_clusters, replace=False)
        self.centroids = embeddings[centroid_indices].copy()

        # Iterate
        labels = np.zeros(n_samples, dtype=int)
        for _ in range(self.max_iters):
            # Assign to nearest centroid
            for i, emb in enumerate(embeddings):
                distances = [np.linalg.norm(emb - c) for c in self.centroids]
                labels[i] = np.argmin(distances)

            # Update centroids
            for k in range(self.n_clusters):
                cluster_points = embeddings[labels == k]
                if len(cluster_points) > 0:
                    self.centroids[k] = cluster_points.mean(axis=0)

        return labels


class RAPTOR:
    """
    RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval.

    Builds hierarchical summarization tree over documents.
    """

    def __init__(
        self,
        n_clusters: int = 5,
        max_levels: int = 3,
        min_cluster_size: int = 2
    ):
        self.n_clusters = n_clusters
        self.max_levels = max_levels
        self.min_cluster_size = min_cluster_size
        self.tree = {}  # level -> list of nodes
        self.node_index = {}  # id -> node

    def build_tree(self, documents: List[str]) -> Dict:
        """
        Build RAPTOR tree from documents.

        Args:
            documents: List of document texts

        Returns:
            Tree statistics
        """
        print(f"Building RAPTOR tree from {len(documents)} documents...")

        # Level 0: Base documents
        level_0_nodes = []
        for i, doc in enumerate(documents):
            node = RAPTORNode(
                id=f"L0_N{i}",
                text=doc,
                level=0,
                embedding=mock_embed(doc),
                metadata={"doc_index": i, "is_leaf": True}
            )
            level_0_nodes.append(node)
            self.node_index[node.id] = node

        self.tree[0] = level_0_nodes
        print(f"  Level 0: {len(level_0_nodes)} nodes")

        # Build higher levels
        current_nodes = level_0_nodes
        for level in range(1, self.max_levels + 1):
            if len(current_nodes) <= 1:
                print(f"  Stopping at level {level-1} (only 1 node remaining)")
                break

            next_nodes = self._build_next_level(current_nodes, level)

            if not next_nodes or len(next_nodes) >= len(current_nodes):
                print(f"  Stopping at level {level-1} (no effective clustering)")
                break

            self.tree[level] = next_nodes
            print(f"  Level {level}: {len(next_nodes)} nodes")
            current_nodes = next_nodes

        # Statistics
        total_nodes = sum(len(nodes) for nodes in self.tree.values())
        stats = {
            "total_levels": len(self.tree),
            "total_nodes": total_nodes,
            "nodes_per_level": {level: len(nodes) for level, nodes in self.tree.items()},
            "base_documents": len(documents)
        }

        return stats

    def _build_next_level(self, nodes: List[RAPTORNode], level: int) -> List[RAPTORNode]:
        """Build next level of tree by clustering and summarizing."""
        if len(nodes) < self.min_cluster_size:
            return []

        # Extract embeddings
        embeddings = np.array([node.embedding for node in nodes])

        # Determine number of clusters
        n_clusters = min(self.n_clusters, len(nodes) // 2)
        if n_clusters < 1:
            return []

        # Cluster
        kmeans = SimpleKMeans(n_clusters=n_clusters, random_seed=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Create summary nodes for each cluster
        next_nodes = []
        for cluster_id in range(n_clusters):
            cluster_node_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]

            if len(cluster_node_indices) < self.min_cluster_size:
                continue  # Skip small clusters

            cluster_nodes = [nodes[i] for i in cluster_node_indices]
            cluster_texts = [node.text for node in cluster_nodes]

            # Generate summary
            summary_text = mock_llm_summarize(cluster_texts)

            # Create summary node
            summary_node = RAPTORNode(
                id=f"L{level}_N{len(next_nodes)}",
                text=summary_text,
                level=level,
                embedding=mock_embed(summary_text),
                children_ids=[node.id for node in cluster_nodes],
                metadata={
                    "cluster_id": cluster_id,
                    "n_children": len(cluster_nodes),
                    "is_summary": True
                }
            )

            next_nodes.append(summary_node)
            self.node_index[summary_node.id] = summary_node

        return next_nodes

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        level_weights: Dict[int, float] = None
    ) -> List[Tuple[RAPTORNode, float]]:
        """
        Multi-level retrieval from RAPTOR tree.

        Args:
            query: Query text
            top_k: Number of results to return
            level_weights: Weight for each level (default: equal)

        Returns:
            List of (node, score) tuples
        """
        query_embedding = mock_embed(query)

        # Default: equal weights for all levels
        if level_weights is None:
            level_weights = {level: 1.0 for level in self.tree.keys()}

        # Search all levels
        all_candidates = []
        for level, nodes in self.tree.items():
            weight = level_weights.get(level, 1.0)

            for node in nodes:
                similarity = cosine_similarity(query_embedding, node.embedding)
                weighted_score = similarity * weight

                all_candidates.append((node, weighted_score, similarity, level))

        # Sort by weighted score
        all_candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top-k with scores
        results = [
            (node, score) for node, score, _, _ in all_candidates[:top_k]
        ]

        return results

    def print_tree_structure(self):
        """Print tree structure for visualization."""
        print("\n" + "=" * 60)
        print("RAPTOR Tree Structure")
        print("=" * 60)

        for level in sorted(self.tree.keys(), reverse=True):
            nodes = self.tree[level]
            print(f"\nLevel {level}: {len(nodes)} nodes")

            for i, node in enumerate(nodes[:3]):  # Show first 3 per level
                indent = "  " * level
                print(f"{indent}├─ {node.id}: {node.text[:80]}...")
                if node.children_ids:
                    print(f"{indent}   └─ Children: {len(node.children_ids)}")

            if len(nodes) > 3:
                print(f"  ... and {len(nodes) - 3} more nodes")

        print("=" * 60)


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    "PagedAttention divides the KV cache into blocks for efficient memory management in LLM serving.",
    "vLLM achieves 20x higher throughput compared to baseline implementations using PagedAttention.",
    "Continuous batching allows dynamic request joining to improve GPU utilization.",
    "The transformer attention mechanism requires storing key-value pairs for each token.",
    "Model quantization reduces precision to INT8 or INT4 to save memory.",
    "RAG combines retrieval systems with generative models for grounded responses.",
    "HyDE generates hypothetical documents to improve retrieval quality.",
    "RAPTOR builds hierarchical summaries for multi-level document retrieval.",
    "Self-RAG uses reflection tokens to decide when to retrieve documents.",
    "Hallucination detection uses NLI models to verify answer grounding.",
]


def main():
    parser = argparse.ArgumentParser(
        description="RAPTOR tree indexing and retrieval"
    )
    parser.add_argument("--n_clusters", type=int, default=3,
                       help="Number of clusters per level")
    parser.add_argument("--max_levels", type=int, default=3,
                       help="Maximum tree depth")
    parser.add_argument("--query", type=str,
                       default="How does PagedAttention work?",
                       help="Query for retrieval")
    parser.add_argument("--top_k", type=int, default=5,
                       help="Number of results to retrieve")
    parser.add_argument("--output", type=str,
                       help="Output JSON file")
    args = parser.parse_args()

    print("=" * 60)
    print("RAPTOR: Hierarchical Retrieval Demo")
    print("=" * 60)
    print(f"Documents: {len(SAMPLE_DOCUMENTS)}")
    print(f"Clusters per level: {args.n_clusters}")
    print(f"Max levels: {args.max_levels}")
    print()

    # Build RAPTOR tree
    raptor = RAPTOR(
        n_clusters=args.n_clusters,
        max_levels=args.max_levels
    )

    stats = raptor.build_tree(SAMPLE_DOCUMENTS)

    print(f"\nTree Statistics:")
    print(f"  Total levels: {stats['total_levels']}")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Nodes per level: {stats['nodes_per_level']}")

    # Print tree structure
    raptor.print_tree_structure()

    # Retrieve
    print(f"\nQuery: {args.query}")
    print(f"Retrieving top-{args.top_k} results...\n")

    results = raptor.retrieve(args.query, top_k=args.top_k)

    print("Results:")
    print("-" * 60)
    for i, (node, score) in enumerate(results, 1):
        print(f"{i}. [{node.level}] {node.id} (score: {score:.3f})")
        print(f"   {node.text[:100]}...")
        if node.children_ids:
            print(f"   Children: {len(node.children_ids)} nodes")
        print()

    # Comparison: flat retrieval vs RAPTOR
    print("=" * 60)
    print("Comparison: Flat vs RAPTOR Retrieval")
    print("=" * 60)

    # Flat retrieval (level 0 only)
    flat_results = raptor.retrieve(
        args.query,
        top_k=args.top_k,
        level_weights={0: 1.0, 1: 0.0, 2: 0.0}
    )

    print(f"\nFlat retrieval (base documents only):")
    for i, (node, score) in enumerate(flat_results[:3], 1):
        print(f"  {i}. {node.id}: {node.text[:60]}... ({score:.3f})")

    print(f"\nRAPTOR retrieval (multi-level):")
    for i, (node, score) in enumerate(results[:3], 1):
        level_marker = "📄" if node.level == 0 else "📑"
        print(f"  {i}. {level_marker} {node.id}: {node.text[:60]}... ({score:.3f})")

    # Benefits analysis
    high_level_nodes = [n for n, s in results if n.level > 0]
    if high_level_nodes:
        print(f"\n✓ RAPTOR retrieved {len(high_level_nodes)} high-level summaries")
        print(f"  (Provides broader context and connections)")
    else:
        print(f"\n→ RAPTOR retrieved only base documents for this query")

    print("=" * 60)

    # Save results
    if args.output:
        output_data = {
            "query": args.query,
            "tree_stats": stats,
            "results": [
                {
                    "rank": i,
                    "node_id": node.id,
                    "level": node.level,
                    "score": float(score),
                    "text": node.text[:200],
                    "is_summary": node.metadata.get("is_summary", False),
                    "n_children": len(node.children_ids)
                }
                for i, (node, score) in enumerate(results, 1)
            ]
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
