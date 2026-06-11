#!/usr/bin/env python
from pathlib import Path
import csv
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from ask_router import ask

IN = ROOT / "tests" / "api_phase3_questions.csv"
OUT = ROOT / "tests" / "qc_reports" / "phase3_api_faq_qc_report.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)
rows = []
passed = 0
with IN.open(newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        res = ask(r["question"], debug=True)
        mode = res.get("mode", "")
        status = res.get("status", "")
        ok = status in {"ok", "not_found"} and bool(res.get("answer"))
        if r["expected_mode"] == "estimate" and mode != "estimate":
            ok = False
        if r["expected_mode"] == "faq" and mode != "faq":
            ok = False
        passed += int(ok)
        rows.append({"question": r["question"], "expected_mode": r["expected_mode"], "status": status, "mode": mode, "pass": ok, "answer_preview": (res.get("answer") or "")[:300].replace("\n", " ")})
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)
print(f"Phase 3 QC complete. Passed: {passed} / {len(rows)}")
print(f"Report: {OUT}")
if passed != len(rows):
    raise SystemExit(1)
