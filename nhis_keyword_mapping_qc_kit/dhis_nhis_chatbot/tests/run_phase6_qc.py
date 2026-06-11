#!/usr/bin/env python
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from ask_router import ask
from model_orchestrator import get_openai_status, polish_answer


def check(name: str, condition: bool, details: str = "") -> tuple[str, bool, str]:
    return name, bool(condition), details


def main() -> int:
    checks = []

    # Force no-key fallback behavior for this QC; do not use real API calls.
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    old_use = os.environ.pop("USE_OPENAI", None)
    try:
        status = get_openai_status(requested=False)
        checks.append(check("OpenAI disabled without key", status["effective_enabled"] is False, str(status)))

        original = "2024 estimate: 8.0% (95% CI: 7.5-8.5). Source: test."
        answer, meta = polish_answer("test", original, evidence={"source":"test"}, use_model=True)
        checks.append(check("use_model without key returns deterministic answer", answer == original, str(meta)))
        checks.append(check("metadata records missing key", meta.get("reason") == "OPENAI_API_KEY_not_set", str(meta)))

        result = ask("What percent of adults had current asthma last year?", debug=True, use_model=True)
        checks.append(check("ask with use_model no key still succeeds", result.get("status") == "ok", result.get("answer", "")[:200]))
        checks.append(check("ask result includes model metadata", isinstance(result.get("model"), dict), str(result.get("model"))))
        checks.append(check("model metadata indicates no model used", result.get("model", {}).get("used_model") is False, str(result.get("model"))))

        faq = ask("What is NHIS?", debug=True, use_model=True)
        checks.append(check("FAQ with use_model no key still returns a routed result", faq.get("status") in {"ok", "not_found"}, str(faq)[:300]))

    finally:
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key
        if old_use is not None:
            os.environ["USE_OPENAI"] = old_use

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"Phase 6 OpenAI layer QC: {passed} / {total} passed")
    for name, ok, details in checks:
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\t{details}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
