from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import uuid
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_DIR = ROOT / "data" / "feedback"
FEEDBACK_CSV = FEEDBACK_DIR / "feedback_log.csv"
FEEDBACK_JSONL = FEEDBACK_DIR / "feedback_log.jsonl"

FIELDNAMES = [
    "feedback_id", "timestamp_utc", "feedback_label", "reviewer_note",
    "question", "answer", "status", "mode",
    "matched_population", "matched_topic", "matched_grouping", "matched_subgroup",
    "matched_years", "source_file", "source_url", "debug_json"
]


def _safe_str(value: Any, max_len: int | None = None) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        out = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        out = str(value)
    out = out.replace("\r\n", "\n").replace("\r", "\n")
    if max_len and len(out) > max_len:
        return out[:max_len] + "…"
    return out


def _extract_debug_field(result: dict, keys: list[str]) -> str:
    """Look for a value in common debug/result locations without depending on one schema."""
    candidates = [result, result.get("debug", {}) if isinstance(result.get("debug"), dict) else {}]
    # Some estimate results nest matched details one level deeper.
    dbg = result.get("debug") if isinstance(result.get("debug"), dict) else {}
    for nested in ("match", "matched", "query", "source", "parsed", "filters"):
        if isinstance(dbg.get(nested), dict):
            candidates.append(dbg[nested])
    for c in candidates:
        for k in keys:
            if k in c and c[k] not in (None, "", []):
                return _safe_str(c[k])
    return ""


def _first_source_url(result: dict) -> str:
    for key in ("source_cards", "citations"):
        items = result.get(key)
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict) and first.get("url"):
                return str(first.get("url"))
    dbg = result.get("debug") if isinstance(result.get("debug"), dict) else {}
    for k in ("source_url", "url"):
        if dbg.get(k):
            return str(dbg[k])
    return ""


def make_feedback_record(payload: dict) -> dict:
    """Normalize a browser/API feedback payload into one durable CSV/JSONL row."""
    result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    debug_obj = result.get("debug", {}) if isinstance(result.get("debug"), dict) else {}
    record = {
        "feedback_id": uuid.uuid4().hex,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "feedback_label": _safe_str(payload.get("feedback_label") or payload.get("label") or payload.get("feedback_type")),
        "reviewer_note": _safe_str(payload.get("reviewer_note") or payload.get("note"), max_len=2000),
        "question": _safe_str(payload.get("question") or result.get("question"), max_len=5000),
        "answer": _safe_str(payload.get("answer") or result.get("answer"), max_len=12000),
        "status": _safe_str(result.get("status")),
        "mode": _safe_str(result.get("mode")),
        "matched_population": _extract_debug_field(result, ["population", "matched_population", "source_population"]),
        "matched_topic": _extract_debug_field(result, ["topic", "outcome", "matched_topic", "Outcome (or Indicator)", "outcome_label"]),
        "matched_grouping": _extract_debug_field(result, ["grouping", "col_label", "grouping_label", "matched_grouping"]),
        "matched_subgroup": _extract_debug_field(result, ["group", "subgroup", "matched_subgroup", "Group"]),
        "matched_years": _extract_debug_field(result, ["years", "year", "matched_years", "Year"]),
        "source_file": _extract_debug_field(result, ["source_file", "file", "dataset", "source"]),
        "source_url": _first_source_url(result),
        "debug_json": _safe_str(debug_obj, max_len=50000),
    }
    return record


def append_feedback(payload: dict) -> dict:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    record = make_feedback_record(payload)
    write_header = not FEEDBACK_CSV.exists() or FEEDBACK_CSV.stat().st_size == 0
    with FEEDBACK_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(record)
    with FEEDBACK_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"status": "ok", "feedback_id": record["feedback_id"], "feedback_csv": str(FEEDBACK_CSV.relative_to(ROOT))}


def read_feedback_rows(limit: int = 100) -> list[dict]:
    if not FEEDBACK_CSV.exists():
        return []
    with FEEDBACK_CSV.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if limit and len(rows) > limit:
        return rows[-limit:]
    return rows


def export_feedback_csv() -> str:
    if not FEEDBACK_CSV.exists():
        return ",".join(FIELDNAMES) + "\n"
    return FEEDBACK_CSV.read_text(encoding="utf-8")
