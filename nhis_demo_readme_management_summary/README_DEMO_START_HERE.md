# DHIS/NHIS Assistant Demo — Start Here

## What this tool is

This is a prototype NHIS assistant that combines:

1. **Deterministic estimate retrieval** from the current DHIS NHIS Adult and Child Summary Health Statistics CSV files.
2. **CDC/NHIS FAQ and participation-resource retrieval** from a controlled local index.
3. **Optional OpenAI/GPT-style polishing and follow-up handling**, while keeping estimates, confidence intervals, special codes, citations, and source routing controlled by the local application logic.

The purpose is to demonstrate a widget-style assistant that can answer common NHIS estimate questions, point users to the right source when estimates are unavailable, and provide brief, source-grounded NHIS information.

## What this tool is not

This is not a final production system. It is a working demo/prototype. It does **not** calculate new estimates from PUF microdata. It does **not** integrate Teen SHS estimates yet. It does **not** replace the NHIS Data Query Tools. It is intended to show how a conversational interface could sit on top of approved NHIS data and documentation resources.

## Core rules

- Adult/child estimates come only from the DHIS NHIS SHS CSV files.
- Teen estimate questions are redirected to the NHIS Teen SHS tool.
- Participation, privacy, benefit, and “why participate” questions route to the local approved resource index.
- The model/OpenAI layer, when enabled, is only for wording/follow-up assistance. It should not create or alter estimates.
- If the tool cannot find an estimate, it should clearly say so and point users to the official NHIS documentation or relevant DQT page.

## Main URLs after starting the server

Start the app from the project root:

```bash
python api_server.py
```

Then open:

```text
http://127.0.0.1:8018/
```

Available UI routes:

```text
/       Draft production-style UI, no raw debug panel
/embed  Compact iframe-friendly UI for a dev/demo page
/debug  Reviewer/debug UI with matched-source details and feedback controls
```

Useful API routes:

```text
/api/ask
/api/estimate
/api/faq
/api/health
/api/openai/status
/api/feedback
/api/feedback/export
```

## OpenAI/API use

The app works without an OpenAI key. If an OpenAI key is configured, the app can polish the answer and help with structured follow-up interpretation. The deterministic estimate engine remains the source of truth.

Typical Windows command prompt setup:

```cmd
set OPENAI_API_KEY=your_api_key_here
set OPENAI_MODEL=gpt-4.1-mini
python api_server.py
```

Then check:

```text
http://127.0.0.1:8018/api/openai/status
```

## Embedding in a dev page

Use the `/embed` route in an iframe:

```html
<iframe
  src="http://127.0.0.1:8018/embed"
  title="NHIS Assistant"
  style="width:100%; max-width:820px; height:620px; border:0;"
></iframe>
```

For a real dev server, replace the localhost URL with the dev-server URL/path.

## Quick smoke tests

Test estimates:

```text
What percent of adults had current asthma last year?
What percent of kids got a flu shot last year?
How many people had diabetes in the last 2 years?
What percent of adults had diabetes last year by SVI?
What percent of adults got a flu shot last year by income?
What percent of adults got a flu shot last year by FPL?
What percent of gay men had current asthma last year?
```

Test follow-up behavior in the same browser session:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
What about kids?
Explain the confidence interval.
Where do I get the data?
```

Test teen routing:

```text
What percent of teens had asthma last year?
Why should teens participate in NHIS?
```

Expected behavior:

- Teen estimate question redirects to the NHIS Teen SHS tool.
- Teen participation question routes to the participation/resource answer, not the teen-estimate redirect.

Test FAQ/resource retrieval:

```text
What is NHIS?
Who is included in NHIS?
Where can I find the 2024 NHIS public use files?
Why should I participate in NHIS?
Is my information private and secure?
How does NHIS data help real people?
How has NHIS data helped with diabetes?
```

Test fallback:

```text
What percent of adults had migraines last year by SVI?
What percent of kids had diabetes last year by sexual orientation?
```

Expected behavior: no hallucinated estimates; approved fallback/resource guidance.

## QC scripts

Run from the project root:

```bash
python tests/run_all_qc.py
```

Or individual checks:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
python tests/run_phase5_qc.py
python tests/run_phase6_qc.py
python tests/run_phase6c_qc.py
python tests/run_phase7_qc.py
python tests/run_phase7d_qc.py
python tests/run_phase7e_qc.py
```

## Feedback logging

In `/debug`, click feedback buttons after testing a question. Feedback is saved to:

```text
data/feedback/feedback_log.csv
```

Export through:

```text
http://127.0.0.1:8018/api/feedback/export
```

Use this CSV to track wrong matches, missing sources, wording problems, and review notes.

## Keyword mapping edits

Most synonym tweaks can be made safely in:

```text
data/keyword_mappings2.json
```

Safe edits:

```text
user_keywords
user_regex
notes/metadata fields
```

Be careful changing:

```text
cdc_topics
cdc_groups
cdc_subgroups
population
canonical labels
mapping IDs/keys
```

Those need to match the adult/child SHS CSV labels. After any mapping edit, restart the server and rerun QC.

## Known limitations

- Estimates are limited to the adult and child SHS files currently loaded.
- Teen estimates are not integrated; teen estimate questions redirect to the NHIS Teen SHS tool.
- The participation/resource index is local and controlled, not a full production search service.
- The OpenAI layer is optional and should not be treated as the source of estimates.
- Live Socrata refresh, authentication, and production deployment hardening are future enhancements.

## Recommended production enhancements

1. Formalize the approved source inventory and refresh schedule.
2. Add controlled live Socrata refresh with validation checks.
3. Add a production-grade retrieval index for NHIS documentation and participant pages.
4. Add structured logs and dashboard-style review of feedback/errors.
5. Add formal accessibility and 508 review for the UI.
6. Add governance review of OpenAI/API use, data flow, logging, and source controls.
7. Add Teen SHS integration only after adult/child SHS routing is fully stable.

