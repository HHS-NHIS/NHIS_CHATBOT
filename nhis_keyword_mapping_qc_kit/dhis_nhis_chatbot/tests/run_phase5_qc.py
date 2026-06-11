#!/usr/bin/env python
"""Phase 5 QC: feedback logging + core API-callable functions.

Run from project root:
  python tests/run_phase5_qc.py
"""
from __future__ import annotations
from pathlib import Path
import csv
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ask_router import ask
from feedback_logger import append_feedback, read_feedback_rows, FEEDBACK_CSV, FEEDBACK_JSONL
from faq_retriever import answer_faq

REPORT = ROOT / "tests" / "qc_reports" / "phase5_feedback_qc_report.csv"
SUMMARY = ROOT / "tests" / "qc_reports" / "phase5_feedback_qc_summary.txt"


def check(name: str, passed: bool, detail: str = "") -> dict:
    return {"check": name, "passed": "PASS" if passed else "FAIL", "detail": detail}


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    # 1. Estimate route still works through /api/ask-equivalent function.
    est = ask("What percent of adults had current asthma last year?", debug=True, use_model=False)
    rows.append(check("ask_estimate_route_status_ok", est.get("status") == "ok", est.get("answer", "")[:160]))
    rows.append(check("ask_estimate_route_mode", est.get("mode") == "estimate", str(est.get("mode"))))

    # 2. FAQ route still works through local seed index.
    faq = answer_faq("What is NHIS?", debug=True)
    rows.append(check("faq_route_returns_source_or_safe_not_found", faq.get("status") in {"ok", "not_found"}, faq.get("status", "")))
    if faq.get("status") == "ok":
        rows.append(check("faq_has_source_cards", bool(faq.get("source_cards")), str(len(faq.get("source_cards", [])))))
    else:
        rows.append(check("faq_safe_not_found_message", "do not have enough information" in faq.get("answer", "").lower(), faq.get("answer", "")[:160]))

    # 3. Feedback logging appends a row and exposes it through read_feedback_rows.
    before = len(read_feedback_rows(limit=100000))
    payload = {
        "feedback_label": "QC test feedback",
        "reviewer_note": "Automated Phase 5 QC test row.",
        "question": "What percent of adults had current asthma last year?",
        "answer": est.get("answer", ""),
        "result": est,
    }
    fb = append_feedback(payload)
    after_rows = read_feedback_rows(limit=100000)
    after = len(after_rows)
    rows.append(check("feedback_append_status_ok", fb.get("status") == "ok", str(fb)))
    rows.append(check("feedback_row_count_incremented", after == before + 1, f"before={before}; after={after}"))
    rows.append(check("feedback_csv_exists", FEEDBACK_CSV.exists(), str(FEEDBACK_CSV)))
    rows.append(check("feedback_jsonl_exists", FEEDBACK_JSONL.exists(), str(FEEDBACK_JSONL)))
    last = after_rows[-1] if after_rows else {}
    rows.append(check("feedback_last_label_preserved", last.get("feedback_label") == "QC test feedback", str(last.get("feedback_label"))))
    rows.append(check("feedback_question_preserved", "current asthma" in last.get("question", "").lower(), last.get("question", "")))

    with REPORT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "detail"])
        writer.writeheader(); writer.writerows(rows)

    passed = sum(1 for r in rows if r["passed"] == "PASS")
    total = len(rows)
    summary = f"Phase 5 feedback/API QC: {passed} / {total} passed\nReport: {REPORT}\nFeedback log: {FEEDBACK_CSV}\n"
    SUMMARY.write_text(summary, encoding="utf-8")
    print(summary)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
