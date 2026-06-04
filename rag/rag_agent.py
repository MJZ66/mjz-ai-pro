"""RAG 完整流程。"""
from typing import List, Optional, Tuple

from core.llm_client import LLMClient
from rag.document_loader import DocumentLoadError, load_from_upload
from rag.retriever import RetrievedChunk, Retriever
from rag.text_splitter import split_text
from rag.vector_store import VectorStore
from utils.logger import get_logger, user_friendly_error

logger = get_logger(__name__)

RAG_SYSTEM_PROMPT = """你是 MJZ AI Pro 的知识库问答助手。
请仅根据提供的参考资料回答问题；若资料不足，请明确说明无法从知识库中找到答案。
回答末尾列出引用来源，格式：
【引用】
1. 文件名 - 片段序号
"""


class RAGAgent:
    def __init__(self, llm_client: LLMClient, vector_store: VectorStore, top_k: int = 4):
        self.llm = llm_client
        self.vector_store = vector_store
        self.retriever = Retriever(vector_store, top_k=top_k)

    def ingest_upload(self, uploaded_file) -> Tuple[int, str]:
        """上传 → 解析 → 分块 → 向量化 → 入库。"""
        try:
            text, filename = load_from_upload(uploaded_file)
            if not text.strip():
                return 0, "文件内容为空，未入库。"

            chunks = split_text(text, source=filename)
            if not chunks:
                return 0, "未能生成有效文本分块。"

            embeddings = self.llm.embed_texts([c.content for c in chunks])
            count = self.vector_store.add_chunks(chunks, embeddings)
            return count, f"已成功入库 {count} 个片段（来源：{filename}）。"
        except DocumentLoadError as exc:
            return 0, str(exc)
        except Exception as exc:
            logger.exception("RAG 入库失败")
            return 0, user_friendly_error(exc)

    def build_context(self, retrieved: List[RetrievedChunk]) -> str:
        if not retrieved:
            return "（无匹配参考资料）"
        lines = []
        for i, item in enumerate(retrieved, start=1):
            lines.append(
                f"[{i}] 来源={item.source} 片段#{item.chunk_index}\n{item.content}"
            )
        return "\n\n".join(lines)

    def format_citations(self, retrieved: List[RetrievedChunk]) -> str:
        if not retrieved:
            return ""
        lines = ["【引用】"]
        for i, item in enumerate(retrieved, start=1):
            lines.append(f"{i}. {item.source} - 片段 {item.chunk_index}")
        return "\n".join(lines)

    def answer(
        self,
        question: str,
        *,
        temperature: float = 0.3,
        stream_callback=None,
    ) -> Tuple[str, List[RetrievedChunk]]:
        if self.vector_store.count() == 0:
            raise RuntimeError("知识库为空，请先上传文档。")

        query_embedding = self.llm.embed_texts([question])[0]
        retrieved = self.retriever.retrieve(question, query_embedding)
        context = self.build_context(retrieved)

        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"参考资料：\n{context}\n\n"
                    f"用户问题：{question}\n\n"
                    "请基于参考资料回答，并附上引用来源。"
                ),
            },
        ]

        if stream_callback:
            answer_text = self.llm.stream_chat_collect(
                messages,
                temperature=temperature,
                on_delta=stream_callback,
            )
        else:
            answer_text = self.llm.chat(messages, temperature=temperature)

        citations = self.format_citations(retrieved)
        if citations and citations not in answer_text:
            answer_text = f"{answer_text}\n\n{citations}"

        return answer_text, retrieved
