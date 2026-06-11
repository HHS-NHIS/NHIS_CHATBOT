#!/usr/bin/env python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from ask_router import ask

checks = []

def add(name, ok, detail=""):
    checks.append((name, bool(ok), detail))

# Multi-turn: first establish context.
r1 = ask("What percent of adults had diabetes last year?", debug=True)
cid = r1.get("conversation_id")
add("initial adult diabetes estimate ok", r1.get("status") == "ok" and r1.get("mode") == "estimate", r1.get("answer", "")[:200])
add("conversation id returned", bool(cid), str(cid))
add("context saved adult diabetes", (r1.get("conversation_context") or {}).get("outcome") is not None, str(r1.get("conversation_context")))

r2 = ask("What about by SVI?", debug=True, conversation_id=cid)
add("follow-up by SVI ok", r2.get("status") == "ok" and "Social vulnerability" in r2.get("answer", ""), r2.get("resolved_question", ""))
add("follow-up context flag", r2.get("context_resolution", {}).get("used_followup_context") is True, str(r2.get("context_resolution")))
add("suggested followups returned", bool(r2.get("suggested_followups")), str(r2.get("suggested_followups")))

r3 = ask("Show last 2 years", debug=True, conversation_id=cid)
add("follow-up last 2 years ok", r3.get("status") == "ok" and "latest 2 years" in r3.get("answer", ""), r3.get("resolved_question", ""))

r4 = ask("What about kids?", debug=True, conversation_id=cid)
add("follow-up kids routes child or safe not found", r4.get("mode") in {"estimate", "estimate_not_found"} and ("Children" in r4.get("answer", "") or "Child" in str(r4.get("debug", {})) or r4.get("status") == "not_found"), r4.get("resolved_question", ""))

r5 = ask("Explain the confidence interval", debug=True, conversation_id=cid)
add("CI explanation follow-up direct", r5.get("mode") == "explanation" and "confidence interval" in r5.get("answer", "").lower(), r5.get("answer", "")[:200])

r6 = ask("Where do I get the data?", debug=True, conversation_id=cid)
add("data documentation follow-up direct", r6.get("mode") == "documentation_followup" and "documentation" in r6.get("answer", "").lower(), r6.get("answer", "")[:200])

r7 = ask("What percent of teens had asthma last year?", debug=True)
add("teen still redirects", r7.get("mode") == "teen_redirect", r7.get("answer", "")[:200])

r8 = ask("What percent of adolescents got a flu shot last year?", debug=True)
add("adolescent routes child not teen", r8.get("mode") == "estimate" and "Children" in r8.get("answer", ""), r8.get("answer", "")[:200])

# Optional model structured routing should safely fall back without key.
r9 = ask("What about by sex?", debug=True, conversation_id=cid, use_model=True)
meta = r9.get("context_resolution", {}).get("model_followup", {})
add("use_model follow-up without key safely falls back", r9.get("status") == "ok" and meta.get("fallback_to_deterministic") is True, str(meta))

passed = sum(1 for _, ok, _ in checks if ok)
print(f"Phase 7 interactive QC: {passed} / {len(checks)} passed")
for name, ok, detail in checks:
    print(("PASS" if ok else "FAIL") + "\t" + name + "\t" + str(detail).replace("\n", " ")[:500])
if passed != len(checks):
    raise SystemExit(1)
