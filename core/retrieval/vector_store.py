"""
Vector Store Module
Manages ChromaDB for storing and querying video transcript embeddings.
Supports metadata filtering by video_id, timestamp range, etc.
"""

from typing import Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.config import CHROMA_DIR, CHROMA_COLLECTION_NAME


class VectorStoreManager:
    """
    Manages the ChromaDB vector store for transcript embeddings.
    Supports adding documents, querying with filters, and cleanup.
    """

    def __init__(self, embedding_model=None, collection_name: str = CHROMA_COLLECTION_NAME):
        """
        Initialize the vector store.
        
        Args:
            embedding_model: LangChain embedding model instance
            collection_name: Name of the ChromaDB collection
        """
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self._store = None

    @property
    def store(self) -> Chroma:
        """Lazy-initialize the Chroma store."""
        if self._store is None:
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=str(CHROMA_DIR),
            )
        return self._store

    def add_documents(self, documents: list[Document]) -> list[str]:
        """
        Add documents to the vector store.
        Each document should have metadata with video_id, timestamps, etc.
        
        Args:
            documents: LangChain Document objects with metadata
            
        Returns:
            List of document IDs assigned by ChromaDB
        """
        if not documents:
            return []

        ids = self.store.add_documents(documents)
        print(f"  Added {len(documents)} documents to vector store")
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        video_id: Optional[str] = None,
        filter_dict: Optional[dict] = None,
    ) -> list[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            video_id: Optional filter to restrict results to a specific video
            filter_dict: Optional ChromaDB metadata filter
            
        Returns:
            List of matching Documents with metadata
        """
        where_filter = filter_dict
        if video_id and not filter_dict:
            where_filter = {"video_id": video_id}

        return self.store.similarity_search(
            query=query,
            k=k,
            filter=where_filter,
        )

    def mmr_search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.7,
        video_id: Optional[str] = None,
        filter_dict: Optional[dict] = None,
    ) -> list[Document]:
        """
        Maximum Marginal Relevance search — balances relevance with diversity.
        Better for multi-video queries where you want varied sources.
        
        Args:
            query: Search query text
            k: Number of results to return
            fetch_k: Number of candidates to consider (should be > k)
            lambda_mult: 0=max diversity, 1=max relevance
            video_id: Optional video filter
            filter_dict: Optional metadata filter
        """
        where_filter = filter_dict
        if video_id and not filter_dict:
            where_filter = {"video_id": video_id}

        return self.store.max_marginal_relevance_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
            filter=where_filter,
        )

    def get_video_ids(self) -> list[str]:
        """Get all unique video IDs currently in the store."""
        try:
            collection = self.store._collection
            results = collection.get(include=["metadatas"])
            video_ids = set()
            for meta in results.get('metadatas', []):
                if meta and 'video_id' in meta:
                    video_ids.add(meta['video_id'])
            return sorted(video_ids)
        except Exception:
            return []

    def get_document_count(self) -> int:
        """Get total number of documents in the store."""
        try:
            return self.store._collection.count()
        except Exception:
            return 0

    def delete_video(self, video_id: str):
        """Remove all documents for a specific video."""
        try:
            collection = self.store._collection
            collection.delete(where={"video_id": video_id})
            print(f"  Deleted documents for video {video_id}")
        except Exception as e:
            print(f"  Error deleting video {video_id}: {e}")

    def clear_all(self):
        """Remove all documents from the store."""
        try:
            collection = self.store._collection
            # Get all IDs and delete
            results = collection.get()
            if results['ids']:
                collection.delete(ids=results['ids'])
            print("  Cleared all documents from vector store")
        except Exception as e:
            print(f"  Error clearing store: {e}")
