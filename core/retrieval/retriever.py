"""
Retriever Module
Advanced retrieval strategies for the RAG pipeline:
- MultiQueryRetriever: generates query variations for better recall
- MMR re-ranking: ensures diverse results across videos
- Metadata-filtered retrieval: scope results to specific videos
"""

from typing import Optional
from langchain_core.documents import Document
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.retrievers import BaseRetriever

from core.retrieval.vector_store import VectorStoreManager
from app.config import RETRIEVER_K, RETRIEVER_FETCH_K, MMR_LAMBDA, MULTI_QUERY_COUNT


def get_base_retriever(
    vector_store: VectorStoreManager,
    search_type: str = "mmr",
    k: int = RETRIEVER_K,
    video_id: Optional[str] = None,
) -> BaseRetriever:
    """
    Get a base retriever from the vector store.
    
    Args:
        vector_store: VectorStoreManager instance
        search_type: 'similarity' or 'mmr'
        k: Number of results
        video_id: Optional filter for a specific video
    """
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


def get_multi_query_retriever(
    vector_store: VectorStoreManager,
    llm,
    search_type: str = "mmr",
    k: int = RETRIEVER_K,
    video_id: Optional[str] = None,
) -> MultiQueryRetriever:
    """
    Create a MultiQueryRetriever that generates multiple query variations
    for better recall. This is especially useful for vague questions —
    the LLM rephrases the query 3 different ways and retrieves for each.
    
    Args:
        vector_store: VectorStoreManager instance
        llm: LangChain LLM for query generation
        search_type: 'similarity' or 'mmr'
        k: Number of results per query variation
        video_id: Optional video filter
    """
    base_retriever = get_base_retriever(vector_store, search_type, k, video_id)

    return MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
    )


def retrieve_for_comparison(
    vector_store: VectorStoreManager,
    query: str,
    video_ids: list[str],
    k_per_video: int = 3,
) -> dict[str, list[Document]]:
    """
    Retrieve relevant chunks from each video separately.
    Used for cross-video comparison queries.
    
    Returns:
        Dict mapping video_id -> list of relevant Documents
    """
    results = {}
    for vid in video_ids:
        docs = vector_store.mmr_search(
            query=query,
            k=k_per_video,
            video_id=vid,
        )
        results[vid] = docs
    return results


def format_retrieved_context(
    documents: list[Document],
    include_timestamps: bool = True,
    include_source: bool = True,
) -> str:
    """
    Format retrieved documents into a context string for the LLM prompt.
    
    Each chunk is formatted with its source info so the LLM can cite it.
    """
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
