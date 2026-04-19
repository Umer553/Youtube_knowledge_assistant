"""
Retriever Module
Advanced retrieval strategies for the RAG pipeline:
- Multi-query expansion: generates query variations for better recall
- MMR re-ranking: ensures diverse results across videos
- Metadata-filtered retrieval: scope results to specific videos
"""

from typing import Optional
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.retrieval.vector_store import VectorStoreManager
from app.config import RETRIEVER_K, RETRIEVER_FETCH_K, MMR_LAMBDA, MULTI_QUERY_COUNT


def get_base_retriever(
    vector_store: VectorStoreManager,
    search_type: str = "mmr",
    k: int = RETRIEVER_K,
    video_id: Optional[str] = None,
) -> BaseRetriever:
    search_kwargs = {"k": k}

    if search_type == "mmr":
        search_kwargs["fetch_k"] = RETRIEVER_FETCH_K
        search_kwargs["lambda_mult"] = MMR_LAMBDA

    if video_id:
        search_kwargs["filter"] = {"video_id": video_id}

    return vector_store.store.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )


class MultiQueryRetrieverLCEL(BaseRetriever):
    """
    Custom multi-query retriever built with LCEL.
    Generates N query variations then merges and deduplicates results.
    Avoids the langchain.retrievers dependency entirely.
    """

    base_retriever: BaseRetriever
    llm: object
    num_queries: int = MULTI_QUERY_COUNT

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str, **kwargs) -> list[Document]:
        # Generate query variations
        prompt = ChatPromptTemplate.from_template(
            "Generate {n} different versions of the following question to improve "
            "document retrieval. Output only the questions, one per line, no numbering.\n\n"
            "Original question: {question}"
        )
        chain = prompt | self.llm | StrOutputParser()
        variations_text = chain.invoke({"n": self.num_queries, "question": query})
        queries = [q.strip() for q in variations_text.strip().split("\n") if q.strip()]
        queries = [query] + queries[:self.num_queries]  # always include original

        # Retrieve for each query and deduplicate by page_content
        seen = set()
        all_docs = []
        for q in queries:
            for doc in self.base_retriever.invoke(q):
                key = doc.page_content[:200]
                if key not in seen:
                    seen.add(key)
                    all_docs.append(doc)

        return all_docs


def get_multi_query_retriever(
    vector_store: VectorStoreManager,
    llm,
    search_type: str = "mmr",
    k: int = RETRIEVER_K,
    video_id: Optional[str] = None,
) -> BaseRetriever:
    base_retriever = get_base_retriever(vector_store, search_type, k, video_id)
    return MultiQueryRetrieverLCEL(base_retriever=base_retriever, llm=llm)


def retrieve_for_comparison(
    vector_store: VectorStoreManager,
    query: str,
    video_ids: list[str],
    k_per_video: int = 3,
) -> dict[str, list[Document]]:
    """Retrieve relevant chunks from each video separately for comparison queries."""
    results = {}
    for vid in video_ids:
        docs = vector_store.mmr_search(query=query, k=k_per_video, video_id=vid)
        results[vid] = docs
    return results


def format_retrieved_context(
    documents: list[Document],
    include_timestamps: bool = True,
    include_source: bool = True,
) -> str:
    """Format retrieved documents into a context string for the LLM prompt."""
    if not documents:
        return "No relevant content found."

    context_parts = []
    for i, doc in enumerate(documents, 1):
        meta = doc.metadata
        header_parts = [f"[Source {i}]"]

        if include_source and meta.get('video_title'):
            header_parts.append(f"Video: {meta['video_title']}")

        if include_timestamps and meta.get('start_formatted'):
            header_parts.append(f"Timestamp: {meta['start_formatted']}")

        if meta.get('timestamp_url'):
            header_parts.append(f"Link: {meta['timestamp_url']}")

        header = " | ".join(header_parts)
        context_parts.append(f"{header}\n{doc.page_content}")

    return "\n\n---\n\n".join(context_parts)
