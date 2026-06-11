# DHIS/NHIS FAQ + Estimate Prototype — Phase 2

This is a local, deterministic prototype for a DHIS/NHIS-specific FAQ and estimate chatbot/widget. It uses the uploaded DHIS NHIS Adult and Child Summary Health Statistics CSV snapshots as the authoritative estimate sources. It does **not** invent estimates.

## Authoritative estimate sources

- Adult: `data/NHIS_adult_SHS.csv`, Socrata ID `25m4-6qqq`
- Child: `data/NHIS_child_SHS.csv`, Socrata ID `wxz7-ekz9`
- Keyword/topic mapping: `data/keyword_mappings2.json`

The source files include outcome labels, grouping labels, group values, percentages, confidence intervals, source titles/descriptions, and reliability/special-code fields.

## What changed in Phase 2

Phase 2 adds the robustness rules requested for the CDC/NHIS demo:

- If no year is provided, the bot returns **all years available** in the current DHIS file and explains why.
- If the user asks for “last year,” “latest,” or “most recent,” the bot uses the **latest year available** in the current file.
- If a generic topic is requested without a group/subgroup, the bot returns the **overall/total population estimate**.
- If a subgroup is requested, such as “male,” the bot lists that subgroup first and then shows the rest of that grouping for context.
- If multiple grouping dimensions are requested, the bot uses a composite/crosstab grouping when available; otherwise it explains that the exact multi-group crosstab was not available and returns the first available matching grouping.
- The bot reports highest and lowest estimates among the returned numeric rows.
- The bot includes confidence intervals when available and SEs if a future source file includes an SE field.
- If SE is requested but the current file has no SE column, the bot says so and shows CIs where available.
- The bot includes a source title/description excerpt from the DHIS file when available.
- If an estimate is found, the bot links to the NHIS Interactive Data Query Systems page for more information.
- If an estimate is not found, the bot uses the approved fallback language and provides relevant CDC/NHIS links.

## Special display codes

The values below are treated as display symbols, never numeric percentages:

| Percentage value | Display | Footnote |
|---:|---|---|
| `999` | `*` | Estimate does not meet NCHS standards of reliability |
| `444` | `**` | While the estimate meets NCHS standards of reliability, its complement does not |
| `555` | `***` | Topic is limited to adults aged 18–64 |
| `777` | `NA` | Rotating content, indicator not available for time period |
| `888` | `–` | Quantity zero |

When one of these values is present, the confidence interval field is expected to be blank.

## Run locally

```bash
cd dhis_nhis_chatbot
python -m pip install -r requirements.txt
python chatbot_cli.py "What percent of adults had current asthma?" --debug
python tests/run_qc.py
python server.py
```

Open the local UI:

```text
http://127.0.0.1:8018
```

Example API call:

```text
http://127.0.0.1:8018/answer?q=What%20percent%20of%20adults%20had%20current%20asthma%3F&debug=1
```

## QC

The QC suite is in `tests/demo_questions.csv`. Run:

```bash
python tests/run_qc.py
```

The latest bundled QC run passed all included checks:

```text
QC complete. Passed: 12 / 12
```

## Current limitations

- This version uses uploaded CSV snapshots only. Live Socrata refresh is not yet enabled.
- General NHIS FAQ retrieval/RAG from CDC pages is not yet fully implemented. Documentation/PUF questions return official NHIS documentation links.
- The current adult/child files include confidence intervals but do not include standard errors as separate fields. The formatter will display SEs automatically if a future file includes an SE/standard error column.
- The answer style is intentionally brief and deterministic; a future LLM wrapper should be restricted to wording only after the retrieval layer returns sourced records.

## Batch debug CSV for testing prompts

Use `batch_cli.py` when you want to send a list of prompts and get back a debug CSV that can be reviewed or sent back for fixes.

Input file format: a CSV with a `question` column. A template is included at:

```bash
tests/batch_questions_template.csv
```

Run:

```bash
python batch_cli.py tests/batch_questions_template.csv --output tests/batch_debug_output.csv
```

The output CSV includes:

- original question
- status
- answer
- debug answer text
- parsed population
- parsed years and year mode
- matched outcome
- matched grouping label and subgroup value
- topic match method/score/keyword
- requested group keys/values
- grouping explanation
- raw debug JSON

Send back `tests/batch_debug_output.csv` when something is wrong.
