#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'src'))
from ask_router import ask

TESTS = [
    ('follow-up uses same conversation', ['What percent of adults had diabetes last year?', 'What about by SVI?'], lambda r: r[-1].get('status') == 'ok' and r[-1].get('context_resolution', {}).get('used_followup_context') is True and 'SVI' in r[-1].get('resolved_question','')),
    ('follow-up last 2 years', ['What percent of adults had diabetes last year?', 'Show last 2 years.'], lambda r: r[-1].get('status') == 'ok' and 'last 2 years' in r[-1].get('resolved_question','')),
    ('why participate routes FAQ', ['Why should I participate in NHIS?'], lambda r: r[-1].get('mode') == 'faq' and 'participate' in r[-1].get('answer','').lower()),
    ('privacy routes participant privacy', ['Is my information private and secure?'], lambda r: r[-1].get('mode') == 'faq' and any('privacy' in (c.get('title','').lower()) for c in r[-1].get('source_cards',[]))),
    ('what to expect selected routes participant page', ['What should I expect if I was selected for NHIS?'], lambda r: r[-1].get('mode') == 'faq' and any('what to expect' in (c.get('title','').lower()) for c in r[-1].get('source_cards',[]))),
    ('impact benefits routes job aid', ['How does NHIS data help real people?'], lambda r: r[-1].get('mode') == 'faq' and any('benefit' in (c.get('title','').lower()) or 'impact' in (c.get('title','').lower()) for c in r[-1].get('source_cards',[]))),
    ('diabetes impact does not return estimate', ['How has NHIS data helped with diabetes?'], lambda r: r[-1].get('mode') == 'faq' and r[-1].get('status') == 'ok'),
    ('adolescent still child estimate', ['How many adolescents got a flu shot last year?'], lambda r: r[-1].get('mode') == 'estimate' and 'Children' in r[-1].get('answer','')),
    ('teen still redirects', ['What percent of teens had asthma last year?'], lambda r: r[-1].get('mode') == 'teen_redirect'),
]

passed = 0
for name, qs, check in TESTS:
    cid = None
    results = []
    for q in qs:
        res = ask(q, debug=True, conversation_id=cid)
        cid = res.get('conversation_id') or cid
        results.append(res)
    ok = bool(check(results))
    passed += int(ok)
    print(('PASS' if ok else 'FAIL') + '\t' + name + '\t' + (results[-1].get('answer','')[:220].replace('\n',' ')))

print(f'Phase 7D interactive UI/participant resource QC: {passed} / {len(TESTS)} passed')
if passed != len(TESTS):
    raise SystemExit(1)
