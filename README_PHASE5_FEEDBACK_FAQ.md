# Phase 5: Feedback Logging + FAQ Index Workflow

This package keeps the deterministic DHIS/NHIS estimate engine as the source of truth and adds two demo-ready upgrades:

1. **UI feedback logging** so reviewer clicks are saved to `data/feedback/feedback_log.csv`.
2. **A controlled FAQ indexing workflow** for approved CDC/NCHS NHIS pages.

Respondent conversion/support tools are not included in this phase.

## Run the app

```bash
cd dhis_nhis_chatbot
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018
```

## Feedback buttons

After asking a question, click one of the feedback labels such as:

- Good answer
- Wrong topic
- Wrong subgroup
- Bad year
- Missing source
- Bad wording
- Needs review

The app saves one row to:

```text
data/feedback/feedback_log.csv
```

It also writes JSONL backup rows to:

```text
data/feedback/feedback_log.jsonl
```

The saved feedback row includes:

```text
timestamp
question
answer
feedback label
reviewer note
status/mode
matched population/topic/grouping/subgroup/year when available
source URL
raw debug JSON
```

Export the CSV from the UI using the **Export feedback CSV** link, or open:

```text
http://127.0.0.1:8018/api/feedback/export
```

## FAQ indexing workflow

The FAQ retriever uses a local approved CDC/NCHS NHIS index at:

```text
data/faq_index/faq_index_seed.json
```

The approved URL allowlist is here:

```text
config/faq_sources.json
```

To refresh the index in an internet-enabled environment:

```bash
python scripts/build_faq_index.py
```

The script only fetches URLs listed in `config/faq_sources.json`. It writes a refresh report to:

```text
tests/qc_reports/faq_index_build_report.csv
```

If internet access is unavailable or all fetches fail, the script leaves the existing FAQ index in place.

## API endpoints

```text
GET  /api/health
GET  /api/sources
GET  /api/ask?q=...
POST /api/ask {"question":"...", "debug":true, "use_model":false}
GET  /api/estimate?q=...
GET  /api/faq?q=...
POST /api/feedback {...}
GET  /api/feedback
GET  /api/feedback/export
```

## QC

Run:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
python tests/run_phase5_qc.py
```

Phase 5 QC verifies that:

- `/api/ask`-equivalent routing still returns an estimate answer.
- FAQ retrieval returns either a sourced answer or safe not-found response.
- Feedback rows are saved to CSV and JSONL.

## Guardrails

- Estimates still come from the deterministic adult/child DHIS SHS files.
- Special display codes are handled before numeric formatting.
- FAQ answers are limited to the local approved CDC/NCHS source index.
- OpenAI/model polishing remains optional and off by default.
- Feedback logging does not send data anywhere external; it writes local files only.
