from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.llm_service import get_embeddings, llm_configured

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "data" / "docs"
EMBED_DIR = ROOT / "data" / "embeddings"
INDEX_NAME = "faiss_index"

_vectorstore: Optional[FAISS] = None


def _load_markdown_files() -> list[Document]:
    documents: list[Document] = []
    if not DOCS_DIR.exists():
        return documents
    for path in sorted(DOCS_DIR.glob("**/*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        documents.append(Document(page_content=text, metadata={"source": str(path.relative_to(DOCS_DIR))}))
    return documents


def ensure_vector_store() -> FAISS:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if not llm_configured():
        raise RuntimeError(
            "Configure GEMINI_API_KEY / GOOGLE_API_KEY (Gemini) or OPENAI_API_KEY (OpenAI) to build or load the vector store."
        )

    EMBED_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    index_path = EMBED_DIR / INDEX_NAME

    if (index_path / "index.faiss").exists():
        _vectorstore = FAISS.load_local(
            str(EMBED_DIR),
            embeddings,
            index_name=INDEX_NAME,
            allow_dangerous_deserialization=True,
        )
        return _vectorstore

    docs = _load_markdown_files()
    if not docs:
        _vectorstore = FAISS.from_texts(["No knowledge base documents loaded yet."], embeddings)
        _vectorstore.save_local(str(EMBED_DIR), index_name=INDEX_NAME)
        return _vectorstore

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    splits = splitter.split_documents(docs)
    _vectorstore = FAISS.from_documents(splits, embeddings)
    _vectorstore.save_local(str(EMBED_DIR), index_name=INDEX_NAME)
    return _vectorstore


def get_retriever(k: Optional[int] = None):
    vs = ensure_vector_store()
    k = k or int(os.getenv("RAG_TOP_K", "4"))
    return vs.as_retriever(search_kwargs={"k": k})
