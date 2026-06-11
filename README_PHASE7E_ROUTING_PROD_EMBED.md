# Phase 7E: Teen participation routing + draft production/embed UIs

## What changed

### Teen routing
Teen/teenager wording is now split by intent:

- **Teen estimate questions** still redirect to the NHIS Teen Summary Health Statistics tool.
  - Example: `What percent of teens had asthma last year?`
- **Teen participation, privacy, benefit, legitimacy, or what-to-expect questions** now route to the participation/FAQ/resource retriever.
  - Example: `Why should teens participate in NHIS?`
  - Example: `Is my teen's information private and secure?`

This prevents the teen-estimate exception from hijacking participation/resource questions.

### UI routes
The same server now exposes three UI entry points:

- `/` or `/prod` — draft production-style UI, cleaner and without debug/feedback panels.
- `/embed` or `/iframe` — compact iframe-friendly UI for embedding in a dev page.
- `/debug` — full debug/reviewer UI with feedback buttons and raw matched-source details.

The API routes are unchanged:

- `POST /api/ask`
- `GET /api/feedback`
- `GET /api/feedback/export`
- `GET /api/health`
- `GET /api/openai/status`

## Suggested iframe snippet

Replace the host/port if deployed somewhere besides localhost.

```html
<iframe
  src="http://127.0.0.1:8018/embed"
  title="NHIS Assistant"
  style="width:100%; max-width:820px; height:620px; border:0;"
></iframe>
```

## QC

Run:

```bash
python tests/run_phase7e_qc.py
```

Expected:

```text
Phase 7E router/UI QC: 8 / 8 passed
```

This QC verifies:

- `Why should teens participate in NHIS?` routes to FAQ/resources, not teen redirect.
- `What percent of teens had asthma last year?` still redirects to the teen SHS tool.
- kid/adult participation questions route to FAQ/resources.
- teen privacy routes to FAQ/resources.
- diabetes impact/benefit questions route to resources, not estimate retrieval.
- production, embed, and debug UI constants are present.

## Manual browser smoke tests

Start the server:

```bash
python api_server.py
```

Open:

```text
http://127.0.0.1:8018/
http://127.0.0.1:8018/embed
http://127.0.0.1:8018/debug
```

Test these prompts:

```text
Why should teens participate in NHIS?
What percent of teens had asthma last year?
Is my teen's information private and secure?
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
Why should adults participate in NHIS?
How has NHIS data helped with diabetes?
```
