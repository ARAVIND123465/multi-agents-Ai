from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pymongo import MongoClient
from pymongo.collection import Collection

_client: Optional[MongoClient] = None
_db_name = os.getenv("MONGODB_DB", "multi_agent_support")


def _collection() -> Optional[Collection]:
    global _client
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client[_db_name]["messages"]


def append_message(
    session_id: str, role: str, content: str, meta: Optional[dict[str, Any]] = None
) -> None:
    coll = _collection()
    if coll is None:
        return
    doc = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "meta": meta or {},
        "ts": datetime.now(timezone.utc),
    }
    coll.insert_one(doc)


def recent_messages(session_id: str, limit: int = 12) -> list[dict[str, str]]:
    coll = _collection()
    if coll is None:
        return []
    cur = (
        coll.find({"session_id": session_id}, {"_id": 0, "role": 1, "content": 1})
        .sort("ts", -1)
        .limit(limit)
    )
    rows = list(cur)
    rows.reverse()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def new_session_id() -> str:
    return str(uuid.uuid4())


def recent_sessions(limit: int = 20) -> list[dict[str, Any]]:
    coll = _collection()
    if coll is None:
        return []
        
    pipeline = [
        {"$match": {"role": "user"}},
        {"$group": {
            "_id": "$session_id",
            "title": {"$first": "$content"},
            "ts": {"$max": "$ts"},
        }},
        {"$sort": {"ts": -1}},
        {"$limit": limit}
    ]
    cur = coll.aggregate(pipeline)
    result = []
    for row in cur:
        title = row.get("title", "New Chat")
        if len(title) > 30:
            title = title[:27] + "..."
        result.append({
            "session_id": row["_id"],
            "title": title,
            "ts": row.get("ts").isoformat() if row.get("ts") else None
        })
    return result


def get_session_history(session_id: str) -> list[dict[str, Any]]:
    coll = _collection()
    if coll is None:
        return []
    cur = (
        coll.find({"session_id": session_id}, {"_id": 0, "role": 1, "content": 1, "meta": 1})
        .sort("ts", 1)
    )
    result = []
    for r in cur:
        result.append({
            "role": r["role"],
            "text": r["content"],
            "meta": r.get("meta")
        })
    return result
