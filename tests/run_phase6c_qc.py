from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ask_router import ask

CASES = [
    ("What percent of teens had current asthma last year?", "teen_redirect", "NHIS Teen Summary Health Statistics"),
    ("What percent of teenagers were uninsured in 2024?", "teen_redirect", "NHIS Teen Summary Health Statistics"),
    ("Where is the NHIS teen SHS tool?", "teen_redirect", "NHIS Teen Summary Health Statistics"),
    ("What percent of adolescents had current asthma last year?", "estimate", "children"),
    ("What percent of youth got a flu shot last year?", "estimate", "children"),
    ("What percent of adolescents were uninsured last year?", "estimate", "children"),
]

passed = 0
rows = []
for q, expected_mode, expected_text in CASES:
    res = ask(q, debug=True, use_model=False)
    mode = res.get('mode', '')
    answer = res.get('answer', '')
    debug = res.get('debug', {})
    population = debug.get('population') or debug.get('matched_population') or debug.get('selected_population') or ''
    ok_mode = mode == expected_mode or (expected_mode == 'estimate' and mode.startswith('estimate'))
    ok_text = expected_text.lower() in (answer + ' ' + str(debug)).lower() or expected_text.lower() in str(population).lower()
    ok = ok_mode and ok_text
    passed += int(ok)
    rows.append((q, mode, population, ok, answer[:250].replace('\n',' ')))

outdir = ROOT / 'tests' / 'qc_reports'
outdir.mkdir(parents=True, exist_ok=True)
with (outdir / 'phase6c_teen_child_qc_report.csv').open('w', encoding='utf-8') as f:
    f.write('question,mode,population,passed,answer_excerpt\n')
    for r in rows:
        f.write('"{}","{}","{}",{},"{}"\n'.format(*(str(x).replace('"','""') for x in r)))
summary = f"Phase 6C teen/adolescent routing QC: {passed} / {len(CASES)} passed\n"
(outdir / 'phase6c_teen_child_qc_summary.txt').write_text(summary, encoding='utf-8')
print(summary)
if passed != len(CASES):
    raise SystemExit(1)
