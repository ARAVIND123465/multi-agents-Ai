from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from services.llm_service import get_chat_model
from services.vector_db import get_retriever

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Answer using ONLY the context below. If the context is insufficient, say what is missing and suggest contacting support.
Cite section ideas in plain language, not file paths. Be concise.""",
        ),
        ("human", "Context:\n{context}\n\nConversation:\n{conversation}\n\nQuestion:\n{question}"),
    ]
)


def run(message: str, conversation: str = "") -> tuple[str, list[str]]:
    try:
        retriever = get_retriever()
        docs = retriever.invoke(message)
    except Exception as e:
        err = str(e)
        if "insufficient_quota" in err or "429" in err or "Resource exhausted" in err or "RESOURCE_EXHAUSTED" in err:
            return (
                "Knowledge search is unavailable: the embeddings API hit a quota or rate limit (Gemini or OpenAI). "
                "Other agents may still work. Check your provider billing/limits, then try again.",
                [],
            )
        return (
            f"Knowledge search failed ({err}). Try a technical or billing question, or retry later.",
            [],
        )
    context = "\n\n".join(d.page_content for d in docs)
    sources: list[str] = []
    for d in docs:
        src = d.metadata.get("source")
        if src and src not in sources:
            sources.append(str(src))

    llm = get_chat_model(temperature=0.2)
    chain = _PROMPT | llm
    conv = conversation.strip() or "(none)"
    out = chain.invoke({"context": context, "question": message, "conversation": conv})
    text = out.content if hasattr(out, "content") else str(out)
    return text, sources
