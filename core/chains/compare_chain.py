"""
Compare Chain
Handles cross-video comparison queries by retrieving from each video
separately and synthesizing a comparative response.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.retrieval.vector_store import VectorStoreManager
from core.retrieval.retriever import retrieve_for_comparison, format_retrieved_context


COMPARE_PROMPT = """You are an expert at analyzing and comparing information from 
multiple YouTube videos. Compare the content from the following videos based on the 
user's question.

{video_contexts}

USER'S QUESTION: {question}

INSTRUCTIONS:
1. Compare and contrast the perspectives, information, or approaches from each video
2. Highlight key agreements and disagreements between the videos
3. Create a clear comparison structure (use a table format if appropriate)
4. Cite specific timestamps from each video: [Video Title @ MM:SS](url)
5. Provide your synthesis/conclusion at the end

Comparison:"""


def run_comparison(
    llm,
    vector_store: VectorStoreManager,
    question: str,
    video_ids: list[str],
    video_titles: dict[str, str] = None,
    k_per_video: int = 4,
) -> str:
    """
    Run a cross-video comparison query.
    
    Retrieves relevant chunks from each video separately,
    then asks the LLM to compare and synthesize.
    
    Args:
        llm: LangChain LLM
        vector_store: VectorStoreManager instance
        question: User's comparison question
        video_ids: List of video IDs to compare
        video_titles: Optional dict mapping video_id -> title
        k_per_video: Chunks to retrieve per video
        
    Returns:
        Comparison response string
    """
    if video_titles is None:
        video_titles = {}

    # Retrieve chunks from each video separately
    per_video_docs = retrieve_for_comparison(
        vector_store=vector_store,
        query=question,
        video_ids=video_ids,
        k_per_video=k_per_video,
    )

    # Format each video's context separately
    video_contexts_parts = []
    for vid in video_ids:
        docs = per_video_docs.get(vid, [])
        title = video_titles.get(vid, vid)
        if docs:
            context = format_retrieved_context(docs)
            video_contexts_parts.append(
                f"=== VIDEO: {title} ===\n{context}"
            )
        else:
            video_contexts_parts.append(
                f"=== VIDEO: {title} ===\nNo relevant content found for this query."
            )

    video_contexts = "\n\n".join(video_contexts_parts)

    # Run the comparison chain
    prompt = ChatPromptTemplate.from_template(COMPARE_PROMPT)
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "video_contexts": video_contexts,
        "question": question,
    })
