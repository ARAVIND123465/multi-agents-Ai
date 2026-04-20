from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.chat import router as chat_router
from services.llm_service import llm_configured, llm_provider
from services.vector_db import ensure_vector_store

_REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_REPO_ROOT / ".env", override=True)
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    key_ok = llm_configured()
    log = logging.getLogger("uvicorn.error")
    env_file = _REPO_ROOT / ".env"
    log.info(
        "Env: root=%s .env_exists=%s llm_provider=%s llm_configured=%s",
        _REPO_ROOT,
        env_file.is_file(),
        llm_provider(),
        key_ok,
    )
    if not key_ok:
        log.warning(
            "No LLM API key after loading .env from %s — set GEMINI_API_KEY (Gemini) or OPENAI_API_KEY (OpenAI), then restart.",
            env_file,
        )
    elif os.getenv("RAG_BUILD_AT_STARTUP", "").strip().lower() in ("1", "true", "yes"):
        try:
            ensure_vector_store()
        except Exception as e:
            log.warning(
                "RAG index was not built at startup (chat still works; RAG builds on first use or after quota/billing is fixed): %s",
                e,
            )
    yield


app = FastAPI(title="Multi-Agent Customer Support API", lifespan=lifespan)

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api", tags=["chat"])


@app.get("/health")
def health():
    return {"status": "ok"}
