"""
Embedding Pipeline
Generates vector embeddings for text chunks using OpenAI or HuggingFace models.
Wraps LangChain embedding classes with fallback support.
"""

from typing import Optional
from langchain.schema import Document


def get_embedding_model(
    provider: str = "openai",
    api_key: str = "",
    model_name: str = ""
):
    """
    Get an embedding model instance.
    
    Args:
        provider: 'openai' or 'huggingface'
        api_key: API key (required for OpenAI)
        model_name: Override default model name
        
    Returns:
        LangChain Embeddings instance
    """
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=model_name or "text-embedding-3-small",
            openai_api_key=api_key,
        )

    elif provider == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=model_name or "all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )

    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


def embed_documents(
    documents: list[Document],
    embedding_model=None,
    provider: str = "openai",
    api_key: str = "",
) -> tuple[list[list[float]], list[Document]]:
    """
    Generate embeddings for a list of LangChain Documents.
    
    Returns:
        Tuple of (embeddings_list, documents) - same order
    """
    if embedding_model is None:
        embedding_model = get_embedding_model(provider, api_key)

    texts = [doc.page_content for doc in documents]
    embeddings = embedding_model.embed_documents(texts)

    return embeddings, documents
