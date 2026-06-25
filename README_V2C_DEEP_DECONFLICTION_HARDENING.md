# NHIS Assistant V2C Deep Deconfliction Hardening

This build is a regression-hardening update focused on special cases, overlap terms, and routing deconfliction before senior-management review.

## Main fixes

### 1. Insurance topic vs. insurance covariate
Insurance can be both a substantive outcome/topic and a grouping/covariate in the adult and child SHS files. This build expands the insurance special-case handler so the app does not confuse:

- insurance as the topic: "How many people had insurance?", "What percent were uninsured?"
- insurance as a grouping: "asthma by insurance status"
- insurance as both topic and requested breakout: "insurance by insurance status"
- age-scoped insurance questions: "adults under 65 had private insurance", "adults 65 and older had private insurance"

For non-insurance outcomes by insurance status, the standard estimate path is preserved.

### 2. Mental-health care due to cost
A strong deconfliction phrase now routes cost-related mental health care questions to:

`Did not get needed mental health care due to cost`

instead of the generic counseling/mental-health-professional outcome.

### 3. Generic difficulty questions
Generic child/adult difficulty questions now route to:

`Difficulty status (composite)`

unless a specific adult difficulty outcome is named, such as seeing, hearing, walking, communicating, remembering, or self care.

### 4. Multi-group/crosstab transparency
When a user asks for a combination that is not available as a crosstab, such as:

`What percent of men had current asthma by sexual orientation last year?`

The app now explains that the exact crosstab is not available and returns the closest available grouping instead of silently dropping the subgroup.

## New QC files

- `tests/run_deep_deconfliction_qc.py`
- `tests/deep_deconfliction_testing_matrix.csv`
- `tests/deep_deconfliction_qc_report.csv`

## QC results

The following passed in this hardened build:

- Deep deconfliction QC: 60 / 60 passed
- V2C conversational orchestrator QC: 20 / 20 passed
- V2A/B QC: 14 / 14 passed
- Phase 7E router/UI QC: 8 / 8 passed

## Run locally

```bash
cd nhis_chatbot_final_railway
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018/
http://127.0.0.1:8018/debug
```

Run QC:

```bash
python tests/run_deep_deconfliction_qc.py
python tests/run_v2c_qc.py
python tests/run_v2ab_qc.py
python tests/run_phase7e_qc.py
```

## High-value manual test prompts

```text
How many people had insurance by insurance status?
What percent of adults had insurance last year by insurance for people under 65?
What percent of adults under 65 had private insurance last year?
What percent of adults 65 and older had private insurance last year?
What percent of adults had asthma by insurance status last year?
What percent of uninsured kids got a flu shot last year?
What percent of adults needed mental health care but did not get it due to cost last year?
What percent of children had difficulty last year?
What percent of men had current asthma by sexual orientation last year?
Why should I participate in NHIS?
tell me more
What percent of teens had asthma last year?
```
