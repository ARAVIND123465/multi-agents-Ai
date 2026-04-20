import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env", override=True)
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)


def _gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def llm_provider() -> str:
    """Active provider: gemini or openai."""
    explicit = os.getenv("LLM_PROVIDER", "").strip().lower()
    if explicit in ("gemini", "google"):
        return "gemini"
    if explicit == "openai":
        return "openai"
    if _gemini_key():
        return "gemini"
    return "openai"


def llm_configured() -> bool:
    if llm_provider() == "gemini":
        return bool(_gemini_key())
    return bool(_openai_key())


def get_chat_model(temperature: float = 0.3) -> BaseChatModel:
    if llm_provider() == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=_gemini_key(),
        )

    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=temperature)


def get_embeddings() -> Embeddings:
    if llm_provider() == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
        return GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=_gemini_key(),
        )

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
