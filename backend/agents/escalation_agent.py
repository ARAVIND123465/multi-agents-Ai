from __future__ import annotations

import secrets

from langchain_core.prompts import ChatPromptTemplate

from services.llm_service import get_chat_model

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are routing this conversation to a human specialist.
Acknowledge the user, summarize what you understood in one sentence, and set expectations (response within 1 business day).
Include the ticket id provided in the user message placeholder — do not change its format.""",
        ),
        (
            "human",
            "Ticket: {ticket_id}\nOriginal request:\n{message}\nConversation:\n{conversation}\nTriage note: {reason}",
        ),
    ]
)


def run(message: str, reason: str, conversation: str = "") -> str:
    ticket_id = f"ESC-{secrets.token_hex(3).upper()}"
    llm = get_chat_model(temperature=0.3)
    chain = _PROMPT | llm
    out = chain.invoke(
        {
            "ticket_id": ticket_id,
            "message": message,
            "reason": reason,
            "conversation": conversation.strip() or "(none)",
        }
    )
    text = out.content if hasattr(out, "content") else str(out)
    return text
