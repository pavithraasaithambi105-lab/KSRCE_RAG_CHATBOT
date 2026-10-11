import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+(?:[-&][a-z0-9]+)*")


def tokenize(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


class VectorStore:
    """On-disk index: vectors.npy holds the embeddings, chunks.json the chunk text and metadata.

    Search is hybrid: embedding similarity (meaning) + BM25 (exact words such as "HOD-CSE"),
    merged with reciprocal rank fusion so a chunk found by either method can be returned.
    """

    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.vectors_path = index_dir / "vectors.npy"
        self.chunks_path = index_dir / "chunks.json"
        self.vectors = np.zeros((0, 0), dtype=np.float32)
        self.chunks: List[dict] = []
        if self.vectors_path.exists() and self.chunks_path.exists():
            self.vectors = np.load(self.vectors_path)
            self.chunks = json.loads(self.chunks_path.read_text(encoding="utf-8"))
        self._build_keyword_index()

    def _save(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.vectors_path, self.vectors)
        self.chunks_path.write_text(
            json.dumps(self.chunks, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        self._build_keyword_index()

    def replace_source(self, source: str, chunks: List[dict], vectors: np.ndarray):
        """Drop any old chunks from `source`, then add the new ones."""
        keep = [i for i, c in enumerate(self.chunks) if c["source"] != source]
        old_vectors = self.vectors[keep] if keep else np.zeros((0, vectors.shape[1]), np.float32)
        self.chunks = [self.chunks[i] for i in keep] + chunks
        self.vectors = np.vstack([old_vectors, vectors]).astype(np.float32)
        self._save()

    def remove_source(self, source: str) -> int:
        keep = [i for i, c in enumerate(self.chunks) if c["source"] != source]
        removed = len(self.chunks) - len(keep)
        self.chunks = [self.chunks[i] for i in keep]
        self.vectors = self.vectors[keep] if keep else np.zeros((0, 0), np.float32)
        self._save()
        return removed

    def search(self, query: str, query_vector: np.ndarray, k: int, candidates: int = 30) -> List[Tuple[dict, float]]:
        """Top-k chunks by fused rank; the score returned is the embedding cosine similarity."""
        if not self.chunks:
            return []
        # Cosine similarity (vectors are unit length). einsum instead of `@` avoids spurious
        # "divide by zero" warnings from numpy 2.0's macOS Accelerate BLAS.
        cosine = np.einsum("ij,j->i", self.vectors, query_vector)
        semantic = np.argsort(-cosine)[:candidates]
        keyword = self._bm25_top(query, candidates)

        fused: Dict[int, float] = {}
        for ranking in (semantic, keyword):
            for rank, i in enumerate(ranking):
                fused[int(i)] = fused.get(int(i), 0.0) + 1.0 / (60 + rank)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        return [(self.chunks[i], float(cosine[i])) for i in top]

    def sources(self) -> dict:
        counts: dict = {}
        for c in self.chunks:
            counts[c["source"]] = counts.get(c["source"], 0) + 1
        return counts

    # ---- BM25 keyword search ----

    def _build_keyword_index(self):
        self._doc_terms = [Counter(tokenize(c["text"])) for c in self.chunks]
        self._doc_len = np.array([sum(t.values()) for t in self._doc_terms], dtype=np.float32)
        df: Counter = Counter()
        for terms in self._doc_terms:
            df.update(terms.keys())
        n = len(self.chunks)
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def _bm25_top(self, query: str, k: int, k1: float = 1.5, b: float = 0.75) -> List[int]:
        terms = [t for t in set(tokenize(query)) if t in self._idf]
        if not terms:
            return []
        avg_len = float(self._doc_len.mean()) or 1.0
        scores = np.zeros(len(self.chunks), dtype=np.float32)
        for i, doc in enumerate(self._doc_terms):
            norm = k1 * (1 - b + b * self._doc_len[i] / avg_len)
            for t in terms:
                f = doc.get(t)
                if f:
                    scores[i] += self._idf[t] * f * (k1 + 1) / (f + norm)
        top = np.argsort(-scores)[:k]
        return [int(i) for i in top if scores[i] > 0]
