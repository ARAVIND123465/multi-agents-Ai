from __future__ import annotations

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from services.llm_service import get_chat_model


class TriageResult(BaseModel):
    intent: Literal["technical", "billing", "rag", "general"] = Field(
        description="technical=bugs/features; billing=payments/refunds/subscriptions; rag=pricing/policy/docs; general=small talk or unclear"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="How sure you are about intent")
    reason: str = Field(description="One short phrase for logging")


_TR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You classify customer support messages for a B2C SaaS product.
- technical: crashes, errors, login issues, performance, integrations, API, bugs, "app not loading"
- billing: invoices, refunds, charges, subscription, plan changes, payment failures
- rag: product facts, pricing tiers, limits, SLA, policies, "what is your pricing"
- general: greetings, thanks, vague text, or multi-topic that needs doc lookup

Pick exactly one intent. Be generous with 'rag' for factual company/product questions.""",
        ),
        (
            "human",
            "{message}",
        ),
    ]
)


def triage(message: str, conversation: str = "") -> TriageResult:
    llm = get_chat_model(temperature=0.0)
    chain = _TR_PROMPT | llm.with_structured_output(TriageResult)
    if conversation.strip():
        wrapped = f"Prior conversation:\n{conversation.strip()}\n\nLatest message:\n{message.strip()}"
    else:
        wrapped = message.strip()
    return chain.invoke({"message": wrapped})
