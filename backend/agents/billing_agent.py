from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from services.llm_service import get_chat_model

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You handle billing and subscription support.
Explain refund/charge policies clearly. If you cannot confirm account-specific details, ask for email on file and last 4 of card or invoice id.
Stay compliant: no legal promises; suggest contacting bank for charge disputes when appropriate.
Keep replies short and structured (bullets ok).""",
        ),
        ("human", "{conversation}Request:\n{message}"),
    ]
)


def run(message: str, conversation: str = "") -> str:
    llm = get_chat_model(temperature=0.25)
    chain = _PROMPT | llm
    prefix = f"Conversation so far:\n{conversation}\n\n" if conversation.strip() else ""
    out = chain.invoke({"message": message, "conversation": prefix})
    return out.content if hasattr(out, "content") else str(out)
