from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from graph.workflow import run_support_turn
from services.chat_store import new_session_id
from services.llm_service import llm_configured, llm_provider

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    agent: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    escalated: bool = False
    sources: list[str] = []


def _quota_or_rate_limited(message: str) -> bool:
    m = message.lower()
    return any(
        s in m
        for s in (
            "insufficient_quota",
            "resource_exhausted",
            "resource exhausted",
            "quota",
            "rate limit",
            "429",
            "too many requests",
        )
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if not llm_configured():
        raise HTTPException(
            status_code=503,
            detail="No LLM API key configured. Add GEMINI_API_KEY (or GOOGLE_API_KEY) for Gemini, or OPENAI_API_KEY for OpenAI, in project root .env — then restart uvicorn.",
        )
    sid = req.session_id or new_session_id()
    try:
        state = run_support_turn(req.message.strip(), sid)
    except Exception as e:
        try:
            from openai import APIError, RateLimitError

            if isinstance(e, RateLimitError):
                raise HTTPException(
                    status_code=503,
                    detail="OpenAI rate limit or quota exceeded. Check https://platform.openai.com/account/billing",
                ) from e
            if isinstance(e, APIError):
                err_body = str(e)
                if getattr(e, "code", None) == "insufficient_quota" or "insufficient_quota" in err_body:
                    raise HTTPException(
                        status_code=503,
                        detail="OpenAI quota or billing issue. See https://platform.openai.com/account/billing",
                    ) from e
                raise HTTPException(status_code=502, detail=err_body) from e
        except ImportError:
            pass

        msg = str(e)
        if _quota_or_rate_limited(msg):
            prov = llm_provider()
            if prov == "gemini":
                hint = "Check Google AI Studio / Cloud billing and limits: https://ai.google.dev/gemini-api/docs"
            else:
                hint = "Check https://platform.openai.com/account/billing"
            raise HTTPException(
                status_code=503,
                detail=f"LLM provider quota or rate limit ({prov}). {hint}",
            ) from e
        raise HTTPException(status_code=500, detail=msg) from e
    return ChatResponse(
        answer=state.get("answer") or "",
        session_id=sid,
        agent=state.get("agent"),
        intent=state.get("intent"),
        confidence=state.get("confidence"),
        escalated=bool(state.get("escalated")),
        sources=list(state.get("sources") or []),
    )


@router.get("/config")
async def config_status():
    """LLM readiness (no secrets)."""
    prov = llm_provider()
    ok = llm_configured()
    return {
        "llm_configured": ok,
        "llm_provider": prov,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "gemini_configured": bool(
            (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        ),
    }


@router.post("/session")
async def create_session():
    return {"session_id": new_session_id()}


@router.get("/sessions")
async def list_sessions():
    from services.chat_store import recent_sessions
    return {"sessions": recent_sessions(20)}


@router.get("/session/{session_id}")
async def fetch_history(session_id: str):
    from services.chat_store import get_session_history
    return {"messages": get_session_history(session_id)}
