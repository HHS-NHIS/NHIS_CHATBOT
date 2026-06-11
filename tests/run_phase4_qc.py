#!/usr/bin/env python
from pathlib import Path
import csv
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from ask_router import ask

IN = ROOT / "tests" / "api_phase4_questions.csv"
OUT = ROOT / "tests" / "qc_reports" / "phase4_widget_faq_qc_report.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)
rows = []
passed = 0
with IN.open(newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        res = ask(r["question"], debug=True)
        mode = res.get("mode", "")
        status = res.get("status", "")
        source_cards = res.get("source_cards", [])
        why = res.get("why", [])
        ok = bool(res.get("answer"))
        if r["expected_mode"] and mode != r["expected_mode"]:
            ok = False
        if r["expected_status"] and status != r["expected_status"]:
            ok = False
        if r["expect_source_cards"] == "yes" and not source_cards:
            ok = False
        if r["expect_source_cards"] == "no" and source_cards:
            ok = False
        if r["expect_why"] == "yes" and not why:
            ok = False
        passed += int(ok)
        rows.append({
            "question": r["question"],
            "expected_mode": r["expected_mode"],
            "mode": mode,
            "expected_status": r["expected_status"],
            "status": status,
            "source_card_count": len(source_cards),
            "why_count": len(why),
            "pass": ok,
            "answer_preview": (res.get("answer") or "")[:300].replace("\n", " "),
        })
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)
print(f"Phase 4A QC complete. Passed: {passed} / {len(rows)}")
print(f"Report: {OUT}")
if passed != len(rows):
    raise SystemExit(1)
