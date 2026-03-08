"""
Summary Chain
Generates summaries of video content in various styles and lengths.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from core.retrieval.retriever import format_retrieved_context


SUMMARY_PROMPT = """You are a video summarization expert. Summarize the following 
YouTube video content based on the transcript excerpts provided.

VIDEO CONTENT:
{context}

INSTRUCTIONS:
- Create a clear, well-structured summary of the video's main points
- Include the most important topics, arguments, and conclusions
- Reference specific timestamps where key points are discussed: [Topic @ MM:SS](url)
- Keep the summary informative and concise
- Structure with clear sections if the content covers multiple topics

Provide the summary now:"""


BRIEF_SUMMARY_PROMPT = """Summarize this YouTube video content in 3-5 bullet points.
Each bullet should capture a key takeaway with its timestamp.

VIDEO CONTENT:
{context}

Format each bullet as:
• **Key Point** — Brief explanation [@ MM:SS](timestamp_url)"""


STUDY_NOTES_PROMPT = """Create detailed study notes from this YouTube video content.
Organize the material as a student would for exam preparation.

VIDEO CONTENT:
{context}

Format the notes with:
- Clear topic headings
- Key definitions and concepts
- Important examples mentioned
- Timestamp references for each section: [Topic @ MM:SS](url)

Study Notes:"""


def create_summary_chain(llm, retriever, style: str = "detailed"):
    """
    Create a summarization chain.
    
    Args:
        llm: LangChain LLM
        retriever: Retriever to get video content
        style: 'detailed', 'brief', or 'study_notes'
    """
    prompts = {
        "detailed": SUMMARY_PROMPT,
        "brief": BRIEF_SUMMARY_PROMPT,
        "study_notes": STUDY_NOTES_PROMPT,
    }

    template = prompts.get(style, SUMMARY_PROMPT)
    prompt = ChatPromptTemplate.from_template(template)

    def retrieve_and_format(inputs):
        question = inputs.get("question", "Summarize this video")
        # For summaries, we want more chunks to cover the full video
        docs = retriever.invoke(question)
        context = format_retrieved_context(docs)
        return {"context": context}

    chain = RunnableLambda(retrieve_and_format) | prompt | llm | StrOutputParser()
    return chain


def run_summary(
    llm,
    retriever,
    style: str = "detailed",
    video_title: str = "",
) -> str:
    """Run a summarization and return the result."""
    chain = create_summary_chain(llm, retriever, style)
    query = f"Summarize the video: {video_title}" if video_title else "Summarize this video completely"
    return chain.invoke({"question": query})
