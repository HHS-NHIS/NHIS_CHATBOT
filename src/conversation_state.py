from __future__ import annotations

"""Lightweight conversation context for NHIS Assistant V2.

This is prototype session state, not permanent memory. It stores the last
successful answer context so vague follow-ups like "tell me more" can inherit
the prior answer lane (estimate vs FAQ/resource vs teen redirect) instead of
falling through to the wrong router path.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

_CONTEXTS: Dict[str, Dict[str, Any]] = {}
_TURNS: Dict[str, list[Dict[str, Any]]] = {}


def new_conversation_id() -> str:
    return str(uuid.uuid4())


def get_context(conversation_id: str | None) -> Optional[Dict[str, Any]]:
    if not conversation_id:
        return None
    return _CONTEXTS.get(conversation_id)


def get_turns(conversation_id: str | None) -> list[Dict[str, Any]]:
    if not conversation_id:
        return []
    return _TURNS.get(conversation_id, [])


def clear_context(conversation_id: str | None) -> None:
    if not conversation_id:
        return
    _CONTEXTS.pop(conversation_id, None)
    _TURNS.pop(conversation_id, None)


def _answer_type_from_result(result: Dict[str, Any]) -> str:
    mode = str(result.get("mode") or "").lower()
    if mode == "estimate":
        return "estimate"
    if mode in {"faq", "resource", "participation_resource"}:
        # We keep participation and general FAQ under a broad resource lane; the
        # source cards/categories preserve the more specific source type.
        return "participation_resource" if _looks_participantish_result(result) else "general_nhis_faq"
    if "teen" in mode:
        return "teen_redirect"
    if "documentation" in mode:
        return "documentation_link"
    if "explanation" in mode:
        return "ci_explanation"
    if "clarification" in mode:
        return "clarification"
    if "not_found" in mode:
        return "not_found"
    return mode or "unknown"


def _looks_participantish_result(result: Dict[str, Any]) -> bool:
    joined = " ".join([
        str(result.get("answer") or ""),
        " ".join(str(c.get("title") or "") + " " + str(c.get("source_category") or "") + " " + str(c.get("url") or "") for c in result.get("source_cards") or [] if isinstance(c, dict)),
    ]).lower()
    return any(k in joined for k in [
        "particip", "participant", "respondent", "privacy", "confidential", "what to expect",
        "real-life benefits", "real life benefits", "impact", "talking points", "selected"
    ])


def summarize_context(ctx: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not ctx:
        return {}
    keys = [
        "last_question", "last_resolved_question", "last_mode", "answer_type", "population",
        "outcome", "label", "group", "years", "source_titles", "source_urls", "updated_at",
    ]
    return {k: ctx.get(k) for k in keys if k in ctx}


def update_from_result(conversation_id: str, original_question: str, resolved_question: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Store the last useful context for any answer lane, not just estimates."""
    now = datetime.now(timezone.utc).isoformat()
    turns = _TURNS.setdefault(conversation_id, [])
    turns.append({
        "turn_id": len(turns) + 1,
        "user_question": original_question,
        "resolved_question": resolved_question,
        "mode": result.get("mode"),
        "status": result.get("status"),
        "answer_type": _answer_type_from_result(result),
        "created_at": now,
    })

    answer_type = _answer_type_from_result(result)
    debug = result.get("debug") or {}
    source_cards = result.get("source_cards") or []
    source_titles = [str(c.get("title")) for c in source_cards if isinstance(c, dict) and c.get("title")]
    source_urls = [str(c.get("url")) for c in source_cards if isinstance(c, dict) and c.get("url")]

    # Preserve estimate fields when they exist; they support estimate follow-ups.
    ctx = {
        "conversation_id": conversation_id,
        "last_question": original_question,
        "last_resolved_question": resolved_question,
        "last_mode": result.get("mode"),
        "answer_type": answer_type,
        "status": result.get("status"),
        "population": debug.get("population"),
        "outcome": debug.get("outcome"),
        "label": debug.get("label"),
        "group": debug.get("group"),
        "years": debug.get("years"),
        "year_meta": debug.get("year_meta"),
        "topic_meta": debug.get("topic_meta"),
        "group_meta": debug.get("group_meta"),
        "source_titles": source_titles,
        "source_urls": source_urls,
        "source_cards": source_cards,
        "last_answer_excerpt": str(result.get("answer") or "")[:1200],
        "turn_count": len(turns),
        "updated_at": now,
    }

    # Do not let not_found estimate fallbacks overwrite a useful prior FAQ/estimate context.
    if result.get("status") == "ok" or answer_type in {"teen_redirect", "documentation_link", "ci_explanation"}:
        _CONTEXTS[conversation_id] = ctx
    elif conversation_id not in _CONTEXTS:
        _CONTEXTS[conversation_id] = ctx
    return _CONTEXTS.get(conversation_id, ctx)
