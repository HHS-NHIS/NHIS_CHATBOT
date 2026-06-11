from __future__ import annotations
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from retrieve_estimate import retrieve


def main() -> int:
    path = ROOT / "tests" / "demo_questions.csv"
    rows = list(csv.DictReader(open(path, newline='', encoding='utf-8')))
    failures = []
    for row in rows:
        result = retrieve(row['question'], debug=True)
        status = result['status']
        answer = result['answer']
        expected_contains = (row.get('expected_contains') or '').strip()
        ok = status == row['expected_status'] and (not expected_contains or expected_contains in answer)
        print("=" * 90)
        print(f"QUESTION: {row['question']}")
        print(f"EXPECTED: {row['expected_status']} | GOT: {status} | {'PASS' if ok else 'FAIL'}")
        if expected_contains:
            print(f"EXPECTED CONTAINS: {expected_contains!r}")
        print(answer)
        if not ok:
            failures.append((row['question'], row['expected_status'], status, expected_contains, result.get('debug')))
    print("=" * 90)
    print(f"QC complete. Passed: {len(rows) - len(failures)} / {len(rows)}")
    if failures:
        print("Failures:")
        for failure in failures:
            print(failure)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
