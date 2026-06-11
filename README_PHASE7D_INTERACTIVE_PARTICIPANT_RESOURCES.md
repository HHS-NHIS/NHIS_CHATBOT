# Phase 7D — Interactive UI follow-ups + participant resource retrieval

This patch fixes two things:

1. **Follow-up UI wiring**: the browser now stores and resends `conversation_id` using `localStorage`, displays a small turn history, and shows suggested follow-up chips. Use **Clear / reset conversation** to start over.
2. **Participant/participation resource retrieval**: the FAQ source index now includes uploaded participant-oriented resources and official NHIS participant links, in addition to the existing NHIS FAQ/DQT/documentation sources.

## Files to replace/add

```text
api_server.py
src/ask_router.py
src/faq_retriever.py
data/faq_index/faq_index_seed.json
tests/run_phase7d_qc.py
README_PHASE7D_INTERACTIVE_PARTICIPANT_RESOURCES.md
```

## How to verify you are running this version

Start the server:

```bash
python api_server.py
```

The terminal should say:

```text
Serving DHIS/NHIS Phase 7D interactive API + participant resources at http://127.0.0.1:8018
```

Then hard-refresh the browser:

```text
Ctrl + F5
```

Cookies are not the main issue. The important part is that the browser is running the updated `api_server.py` HTML/JavaScript and that the same `conversation_id` is sent with each `/api/ask` request.

## Follow-up smoke test

Ask this sequence in the same browser page:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
What about kids?
Explain the confidence interval.
Where do I get the data?
```

Expected behavior:

- The page should show a conversation ID pill.
- Follow-up answers should show a `resolved follow-up` pill when the prompt was interpreted using prior context.
- The previous turns should appear in the turn history.
- Suggested follow-up chips should appear after successful estimate answers.

## Participant resource queries to test

```text
Why should I participate in NHIS?
What's in it for me if I participate in NHIS?
Is my information private and secure?
What should I expect if I was selected for NHIS?
How does NHIS data help real people?
How has NHIS data helped with diabetes?
```

Expected behavior:

- These should route to FAQ/resource retrieval, not the estimate engine.
- Privacy questions should prioritize the official NHIS participant privacy link.
- Benefit/impact questions should use the uploaded impact/job-aid resources.
- Diabetes benefit questions should **not** return diabetes prevalence estimates unless the user explicitly asks for an estimate.

## QC

Run:

```bash
python tests/run_phase7d_qc.py
```

Expected:

```text
Phase 7D interactive UI/participant resource QC: 9 / 9 passed
```

Also rerun the standing suite after replacing files:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
python tests/run_phase5_qc.py
python tests/run_phase6_qc.py
python tests/run_phase6c_qc.py
python tests/run_phase7_qc.py
python tests/run_phase7d_qc.py
```

## Guardrail

The uploaded participation resources are indexed as source material for FAQ-style answers. This patch does not add a separate respondent-conversion module and does not let the model invent respondent-facing claims. If no source is retrieved, the assistant should say it does not have enough sourced information.
