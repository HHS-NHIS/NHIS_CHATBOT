#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from ask_router import ask
import api_server

CASES = [
    ('Why should teens participate in NHIS?', 'faq', 'ok', 'Teen Summary Health Statistics tool'),
    ('What percent of teens had asthma last year?', 'teen_redirect', 'not_found', 'NHIS Teen Summary Health Statistics tool'),
    ('Why should kids participate in NHIS?', 'faq', 'ok', 'particip'),
    ('Why should adults participate in NHIS?', 'faq', 'ok', 'particip'),
    ('Is my teen\'s information private and secure?', 'faq', 'ok', 'Teen Summary Health Statistics tool'),
    ('How has NHIS data helped with diabetes?', 'faq', 'ok', 'diabetes'),
    ('What should I expect if selected for NHIS?', 'faq', 'ok', 'expect'),
]

def main():
    failures=[]
    for q, exp_mode, exp_status, forbidden in CASES:
        r=ask(q, debug=True, use_model=False)
        mode=r.get('mode')
        status=r.get('status')
        ans=str(r.get('answer',''))
        ok = (mode == exp_mode and status == exp_status)
        if exp_mode == 'faq' and 'Teen estimates are not included' in ans:
            ok = False
        if exp_mode == 'teen_redirect' and 'Teen estimates are not included' not in ans:
            ok = False
        print(('PASS' if ok else 'FAIL'), q, '=>', mode, status)
        if not ok:
            failures.append({'question':q,'mode':mode,'status':status,'answer':ans[:250]})
    ui_ok = hasattr(api_server, 'PROD_HTML') and hasattr(api_server, 'EMBED_HTML') and hasattr(api_server, 'DEBUG_HTML')
    print(('PASS' if ui_ok else 'FAIL'), 'UI constants present')
    if not ui_ok:
        failures.append({'question':'UI constants','mode':'missing','status':'fail','answer':''})
    if failures:
        print('\nFailures:')
        for f in failures:
            print(f)
        raise SystemExit(1)
    print(f'Phase 7E router/UI QC: {len(CASES)+1} / {len(CASES)+1} passed')
if __name__ == '__main__':
    main()
