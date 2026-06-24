#!/usr/bin/env python
"""QC for NHIS Assistant V2A/B local testing build."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'src'))
from ask_router import ask

checks = []

def check(name, condition, detail=''):
    checks.append((name, bool(condition), detail))
    print(('PASS' if condition else 'FAIL'), name, detail)

# Participation/resource follow-up should not fall to SHS estimate fallback.
r1 = ask('Why should I participate in NHIS?', debug=True)
cid = r1['conversation_id']
r2 = ask('tell me more', conversation_id=cid, debug=True)
check('participation first turn routes FAQ', r1.get('mode') == 'faq' and r1.get('status') == 'ok', r1.get('mode'))
check('tell me more inherits participation context', r2.get('mode') == 'faq' and r2.get('context_resolution',{}).get('used_followup_context'), r2.get('resolved_question'))
check('tell me more did not fall to estimate fallback', 'estimate' not in str(r2.get('mode')), r2.get('mode'))

# Estimate follow-ups should still work.
r3 = ask('What percent of adults had diabetes last year?', debug=True)
cid2 = r3['conversation_id']
r4 = ask('What about by SVI?', conversation_id=cid2, debug=True)
r5 = ask('Show last 2 years.', conversation_id=cid2, debug=True)
check('adult diabetes routes estimate', r3.get('mode') == 'estimate' and r3.get('status') == 'ok', r3.get('mode'))
check('SVI follow-up routes estimate with context', r4.get('mode') == 'estimate' and r4.get('context_resolution',{}).get('used_followup_context'), r4.get('resolved_question'))
check('last 2 years follow-up routes estimate with context', r5.get('mode') == 'estimate' and r5.get('context_resolution',{}).get('used_followup_context'), r5.get('resolved_question'))

# Teen exception split.
r6 = ask('Why should teens participate in NHIS?', debug=True)
r7 = ask('What percent of teens had asthma last year?', debug=True)
check('teen participation routes FAQ', r6.get('mode') == 'faq' and r6.get('status') == 'ok', r6.get('mode'))
check('teen estimate routes redirect', r7.get('mode') == 'teen_redirect', r7.get('mode'))

# Editable resource structure exists.
check('approved_urls.csv exists', (ROOT/'resources/approved_urls.csv').exists())
check('approved_documents folder exists', (ROOT/'resources/approved_documents').exists())
check('generated faq index exists', (ROOT/'resources/generated/faq_index_seed.json').exists())
check('resource builder exists', (ROOT/'scripts/build_resource_index.py').exists())

# UI strings indicate V2 chat transcript.
api = (ROOT/'api_server.py').read_text(encoding='utf-8')
check('prod UI has GPT-like chat container', 'id="chat" class="chat"' in api and 'NHIS Assistant Prototype' in api)
check('embed UI has chat container', 'nhis_embed_v2_conversation_id' in api)

passed = sum(1 for _, ok, _ in checks if ok)
print(f"V2A/B QC: {passed} / {len(checks)} passed")
raise SystemExit(0 if passed == len(checks) else 1)
