from __future__ import annotations

"""Lightweight local conversation context for Phase 7 interactive follow-ups.

This is intentionally session-scoped prototype state, not a permanent memory system.
It stores only the last successful structured result needed to resolve follow-up
questions like "what about by sex?" or "show last 2 years." 
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

# In-memory store is enough for the local demo. It resets when the server restarts.
_CONTEXTS: Dict[str, Dict[str, Any]] = {}


def new_conversation_id() -> str:
    return str(uuid.uuid4())


def get_context(conversation_id: str | None) -> Optional[Dict[str, Any]]:
    if not conversation_id:
        return None
    return _CONTEXTS.get(conversation_id)


def clear_context(conversation_id: str | None) -> None:
    if conversation_id and conversation_id in _CONTEXTS:
        del _CONTEXTS[conversation_id]


def summarize_context(ctx: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not ctx:
        return {}
    keys = [
        "last_question", "last_resolved_question", "last_mode", "population",
        "outcome", "label", "group", "years", "updated_at",
    ]
    return {k: ctx.get(k) for k in keys if k in ctx}


def update_from_result(conversation_id: str, original_question: str, resolved_question: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Store last successful estimate context. FAQ contexts are not used for estimate follow-ups."""
    debug = result.get("debug") or {}
    if result.get("status") == "ok" and result.get("mode") == "estimate" and debug.get("outcome"):
        ctx = {
            "conversation_id": conversation_id,
            "last_question": original_question,
            "last_resolved_question": resolved_question,
            "last_mode": result.get("mode"),
            "population": debug.get("population"),
            "outcome": debug.get("outcome"),
            "label": debug.get("label"),
            "group": debug.get("group"),
            "years": debug.get("years"),
            "year_meta": debug.get("year_meta"),
            "topic_meta": debug.get("topic_meta"),
            "group_meta": debug.get("group_meta"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _CONTEXTS[conversation_id] = ctx
        return ctx
    return _CONTEXTS.get(conversation_id, {})
