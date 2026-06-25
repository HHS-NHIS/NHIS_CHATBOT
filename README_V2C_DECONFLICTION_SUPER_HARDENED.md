# V2C Super-Hardened Deconfliction Update

This build adds a deeper deconfliction/regression pass for senior-management demo use. It does **not** make the assistant perfect, and it cannot guarantee every future natural-language phrasing, but it substantially expands the tested special-case coverage for the known high-risk NHIS SHS routing conflicts.

## Additional fixes in this build

### Difficulty/functioning as topic vs subgroup
Fixed a routing error where questions such as:

```text
What percent of children with functioning difficulty had asthma last year?
```

were being routed to the `Difficulty status (composite)` outcome instead of `Current asthma by Difficulty Status`. Difficulty/functioning words now become the topic only when no other clear SHS health topic is present.

### Missed workdays phrasing
Fixed natural-language variants such as:

```text
What percent of adults missed six or more workdays last year?
```

so they map to:

```text
Six or more workdays missed due to illness, injury, or disability
```

### Estimate-lane signal expansion
Expanded estimate-lane detection for additional SHS terms that could otherwise fall to FAQ/resource fallback, including disability, difficulty, workdays, missed school, special education, learning disability, foreign-born, veteran, SVI, and social vulnerability.

## Deconfliction coverage now tested

The build includes these QC layers:

```text
tests/run_expanded_deconfliction_qc.py    68 / 68 passed
tests/run_deep_deconfliction_qc.py        60 / 60 passed
tests/run_v2c_qc.py                       20 / 20 passed
tests/run_v2ab_qc.py                      14 / 14 passed
tests/run_phase7e_qc.py                    8 / 8 passed
```

Combined, the targeted router/deconfliction tests cover 170 pass checks.

## High-risk categories covered

- Insurance as topic vs insurance as grouping/covariate
- Adult under-65 and 65+ insurance wording
- Child insurance/uninsured wording
- Income / household income / family income / poverty / FPL equivalence
- Asthma current vs ever vs episode/attack
- Anxiety/depression feelings vs medication outcomes
- Mental-health care due to cost vs mental-health services/counseling
- Delayed care vs unmet care vs skipped medication due to cost
- Difficulty/disability as topic vs subgroup
- Difficulty/functioning subgroup with another health topic
- Sex vs sexual orientation and unavailable multi-way crosstab wording
- Race vs Hispanic origin/race
- Region vs MSA/urbanicity/place wording
- Nativity, veteran, employment, and workdays wording
- Adult education vs child parental education vs child special education topic
- Family income vs family structure vs marital status
- Care setting topics vs place/geography grouping words
- Skin cancer vs any cancer vs breast/cervical cancer
- Smoking vs e-cigarette/vaping
- Pneumococcal vs influenza vaccination
- FAQ/resource to estimate lane switching and vague follow-up handling
- Teen participation vs teen estimate redirect

## Important limitation

I am not claiming this is mathematically impossible to break. Natural language is open-ended, and future SHS modules may introduce new overlaps. What this build does is greatly expand the explicit tested surface area and add a stronger QC safety net. Any new dataset/module should be added with its own deconfliction tests before senior/public demos.

## How to test locally

```bash
python tests/run_expanded_deconfliction_qc.py
python tests/run_deep_deconfliction_qc.py
python tests/run_v2c_qc.py
python tests/run_v2ab_qc.py
python tests/run_phase7e_qc.py
python api_server.py
```

Then open:

```text
http://127.0.0.1:8018/debug
```

Suggested manual smoke tests:

```text
What percent of children with functioning difficulty had asthma last year?
What percent of adults missed six or more workdays last year?
How many people had insurance by insurance status?
What percent of adults had insurance last year by insurance for people under 65?
What percent of adults had asthma by insurance status last year?
What percent of uninsured kids got a flu shot last year?
Why should I participate in NHIS?
tell me more
What percent of teens had asthma last year?
```
