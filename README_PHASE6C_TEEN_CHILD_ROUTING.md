# Phase 6C teen/adolescent routing patch

This patch narrows teen redirects and restores youth/adolescent/adolescents to child SHS routing.

## Rules

- `teen`, `teens`, `teenager`, `teenagers`, `NHIS teen`, `NHIS-teen`, `teen SHS`, `teen summary` → redirect to the NHIS Teen Summary Health Statistics tool.
- `youth`, `adolescent`, `adolescents` → route to the child SHS estimate engine.

## Files changed

- `src/ask_router.py`
- `src/matchers.py`

## QC

Run:

```bash
python tests/run_phase6c_qc.py
```

Expected:

```text
Phase 6C teen/adolescent routing QC: 6 / 6 passed
```
