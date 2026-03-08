"""
Output Formatter
Transforms LLM responses into structured output formats:
- Flashcards (Q&A pairs for spaced repetition)
- Quiz (MCQs with answer key)
- Comparison table
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.retrieval.retriever import format_retrieved_context


FLASHCARD_PROMPT = """Based on the following YouTube video content, create {num_cards} 
flashcards for study/revision purposes.

VIDEO CONTENT:
{context}

Create flashcards in this exact JSON format:
[
  {{"front": "Question or term", "back": "Answer or definition", "timestamp": "MM:SS"}},
  ...
]

Rules:
- Each flashcard should test a specific concept from the video
- Questions should be clear and specific
- Answers should be concise but complete
- Include the approximate timestamp where this topic is discussed

Return ONLY the JSON array, no other text."""


QUIZ_PROMPT = """Based on the following YouTube video content, create a {num_questions}-question 
multiple choice quiz.

VIDEO CONTENT:
{context}

Create the quiz in this exact JSON format:
[
  {{
    "question": "Question text?",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct": "A",
    "explanation": "Brief explanation of why this is correct",
    "timestamp": "MM:SS"
  }},
  ...
]

Rules:
- Questions should test understanding, not just recall
- All options should be plausible
- Include exactly 4 options per question
- The explanation should reference the video content
- Include the timestamp where the answer can be found

Return ONLY the JSON array, no other text."""


def generate_flashcards(
    llm,
    retriever,
    topic: str = "",
    num_cards: int = 10,
) -> list[dict]:
    """
    Generate flashcards from video content.
    
    Returns:
        List of dicts: [{front, back, timestamp}]
    """
    query = f"Key concepts and topics about {topic}" if topic else "Main topics and concepts"
    docs = retriever.invoke(query)
    context = format_retrieved_context(docs)

    prompt = ChatPromptTemplate.from_template(FLASHCARD_PROMPT)
    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "context": context,
        "num_cards": num_cards,
    })

    return _parse_json_response(result)


def generate_quiz(
    llm,
    retriever,
    topic: str = "",
    num_questions: int = 5,
) -> list[dict]:
    """
    Generate a multiple-choice quiz from video content.
    
    Returns:
        List of dicts: [{question, options, correct, explanation, timestamp}]
    """
    query = f"Important information about {topic}" if topic else "Important concepts and details"
    docs = retriever.invoke(query)
    context = format_retrieved_context(docs)

    prompt = ChatPromptTemplate.from_template(QUIZ_PROMPT)
    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "context": context,
        "num_questions": num_questions,
    })

    return _parse_json_response(result)


def format_flashcards_markdown(flashcards: list[dict]) -> str:
    """Format flashcards as readable markdown."""
    if not flashcards:
        return "Could not generate flashcards."

    lines = ["## 📝 Flashcards\n"]
    for i, card in enumerate(flashcards, 1):
        lines.append(f"**Card {i}**")
        lines.append(f"**Q:** {card.get('front', '')}")
        lines.append(f"**A:** {card.get('back', '')}")
        ts = card.get('timestamp', '')
        if ts:
            lines.append(f"*📍 Discussed at {ts}*")
        lines.append("")  # blank line

    return "\n".join(lines)


def format_quiz_markdown(quiz: list[dict]) -> str:
    """Format quiz as readable markdown with hidden answers."""
    if not quiz:
        return "Could not generate quiz."

    lines = ["## 🧪 Quiz\n"]

    # Questions section
    for i, q in enumerate(quiz, 1):
        lines.append(f"**Question {i}:** {q.get('question', '')}")
        for opt in q.get('options', []):
            lines.append(f"  {opt}")
        lines.append("")

    # Answer key section
    lines.append("---")
    lines.append("### Answer Key\n")
    for i, q in enumerate(quiz, 1):
        correct = q.get('correct', '?')
        explanation = q.get('explanation', '')
        ts = q.get('timestamp', '')
        lines.append(f"**Q{i}:** {correct} — {explanation}")
        if ts:
            lines.append(f"  *📍 See video at {ts}*")

    return "\n".join(lines)


def _parse_json_response(text: str) -> list[dict]:
    """Parse JSON from LLM response, handling markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        result = json.loads(cleaned)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return []
