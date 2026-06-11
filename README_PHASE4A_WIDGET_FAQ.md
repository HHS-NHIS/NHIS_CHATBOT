# DHIS/NHIS Chatbot Prototype — Phase 4A

Phase 4A keeps the deterministic DHIS NHIS estimate engine as the source of truth and improves the demo wrapper around it.

## What changed

- Polished local widget-style UI in `api_server.py`
- Source cards for estimate and FAQ answers
- `Why this answer?` panel for routing/matching explanations
- Debug drawer for matched source details/raw JSON
- Feedback labels for manual testing notes
- Improved FAQ retriever with source cards, best excerpts, and more conservative source handling
- Approved-source FAQ index builder: `scripts/build_faq_index.py`
- Phase 4 QC test file and report

## Run locally

```bash
cd dhis_nhis_chatbot
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018
```

## API endpoints

```text
POST /api/ask
GET  /api/ask?q=...
GET  /api/estimate?q=...
GET  /api/faq?q=...
GET  /api/sources
GET  /api/health
```

## Refresh the FAQ index

The local FAQ index is intentionally built only from the CDC/NCHS NHIS allowlist in:

```text
config/faq_sources.json
```

To refresh in an internet-enabled environment:

```bash
python scripts/build_faq_index.py
```

Outputs:

```text
data/faq_index/faq_index_seed.json
tests/qc_reports/faq_index_build_report.csv
```

If internet access is unavailable, the script leaves the existing index in place and writes a failure report.

## QC

Run:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
```

Current package QC:

```text
Existing estimate QC: 14 / 14 passed
Phase 3 API/FAQ QC: 7 / 7 passed
Phase 4A widget/FAQ QC: 8 / 8 passed
```

## Guardrails

- Estimates come only from the local DHIS NHIS Adult/Child Summary Health Statistics files.
- FAQ answers come only from the local approved CDC/NCHS NHIS source index.
- If an estimate/source is not found, the assistant should say so rather than inventing an answer.
- OpenAI/model polishing remains optional and off by default in this package.
