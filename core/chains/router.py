"""
Query Router
Classifies user queries into intent types and routes them
to the appropriate processing chain.

Intent types:
- factual_qa: Direct questions about video content
- summarize: Summarization requests
- compare_videos: Cross-video comparison
- sentiment_query: Questions about viewer opinions/comments
- generate_quiz: Quiz/flashcard generation requests
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


ROUTER_PROMPT = """You are a query intent classifier for a YouTube video chatbot.
Classify the user's question into exactly ONE of these categories:

- factual_qa: Direct question about the content discussed in the video(s)
- summarize: Request to summarize a video or part of it
- compare_videos: Request to compare, contrast, or synthesize information across multiple videos
- sentiment_query: Question about what viewers/commenters think, audience reactions, or opinions
- generate_quiz: Request to create quiz questions, flashcards, or study material
- generate_flashcards: Request specifically for flashcard-format Q&A pairs

User's question: {question}

Context: The user currently has {num_videos} video(s) loaded.
Video titles: {video_titles}

Respond with ONLY the category name, nothing else."""


def create_router_chain(llm):
    """
    Create a chain that classifies query intent.
    
    Args:
        llm: LangChain LLM instance
        
    Returns:
        A runnable chain that takes a dict and returns an intent string
    """
    prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
    chain = prompt | llm | StrOutputParser()
    return chain


def classify_intent(
    llm,
    question: str,
    num_videos: int = 1,
    video_titles: str = "",
) -> str:
    """
    Classify the intent of a user's question.
    
    Args:
        llm: LangChain LLM
        question: User's question
        num_videos: Number of videos currently loaded
        video_titles: Comma-separated list of video titles
        
    Returns:
        Intent string (one of the defined types)
    """
    chain = create_router_chain(llm)

    result = chain.invoke({
        "question": question,
        "num_videos": num_videos,
        "video_titles": video_titles or "Not specified",
    })

    # Normalize the response
    intent = result.strip().lower().replace(" ", "_")

    # Validate against known intents
    valid_intents = [
        "factual_qa", "summarize", "compare_videos",
        "sentiment_query", "generate_quiz", "generate_flashcards",
    ]

    if intent not in valid_intents:
        # Default to factual_qa for unrecognized intents
        intent = "factual_qa"

    return intent
