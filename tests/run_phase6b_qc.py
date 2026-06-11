#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from ask_router import ask

TEEN_URL = "https://wwwn.cdc.gov/NHISDataQueryTool/NHIS_teen/index.html"


def check(name: str, condition: bool, details: str = "") -> tuple[str, bool, str]:
    return name, bool(condition), details


def main() -> int:
    checks = []
    teen_questions = [
        "What percent of teens had current asthma last year?",
        "How many adolescents got a flu shot last year?",
        "What percent of teenagers were uninsured in 2024?",
        "Show youth depression estimates last year.",
    ]
    for q in teen_questions:
        r = ask(q, debug=True, use_model=False)
        checks.append(check(f"teen redirect: {q}", r.get("mode") == "teen_redirect" and TEEN_URL in r.get("answer", ""), str(r)[:500]))
        checks.append(check(f"teen redirect source card: {q}", any(c.get("url") == TEEN_URL for c in r.get("source_cards", [])), str(r.get("source_cards"))))

    adult = ask("What percent of adults had current asthma last year?", debug=True, use_model=False)
    checks.append(check("adult estimate unaffected", adult.get("status") == "ok" and adult.get("mode") == "estimate", adult.get("answer", "")[:300]))

    child = ask("What percent of kids got a flu shot last year?", debug=True, use_model=False)
    checks.append(check("child estimate unaffected", child.get("status") == "ok" and child.get("mode") == "estimate", child.get("answer", "")[:300]))

    faq = ask("What is NHIS?", debug=True, use_model=False)
    checks.append(check("FAQ routing unaffected", faq.get("mode") == "faq" and faq.get("status") in {"ok", "not_found"}, str(faq)[:300]))

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"Phase 6B teen redirect QC: {passed} / {total} passed")
    for name, ok, details in checks:
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\t{details}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
