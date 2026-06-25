# NHIS Assistant V2C Conversational Orchestrator

This build adds the next conversational layer on top of the V2A/B local test build.

## What changed

### 1. Conversation lanes / lane switching

The assistant now treats each turn as belonging to a conversation lane:

- `estimate` — deterministic adult/child SHS estimate lookup
- `faq` / resource — approved NHIS FAQ, participant, privacy, impact, and resource answers
- `teen_redirect` — teen estimate requests redirect to the Teen SHS tool until teen SHS data are added
- `explanation` / documentation follow-up — CI/source/file explanation turns
- fallback/not found — safe response when no approved source or estimate matches

The key change is that explicit new questions now override prior context. Vague prompts like `tell me more` inherit prior context, but explicit new estimate or FAQ questions switch lanes.

Examples:

```text
Why should I participate in NHIS?
tell me more
What percent of teens had asthma last year?
What percent of adults had diabetes last year?
Why should I participate in NHIS?
```

Expected behavior:

- `tell me more` after a resource answer stays in the resource lane.
- teen estimate questions switch to the teen redirect lane.
- adult/child estimate questions switch to the deterministic SHS estimate lane.
- FAQ/resource questions switch back to the resource lane.

### 2. Dynamic FAQ/resource answer composition

FAQ/resource answers are no longer treated as purely canned responses. Without OpenAI, repeated FAQ/resource questions get a deterministic alternate framing so the response does not look like the exact same copy/paste answer.

With OpenAI configured and requested, FAQ/resource answers can be conversationally composed from the approved retrieved evidence.

Guardrails:

- The model may only use retrieved approved source evidence.
- It must not invent facts, URLs, estimates, percentages, or policy claims.
- It should not repeat the same answer verbatim if the user circles back.
- Estimates still come from the deterministic SHS data files.

### 3. Insurance topic/status deconfliction

Insurance is both a topic and a grouping/covariate in the adult and child SHS files. This build adds a special rule for questions like:

```text
How many people had insurance by insurance status?
What percent of children had insurance by insurance status?
```

Those now route to an insurance special-case estimate response instead of falling into `not_found`.

Questions where another health condition is clearly the topic still work normally:

```text
What percent of adults had asthma by insurance status?
```

That stays in the normal SHS estimate lane with insurance as the grouping/covariate.

## Run locally

```bash
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018/
http://127.0.0.1:8018/embed
http://127.0.0.1:8018/debug
```

## Run QC

```bash
python tests/run_v2c_qc.py
python tests/run_v2ab_qc.py
python tests/run_phase7e_qc.py
```

The included testing matrix is here:

```text
tests/v2c_testing_matrix.csv
```

QC reports are saved here:

```text
tests/qc_reports/v2c_qc_output.txt
tests/qc_reports/v2ab_after_v2c_qc_output.txt
tests/qc_reports/phase7e_after_v2c_qc_output.txt
```

## Important production note

This is still a prototype. It is much closer to a true conversational assistant, but production use should still require:

- formal approved-source indexing workflow review
- broader routing QC
- persistent feedback logging
- security/privacy review
- decision on whether OpenAI-based resource answer composition is allowed
- teen/3-year/detail SHS module expansion after file review
