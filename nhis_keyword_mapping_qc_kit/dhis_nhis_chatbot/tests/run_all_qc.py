"""Run all NHIS chatbot QC scripts in sequence.

Place this file in dhis_nhis_chatbot/tests/ and run from the project root:
    python tests/run_all_qc.py

This script stops at the end and reports pass/fail for each QC module. It does not
modify data files.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "tests/run_qc.py",
    "tests/run_phase3_qc.py",
    "tests/run_phase4_qc.py",
    "tests/run_phase5_qc.py",
    "tests/run_phase6_qc.py",
    "tests/run_phase6c_qc.py",
]


def main() -> int:
    results = []
    for script in SCRIPTS:
        path = ROOT / script
        if not path.exists():
            results.append((script, "MISSING", 1))
            print(f"\n=== {script}: MISSING ===")
            continue
        print(f"\n=== Running {script} ===")
        proc = subprocess.run([sys.executable, str(path)], cwd=str(ROOT), text=True)
        status = "PASS" if proc.returncode == 0 else "FAIL"
        results.append((script, status, proc.returncode))

    print("\n=== QC SUMMARY ===")
    for script, status, code in results:
        print(f"{status:7} {script} (exit={code})")

    return 0 if all(code == 0 for _, _, code in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
