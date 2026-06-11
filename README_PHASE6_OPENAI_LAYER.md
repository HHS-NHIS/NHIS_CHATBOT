# Phase 6 — Optional OpenAI Layer

This phase adds an **optional OpenAI answer-polishing layer** on top of the deterministic DHIS/NHIS estimate engine and local NHIS FAQ retriever.

## What the OpenAI layer is allowed to do

The model may:

- Rewrite deterministic estimate output into a more natural GPT-style answer.
- Summarize retrieved NHIS FAQ/source excerpts.
- Preserve citations/source links already returned by the app.
- Explain routing choices already present in the tool output, such as latest year or closest available grouping.

The model may **not**:

- Calculate estimates.
- Add estimates, CIs, SEs, years, or facts not returned by the deterministic engine/FAQ retriever.
- Override suppression/special-code rules.
- Invent sources or citations.
- Convert a fallback/not-found result into a substantive answer.

## New/updated files

```text
api_server.py
src/ask_router.py
src/model_orchestrator.py
tests/run_phase6_qc.py
README_PHASE6_OPENAI_LAYER.md
```

## API endpoints

```text
GET  /api/openai/status
POST /api/ask {"question":"...", "debug":true, "use_model":true}
GET  /api/ask?q=...&debug=1&use_model=1
```

The existing endpoints remain available:

```text
/api/estimate
/api/faq
/api/feedback
/api/feedback/export
/api/sources
/api/health
```

## How to run without OpenAI

No setup needed. The app behaves deterministically exactly like Phase 5.

```bash
python api_server.py
```

If the UI checkbox is selected but `OPENAI_API_KEY` is not set, the app safely returns the deterministic answer and records model metadata explaining that no key was configured.

## How to enable OpenAI polishing

Set these environment variables before starting the server.

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_MODEL="gpt-4.1-mini"
python api_server.py
```

### Windows cmd

```cmd
set OPENAI_API_KEY=your_api_key_here
set OPENAI_MODEL=gpt-4.1-mini
python api_server.py
```

### Optional always-on mode

You can make model polishing default to on for every request:

```cmd
set USE_OPENAI=1
```

For demo safety, the UI checkbox is usually better than always-on mode.

## Test the OpenAI layer status

Open:

```text
http://127.0.0.1:8018/api/openai/status
```

Without a key, you should see `effective_enabled: false`.

With a key and `use_model=1`, you should see `effective_enabled: true`.

## Recommended smoke tests

Run the deterministic QC first:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
python tests/run_phase5_qc.py
python tests/run_phase6_qc.py
```

Then test these in the UI with OpenAI polishing OFF and ON:

```text
What percent of adults had current asthma last year?
What percent of kids got a flu shot last year?
What percent of adults had diabetes last year by SVI?
What percent of adults got a flu shot last year by insurance for seniors?
What percent of gay men had current asthma last year?
What is NHIS?
Where can I find the 2024 NHIS public use files?
What percent of adults had migraines last year by SVI?
```

Expected behavior:

- With OpenAI OFF: deterministic answer.
- With OpenAI ON: same facts/numbers/sources, smoother wording.
- Any missing estimate should still use fallback language.
- Debug JSON should include a `model` block showing whether the model was used or whether the app fell back to deterministic output.

## Production/demo reminder

Do not put an API key in browser JavaScript. The key belongs only in the backend environment. The browser calls your `/api/ask` endpoint; the backend calls OpenAI.
