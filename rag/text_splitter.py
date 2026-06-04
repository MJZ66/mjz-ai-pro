"""文本分块。"""
from dataclasses import dataclass
from typing import List


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    source: str = ""


def split_text(
    text: str,
    *,
    source: str = "",
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> List[TextChunk]:
    if not text or not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 5)

    chunks: List[TextChunk] = []
    start = 0
    index = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        piece = text[start:end].strip()
        if piece:
            chunks.append(
                TextChunk(content=piece, chunk_index=index, source=source)
            )
            index += 1
        if end >= length:
            break
        start = end - chunk_overlap
        if start < 0:
            start = 0

    return chunks
