# Phase 7 Interactive GPT-Style Layer

This patch combines Phase 7A and Phase 7B into one integrated interactive layer.

## What this adds

### Phase 7A: Follow-up interaction
The app now keeps a local session-level `conversation_id` and remembers the last successful estimate context:

- population
- topic/outcome
- year(s)
- grouping label
- subgroup
- resolved question

This allows follow-ups like:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
What about kids?
Explain the confidence interval.
Where do I get the data?
```

The deterministic DHIS estimate engine is still the authority. Follow-ups are resolved into a complete question and then routed back through the existing estimate/FAQ tools.

### Phase 7B: Optional OpenAI structured follow-up planning
When OpenAI is configured and requested, the model can help convert a follow-up into a small structured plan, such as:

```json
{
  "population": "adults",
  "year_phrase": "last 2 years",
  "grouping": "SVI",
  "subgroup": null
}
```

The backend validates this plan and still calls the deterministic tools. The model does **not** calculate estimates, invent unavailable data, override suppression rules, or create citations.

If no `OPENAI_API_KEY` is set, everything still works with deterministic follow-up resolution.

## Files added/updated

```text
api_server.py
src/ask_router.py
src/conversation_state.py
src/followup_resolver.py
src/model_orchestrator.py
tests/run_phase7_qc.py
README_PHASE7_INTERACTIVE_GPT.md
```

## Run

```bash
python api_server.py
```

Open:

```text
http://127.0.0.1:8018
```

## Optional OpenAI setup

```cmd
set OPENAI_API_KEY=your_api_key_here
set OPENAI_MODEL=gpt-4.1-mini
python api_server.py
```

Then check the UI box for OpenAI polishing/structured routing.

## QC

Run:

```bash
python tests/run_phase7_qc.py
```

Expected:

```text
Phase 7 interactive QC: 13 / 13 passed
```

For the broader QC suite, continue running:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
python tests/run_phase5_qc.py
python tests/run_phase6_qc.py
python tests/run_phase6c_qc.py
python tests/run_phase7_qc.py
```

## Manual smoke test sequence

Run these in the browser as a sequence in the same session:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
What about kids?
Explain the confidence interval.
Where do I get the data?
```

Expected behavior:

- The first question returns the adult diabetes estimate.
- `What about by SVI?` uses the prior topic/year/population and changes only the grouping.
- `Show last 2 years.` uses the prior topic/population/grouping and changes only the year window.
- `What about kids?` reuses the prior topic/year concept but routes to child SHS if available, otherwise safely falls back.
- `Explain the confidence interval.` gives a general CI explanation and does not retrieve a new estimate.
- `Where do I get the data?` points to NHIS documentation/DQT links.

## Guardrails

- Estimates still come only from the local DHIS NHIS Adult/Child SHS files.
- Teen-specific questions still redirect to the NHIS Teen SHS tool.
- Youth/adolescent/adolescents route to the child SHS file.
- The model may help interpret a follow-up only when enabled and configured.
- The model may not generate estimates or sources.

## Lockdown note

After this phase, remaining work should be demo hardening only. Recommended future enhancements should be documented but not implemented before the demo unless absolutely necessary.
