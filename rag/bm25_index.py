"""BM25 keyword index for hybrid retrieval."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from rank_bm25 import BM25Okapi

from rag.hybrid_fusion import build_chunk_id
from rag.text_splitter import TextChunk

BM25_INDEX_FILENAME = "bm25_index.json"
INDEX_VERSION = 1

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_EN_NUM_RE = re.compile(r"[a-z]+|\d+", re.IGNORECASE)


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: str
    content: str
    source: str
    chunk_index: int


def tokenize(text: str) -> List[str]:
    """Tokenize for BM25: English words, digits, CJK single characters."""
    if not text:
        return []

    lowered = text.lower()
    tokens: List[str] = []
    seen_spans: set[tuple[int, int]] = set()

    for match in _EN_NUM_RE.finditer(lowered):
        span = match.span()
        seen_spans.add(span)
        tokens.append(match.group().lower())

    for match in _CJK_RE.finditer(text):
        span = match.span()
        if span in seen_spans:
            continue
        tokens.append(match.group())

    return tokens


class BM25Index:
    def __init__(self) -> None:
        self._chunks: List[IndexedChunk] = []
        self._chunk_map: dict[str, IndexedChunk] = {}
        self._bm25: Optional[BM25Okapi] = None

    def __len__(self) -> int:
        return len(self._chunks)

    def add_chunks(self, chunks: List[TextChunk]) -> int:
        if not chunks:
            return 0

        added = 0
        for chunk in chunks:
            if not chunk.content or not chunk.content.strip():
                continue
            chunk_id = build_chunk_id(chunk.source, chunk.chunk_index)
            if chunk_id in self._chunk_map:
                continue
            indexed = IndexedChunk(
                chunk_id=chunk_id,
                content=chunk.content,
                source=chunk.source,
                chunk_index=chunk.chunk_index,
            )
            self._chunks.append(indexed)
            self._chunk_map[chunk_id] = indexed
            added += 1

        if added:
            self._rebuild()
        return added

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        if top_k <= 0 or not query.strip() or not self._bm25 or not self._chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        if ranked and float(ranked[0][1]) <= 0:
            return self._overlap_search(query_tokens, top_k)

        results: List[Tuple[str, float]] = []
        for idx, score in ranked:
            value = float(score)
            if value <= 0:
                break
            if len(results) >= top_k:
                break
            results.append((self._chunks[idx].chunk_id, value))
        return results

    def _overlap_search(
        self,
        query_tokens: List[str],
        top_k: int,
    ) -> List[Tuple[str, float]]:
        """Fallback when BM25 scores are all zero (common with tiny corpora)."""
        if not query_tokens:
            return []

        query_set = set(query_tokens)
        scored: List[Tuple[int, float]] = []
        for idx, chunk in enumerate(self._chunks):
            doc_tokens = set(tokenize(chunk.content))
            overlap = sum(1 for token in query_set if token in doc_tokens)
            if overlap > 0:
                scored.append((idx, float(overlap)))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            (self._chunks[idx].chunk_id, score)
            for idx, score in scored[:top_k]
        ]

    def get_chunk(self, chunk_id: str) -> Optional[IndexedChunk]:
        return self._chunk_map.get(chunk_id)

    def save(self, persist_dir: str) -> None:
        path = Path(persist_dir) / BM25_INDEX_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": INDEX_VERSION,
            "chunks": [asdict(chunk) for chunk in self._chunks],
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, persist_dir: str) -> "BM25Index":
        path = Path(persist_dir) / BM25_INDEX_FILENAME
        index = cls()
        if not path.is_file():
            return index

        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("chunks", []):
            indexed = IndexedChunk(
                chunk_id=item["chunk_id"],
                content=item["content"],
                source=item["source"],
                chunk_index=int(item["chunk_index"]),
            )
            index._chunks.append(indexed)
            index._chunk_map[indexed.chunk_id] = indexed

        index._rebuild()
        return index

    def _rebuild(self) -> None:
        if not self._chunks:
            self._bm25 = None
            return
        tokenized_corpus = [tokenize(chunk.content) for chunk in self._chunks]
        self._bm25 = BM25Okapi(tokenized_corpus)
