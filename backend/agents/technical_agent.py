from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from services.llm_service import get_chat_model

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a senior technical support engineer for a modern web and mobile SaaS product.
Give concise, actionable steps. If you need logs or versions, ask for them briefly.
Do not invent product-specific settings; stay generic but professional.
If the issue likely needs engineering, say you'll note it and suggest workaround if any.""",
        ),
        ("human", "{conversation}Current issue:\n{message}"),
    ]
)


def run(message: str, conversation: str = "") -> str:
    llm = get_chat_model(temperature=0.35)
    chain = _PROMPT | llm
    prefix = f"Conversation so far:\n{conversation}\n\n" if conversation.strip() else ""
    out = chain.invoke({"message": message, "conversation": prefix})
    return out.content if hasattr(out, "content") else str(out)
