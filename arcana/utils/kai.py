"""
Kai DBMS implementation with instant/think modes.

The design keeps compatibility with FiberDBMS while layering hybrid scoring,
optional embeddings, and reranking.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from arcana.utils.fiber import FiberDBMS

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - optional dependency
    SentenceTransformer = None

try:
    import faiss
except ImportError:  # pragma: no cover - optional dependency
    faiss = None


class KaiDBMS(FiberDBMS):
    """Hybrid search with BM25 + optional semantic ranking."""

    def __init__(
        self,
        *,
        mode: str = "instant",
        embed_model: str = "all-MiniLM-L6-v2",
        use_rerank: bool = False,
        candidate_multiplier: int = 6,
        rerank_top_n: int = 30,
    ) -> None:
        super().__init__()
        self.mode = mode
        self.embed_model = embed_model
        self.use_rerank = use_rerank
        self.candidate_multiplier = candidate_multiplier
        self.rerank_top_n = rerank_top_n

        self._bm25_term_freqs: List[Counter] = []
        self._bm25_df: Dict[str, int] = defaultdict(int)
        self._bm25_doc_len: List[int] = []
        self._bm25_avgdl = 0.0

        self._embedder: Optional["SentenceTransformer"] = None
        self._embeddings: Optional["np.ndarray"] = None
        self._faiss_index = None

    def add_entry(self, name: str, content: str, tags: List[str]) -> None:
        super().add_entry(name, content, tags)
        self._add_bm25_entry(content)
        self._add_embedding_entry(content)

    def load_from_file(self, filename: str) -> None:
        super().load_from_file(filename)
        self._rebuild_bm25_index()
        self._rebuild_embeddings()

    def query(self, query: str, top_n: int) -> List[Dict[str, str]]:
        if self.is_empty():
            return []

        query_tokens = self._tokenize(query)
        candidate_count = max(top_n * self.candidate_multiplier, top_n)

        lexical_candidates = self._bm25_candidates(query_tokens, candidate_count)
        semantic_candidates = self._semantic_candidates(query, candidate_count)
        fused = self._fuse_candidates(
            lexical_candidates,
            semantic_candidates,
            lexical_weight=1.2 if self.mode == "instant" else 1.0,
            semantic_weight=1.0 if self.mode == "instant" else 1.2,
        )

        if self.use_rerank:
            fused = self._rerank(query, fused, top_n)

        results = []
        for idx, _score in fused[:top_n]:
            entry = self.database[idx]
            if self.mode == "instant":
                snippet = entry["content"]
            else:
                snippet = self._get_snippet(entry["content"], query_tokens)
            updated_tags = self._update_tags(entry["tags"], entry["content"], query_tokens)
            results.append(
                {
                    "name": entry["name"],
                    "content": snippet,
                    "tags": updated_tags,
                    "index": idx,
                }
            )
        return results

    def _add_bm25_entry(self, content: str) -> None:
        tokens = self._tokenize(content)
        term_counts = Counter(tokens)
        self._bm25_term_freqs.append(term_counts)
        self._bm25_doc_len.append(len(tokens))
        for token in term_counts:
            self._bm25_df[token] += 1
        self._bm25_avgdl = sum(self._bm25_doc_len) / max(1, len(self._bm25_doc_len))

    def _rebuild_bm25_index(self) -> None:
        self._bm25_term_freqs = []
        self._bm25_doc_len = []
        self._bm25_df = defaultdict(int)
        for entry in self.database:
            self._add_bm25_entry(entry["content"])

    def _bm25_candidates(self, query_tokens: List[str], top_k: int) -> List[Tuple[int, float]]:
        if not query_tokens:
            return []

        candidate_indices = set()
        for token in query_tokens:
            if token in self.content_index:
                candidate_indices.update(self.content_index[token])

        scores = []
        N = len(self.database)
        k1 = 1.2
        b = 0.75
        avgdl = self._bm25_avgdl or 1.0

        for idx in candidate_indices:
            term_counts = self._bm25_term_freqs[idx]
            dl = self._bm25_doc_len[idx] or 1
            score = 0.0
            for token in query_tokens:
                tf = term_counts.get(token, 0)
                if tf == 0:
                    continue
                df = self._bm25_df.get(token, 0)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
                denom = tf + k1 * (1 - b + b * dl / avgdl)
                score += idf * (tf * (k1 + 1) / denom)
            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_k]

    def _semantic_candidates(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        if np is None or SentenceTransformer is None:
            return []

        self._ensure_embeddings()
        if self._embeddings is None:
            return []

        query_vec = self._encode_texts([query])
        if query_vec is None:
            return []

        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(query_vec, min(top_k, len(self.database)))
            return [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0]) if idx >= 0]

        query_vec = query_vec[0]
        scores = self._embeddings @ query_vec
        best_idx = np.argsort(-scores)[:top_k]
        return [(int(idx), float(scores[idx])) for idx in best_idx]

    def _fuse_candidates(
        self,
        lexical: List[Tuple[int, float]],
        semantic: List[Tuple[int, float]],
        *,
        lexical_weight: float,
        semantic_weight: float,
    ) -> List[Tuple[int, float]]:
        rank_scores: Dict[int, float] = defaultdict(float)
        k = 60
        for rank, (idx, _score) in enumerate(lexical, start=1):
            rank_scores[idx] += lexical_weight / (k + rank)
        for rank, (idx, _score) in enumerate(semantic, start=1):
            rank_scores[idx] += semantic_weight / (k + rank)

        fused = [(idx, score) for idx, score in rank_scores.items()]
        fused.sort(key=lambda item: item[1], reverse=True)
        return fused

    def _rerank(self, query: str, candidates: List[Tuple[int, float]], top_n: int) -> List[Tuple[int, float]]:
        if not candidates:
            return []
        rerank_limit = min(self.rerank_top_n, len(candidates))
        subset = candidates[:rerank_limit]

        if np is None or SentenceTransformer is None or self._embeddings is None:
            reranked = [
                (idx, self._rate_result(self.database[idx], self._tokenize(query)))
                for idx, _score in subset
            ]
        else:
            query_vec = self._encode_texts([query])
            if query_vec is None:
                return candidates[:top_n]
            query_vec = query_vec[0]
            reranked = []
            for idx, base_score in subset:
                score = float(self._embeddings[idx] @ query_vec)
                reranked.append((idx, base_score + score))

        reranked.sort(key=lambda item: item[1], reverse=True)
        return reranked + candidates[rerank_limit:]

    def _ensure_embeddings(self) -> None:
        if self._embeddings is not None:
            return
        if np is None or SentenceTransformer is None:
            return

        self._embedder = SentenceTransformer(self.embed_model)
        self._rebuild_embeddings()

    def _rebuild_embeddings(self) -> None:
        if np is None or SentenceTransformer is None:
            self._embeddings = None
            self._faiss_index = None
            return
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.embed_model)
        contents = [entry["content"] for entry in self.database]
        if not contents:
            self._embeddings = None
            self._faiss_index = None
            return

        vectors = self._encode_texts(contents)
        if vectors is None:
            self._embeddings = None
            self._faiss_index = None
            return
        self._embeddings = vectors

        if faiss is None:
            self._faiss_index = None
            return
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        self._faiss_index = index

    def _add_embedding_entry(self, content: str) -> None:
        if np is None or SentenceTransformer is None:
            return
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.embed_model)
        vector = self._encode_texts([content])
        if vector is None:
            return

        if self._embeddings is None:
            self._embeddings = vector
        else:
            self._embeddings = np.vstack([self._embeddings, vector])

        if faiss is not None:
            if self._faiss_index is None:
                self._faiss_index = faiss.IndexFlatIP(vector.shape[1])
                self._faiss_index.add(self._embeddings)
            else:
                self._faiss_index.add(vector)

    def _encode_texts(self, texts: Iterable[str]) -> Optional["np.ndarray"]:
        if np is None or self._embedder is None:
            return None
        vectors = self._embedder.encode(list(texts), normalize_embeddings=True)
        return np.asarray(vectors, dtype="float32")


class KaiInstantDBMS(KaiDBMS):
    """Fast mode: BM25 + semantic fusion, no rerank."""

    def __init__(self) -> None:
        super().__init__(mode="instant", use_rerank=False, candidate_multiplier=6, rerank_top_n=0)


class KaiThinkDBMS(KaiDBMS):
    """High quality mode: larger candidates and reranking enabled."""

    def __init__(self) -> None:
        super().__init__(mode="think", use_rerank=True, candidate_multiplier=10, rerank_top_n=40)
