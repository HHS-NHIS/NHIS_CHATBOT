# NHIS Chatbot Keyword Mapping + QC Workflow

Use this README when editing `data/keyword_mappings2.json` and rerunning QC.

## What you can safely edit in `keyword_mappings2.json`

For most wording tweaks, you can edit the JSON without changing Python code, as long as you keep the structure intact.

Safe edits usually include:

```text
user_keywords
user_regex
confidence
notes / metadata fields
```

Examples of safe keyword additions:

```json
"user_keywords": [
  "Current asthma in adults",
  "current asthma",
  "asthma",
  "currently has asthma",
  "still has asthma"
]
```

For income/FPL wording, keep all common user terms routed to the same user-facing Family income grouping:

```json
"user_keywords": [
  "family income",
  "household income",
  "income",
  "income group",
  "income level",
  "poverty",
  "poverty status",
  "FPL",
  "federal poverty level",
  "below poverty"
]
```

## Fields to be careful with

Do **not** casually change these unless you also verify the exact values exist in the adult/child SHS CSV files:

```text
cdc_topics
cdc_groups
cdc_subgroups
population
canonical labels
mapping IDs / keys
```

Those fields are used to retrieve actual rows. If you rename a `cdc_topic`, `cdc_group`, or `cdc_subgroup` to something that does not exist in the CSV, the chatbot may recognize the user keyword but fail to return data.

## Avoid overly broad keywords

Broad keywords can create false matches and overlap problems. Avoid adding words like these by themselves unless they are part of a carefully tested rule:

```text
care
doctor
health
insurance
income
kids
adult
race
school
pain
mental
```

Prefer more specific phrases:

```text
usual place of care
saw a doctor
health insurance coverage
household income
race and ethnicity
missed school due to illness
chronic pain
mental health counseling
```

## Deconfliction rules that may require code changes

Some concepts are not just keywords; they are routing/deconfliction rules. Changes to these may require edits in `src/matchers.py`, `src/retrieve_estimate.py`, or `src/ask_router.py`.

Examples:

```text
teen / teenager → redirect to Teen SHS tool
youth / adolescent / adolescents → child SHS file
income / poverty / FPL → Family income grouping
insurance under 65 vs insurance 65+
race vs race and Hispanic origin
sex vs sexual orientation
metro/MSA vs place of residence
current asthma vs ever asthma vs asthma attack
anxiety feelings vs anxiety medication
depression feelings vs depression medication
```

## Recommended edit workflow

1. Back up the existing mapping file:

```text
data/keyword_mappings2_BACKUP_YYYYMMDD.json
```

2. Edit:

```text
data/keyword_mappings2.json
```

3. Restart the server after saving:

```bash
Ctrl + C
python api_server.py
```

4. Run the QC scripts from the project root:

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
python tests/run_phase4_qc.py
python tests/run_phase5_qc.py
python tests/run_phase6_qc.py
python tests/run_phase6c_qc.py
```

Or run everything at once if you use the included helper:

```bash
python tests/run_all_qc.py
```

5. Manually test the specific phrases you changed in the UI.

6. If a match is wrong, use the feedback buttons and export:

```text
http://127.0.0.1:8018/api/feedback/export
```

## QC scripts included in this kit

Place these under `dhis_nhis_chatbot/tests/`:

```text
run_qc.py
run_phase3_qc.py
run_phase4_qc.py
run_phase5_qc.py
run_phase6_qc.py
run_phase6c_qc.py
audit_grouping_and_overlap.py
run_all_qc.py
```

### What each script covers

| Script | Purpose |
|---|---|
| `run_qc.py` | Core deterministic estimate QC. |
| `run_phase3_qc.py` | API/FAQ routing QC. |
| `run_phase4_qc.py` | Widget/FAQ behavior QC. |
| `run_phase5_qc.py` | Feedback API/logging QC. |
| `run_phase6_qc.py` | Optional OpenAI polishing layer QC. Works without API key. |
| `run_phase6c_qc.py` | Teen redirect vs youth/adolescent child-routing QC. |
| `audit_grouping_and_overlap.py` | Broader grouping/overlap audit helper. |
| `run_all_qc.py` | Convenience runner for the phase QC scripts. |

## Manual smoke-test prompts after keyword edits

Use these after any mapping change:

```text
What percent of adults had current asthma last year?
What percent of kids got a flu shot last year?
How many people had diabetes in the last 2 years?
What percent of children ever had asthma last year?
What percent of adults had an asthma attack last year?
How many adults took anxiety medication last year?
How many adults regularly felt depressed last year?
What percent of adults had diabetes last year by SVI?
What percent of adults got a flu shot last year by insurance for seniors?
What percent of adults got a flu shot last year by insurance for people under 65?
What percent of adults got a flu shot last year by family income?
What percent of adults got a flu shot last year by poverty?
What percent of adults got a flu shot last year by FPL?
What percent of uninsured adults got a flu shot last year?
What percent of adults were uninsured last year?
What percent of gay men had current asthma last year?
What percent of men had current asthma last year?
What percent of teens had current asthma last year?
What percent of adolescents got a flu shot last year?
What is NHIS?
Where can I find the 2024 NHIS public use files?
What percent of adults had migraines last year by SVI?
```

## Expected teen/youth behavior

```text
teen / teens / teenager / teenagers → Teen SHS redirect
adolescent / adolescents / youth → child SHS routing
```

## Bottom line

Use the JSON file for normal synonym tuning. Use Python code changes only for routing/deconfliction logic. After every edit, restart the server, run QC, and manually test the phrases you changed.
