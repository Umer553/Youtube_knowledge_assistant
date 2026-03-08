"""
Q&A Chain
The core conversational chain for answering questions about video content.
Returns answers with source citations and clickable timestamp links.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.memory import ConversationBufferWindowMemory

from core.retrieval.retriever import format_retrieved_context
from app.config import MEMORY_WINDOW_SIZE


QA_SYSTEM_PROMPT = """You are a helpful YouTube video assistant. You answer questions 
based on the content from YouTube video transcripts provided as context.

RULES:
1. Only answer based on the provided context. If the context doesn't contain 
   enough information, say so clearly.
2. Always cite your sources using the video title and timestamp.
3. Format timestamp citations as clickable links: [Video Title @ MM:SS](timestamp_url)
4. If multiple sources are relevant, cite all of them.
5. Be concise but thorough. Use the exact information from the transcripts.
6. If the question is about something not covered in the videos, let the user know.

CONTEXT FROM VIDEO TRANSCRIPTS:
{context}

CONVERSATION HISTORY:
{chat_history}"""


QA_USER_PROMPT = """{question}"""


def create_qa_chain(llm, retriever):
    """
    Create the main Q&A chain with retrieval and conversation memory.
    
    Pipeline:
    1. User question → MultiQueryRetriever → relevant chunks
    2. Chunks formatted with timestamp/source info
    3. Formatted context + question + history → LLM → answer with citations
    
    Args:
        llm: LangChain LLM instance
        retriever: LangChain retriever (base or MultiQueryRetriever)
        
    Returns:
        Runnable chain
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("human", QA_USER_PROMPT),
    ])

    def retrieve_and_format(inputs):
        question = inputs["question"]
        docs = retriever.invoke(question)
        context = format_retrieved_context(docs)
        return {
            "context": context,
            "question": question,
            "chat_history": inputs.get("chat_history", ""),
            "source_documents": docs,
        }

    chain = (
        RunnableLambda(retrieve_and_format)
        | RunnablePassthrough.assign(
            answer=prompt | llm | StrOutputParser()
        )
    )

    return chain


def create_condense_question_chain(llm):
    """
    Condenses a follow-up question into a standalone question
    using conversation history. This is critical for multi-turn chat.
    
    Example:
        History: "What is the video about?" → "It's about machine learning."
        Follow-up: "What tools does he recommend?"
        Condensed: "What tools does the speaker recommend for machine learning?"
    """
    condense_prompt = ChatPromptTemplate.from_template(
        """Given the conversation history and a follow-up question, 
rephrase the follow-up question to be a standalone question that 
captures all necessary context.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone Question:"""
    )

    return condense_prompt | llm | StrOutputParser()


def run_qa(
    llm,
    retriever,
    question: str,
    chat_history: str = "",
) -> dict:
    """
    Run a single Q&A query and return the answer with sources.
    
    Returns:
        Dict with 'answer' and 'source_documents'
    """
    chain = create_qa_chain(llm, retriever)
    result = chain.invoke({
        "question": question,
        "chat_history": chat_history,
    })
    return {
        "answer": result.get("answer", ""),
        "source_documents": result.get("source_documents", []),
    }
