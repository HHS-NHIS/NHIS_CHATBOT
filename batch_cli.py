from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.append(str(SRC))

from retrieve_estimate import retrieve  # noqa: E402


def read_questions(path: Path, question_col: str) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")
        fields = reader.fieldnames
        col = question_col if question_col in fields else None
        if col is None:
            lowered = {c.lower().strip(): c for c in fields}
            for candidate in ["question", "prompt", "query", "text"]:
                if candidate in lowered:
                    col = lowered[candidate]
                    break
        if col is None:
            raise ValueError(f"Could not find a question column. Use --question-col. Columns found: {fields}")
        rows = []
        for i, row in enumerate(reader, start=1):
            q = (row.get(col) or "").strip()
            if q:
                row["_row_number"] = i
                row["_question_col"] = col
                rows.append(row)
        return rows


def flatten_debug(debug: dict) -> dict:
    if not isinstance(debug, dict):
        return {}
    topic_meta = debug.get("topic_meta") or {}
    group_meta = debug.get("group_meta") or {}
    year_meta = debug.get("year_meta") or {}
    return {
        "debug_reason": debug.get("reason", ""),
        "parsed_population": debug.get("population", ""),
        "parsed_years": ";".join(map(str, debug.get("years", []) or [])),
        "year_mode": year_meta.get("mode", ""),
        "year_explanation": year_meta.get("explanation", ""),
        "matched_outcome": debug.get("outcome", ""),
        "matched_grouping_label": debug.get("label", ""),
        "matched_group_value": debug.get("group", ""),
        "rows_returned": debug.get("rows_returned", ""),
        "topic_match_method": topic_meta.get("method", ""),
        "topic_match_score": topic_meta.get("score", ""),
        "topic_match_keyword": topic_meta.get("keyword", ""),
        "topic_mapped_topic": topic_meta.get("mapped_topic", ""),
        "requested_group_keys": ";".join(group_meta.get("requested_keys", []) or []),
        "requested_group_values": ";".join(group_meta.get("requested_values", []) or []),
        "group_is_composite": group_meta.get("is_composite", ""),
        "group_explanation": group_meta.get("explanation", ""),
        "raw_debug_json": json.dumps(debug, ensure_ascii=False, default=str),
    }


def run_batch(input_csv: Path, output_csv: Path, question_col: str = "question") -> None:
    rows = read_questions(input_csv, question_col)
    out_rows = []
    for row in rows:
        q = (row.get(row["_question_col"]) or "").strip()
        base = {
            "input_row": row["_row_number"],
            "question": q,
        }
        try:
            debug_result = retrieve(q, debug=True)
            result = debug_result
            debug = debug_result.get("debug") or {}
            out = {
                **base,
                "status": result.get("status", ""),
                "answer": result.get("answer", ""),
                "answer_debug_text": debug_result.get("answer", ""),
                "error": "",
                **flatten_debug(debug),
            }
        except Exception as e:
            out = {
                **base,
                "status": "exception",
                "answer": "",
                "answer_debug_text": "",
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
        out_rows.append(out)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    for r in out_rows:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)
    with output_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-submit DHIS/NHIS chatbot questions and write a debug CSV.")
    parser.add_argument("input_csv", help="CSV with a question/prompt/query column")
    parser.add_argument("--output", "-o", default="tests/batch_debug_output.csv", help="Output debug CSV path")
    parser.add_argument("--question-col", default="question", help="Input column containing questions; default: question")
    args = parser.parse_args()
    run_batch(Path(args.input_csv), Path(args.output), args.question_col)
