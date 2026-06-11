# DHIS/NHIS Chatbot Phase 4A Testing Checklist

Use this checklist to test whether the Phase 4A widget, API routing, estimate engine, FAQ retrieval, and deconfliction logic are behaving correctly.

## 1. Start the app

From the project folder:

```bash
cd dhis_nhis_chatbot
python api_server.py
```

Open:

```text
http://127.0.0.1:8018
```

Also check:

```text
http://127.0.0.1:8018/api/health
http://127.0.0.1:8018/api/sources
```

Expected behavior:

- The widget loads without errors.
- `/api/health` returns a healthy/ok response.
- `/api/sources` lists the adult/child DHIS sources and FAQ sources.

---

## 2. Core estimate tests

Goal: confirm the app retrieves estimates from the DHIS adult/child files and does not hallucinate.

Test examples:

```text
What percent of adults had current asthma last year?
What percent of kids got a flu shot last year?
How many people had diabetes in the last 2 years?
What percent of adults had diabetes in 2024 by SVI?
```

Expected behavior:

- Adult is used by default unless child/kid/children language is present.
- “Last year” maps to the latest available final-data year in the file.
- “Last 2 years” returns only the two latest available years.
- Generic topic questions return total/overall estimates.
- Grouped questions return rows for the matched grouping.
- Highest/lowest summaries appear when there are multiple numeric rows.
- The DQT/DQ page link appears when an estimate is found.

---

## 3. Topic deconfliction tests

Goal: confirm overlapping topics map correctly.

Test examples:

```text
What percent of children ever had asthma last year?
What percent of adults had an asthma attack last year?
How many adults took anxiety medication last year?
How many adults regularly felt depressed last year?
How many adults could not afford medical care last year?
How many adults skipped medicine to save money last year?
What percent of kids had ADHD last year?
What percent of kids had a learning disability last year?
```

Expected behavior:

- “Ever asthma” should not map to current asthma.
- “Asthma attack” should not map to current asthma.
- “Anxiety medication” should map to medication, not feelings of anxiety.
- “Regularly felt depressed” should map to feelings of depression, not depression medication.
- “Could not afford care” and “skipped medicine” should route to different cost-related topics.
- Child ADHD, learning disability, special education, and mental health service topics should stay separate.

---

## 4. Subgroup deconfliction tests

Goal: confirm subgroup/grouping detection works when terms overlap.

Test examples:

```text
What percent of adults got a flu shot last year by insurance for people under 65?
What percent of adults got a flu shot last year by insurance for seniors?
What percent of adults got a flu shot last year by race?
What percent of adults got a flu shot last year by race and ethnicity?
What percent of adults got a flu shot last year by SVI?
What percent of adults got a flu shot last year by metro area?
What percent of adults got a flu shot last year by poverty level?
What percent of adults got a flu shot last year by family income?
```

Expected behavior:

- Under-65 insurance should not return 65+ insurance.
- Senior/Medicare/65+ insurance should not return under-65 insurance.
- Race-only and race/Hispanic-origin groupings should stay distinct.
- SVI should expand all social vulnerability statuses.
- Metro/MSA/place of residence should not be confused when a more specific match is available.
- Poverty and family income should stay distinct.

---

## 5. Topic-vs-subgroup overlap tests

Goal: confirm a word can be interpreted as a topic or subgroup depending on context.

Test examples:

```text
What percent of adults were uninsured last year?
What percent of uninsured adults got a flu shot last year?
What percent of kids were uninsured last year?
What percent of kids with private insurance got a flu shot last year?
What percent of adults had a disability last year?
What percent of adults with a disability got a flu shot last year?
```

Expected behavior:

- “Were uninsured” should map to the uninsured topic.
- “Uninsured adults got a flu shot” should map to flu shot topic + uninsured subgroup.
- “Had a disability” should map to disability topic where available.
- “With a disability got a flu shot” should map to flu shot topic + disability subgroup where available.

---

## 6. Multiple subgroup limitation tests

Goal: confirm the bot does not invent unavailable crosstabs.

Test examples:

```text
What percent of Black women had diabetes last year?
What percent of gay men had current asthma last year?
What percent of gay men had diabetes last year by SVI?
What percent of uninsured Hispanic adults got a flu shot last year?
```

Expected behavior:

- If a requested multi-group crosstab is unavailable, the answer should say so.
- The bot should provide the closest available grouping, not a fake race × sex, sexual orientation × sex, or insurance × race result.
- The “Why this answer?” section should explain the limitation.

---

## 7. FAQ/general NHIS tests

Goal: confirm Phase 4A routes general questions to FAQ retrieval instead of estimate retrieval.

Test examples:

```text
What is NHIS?
Who is included in NHIS?
Where can I find the 2024 NHIS public use files?
What is the NHIS Data Query System?
What are NHIS early release estimates?
```

Expected behavior:

- These should route to FAQ/general knowledge, not the estimate engine.
- The answer should include source cards or CDC/NCHS source links.
- If the seed index does not have enough information, the answer should say it does not have enough sourced information rather than guessing.

---

## 8. Fallback/no-answer tests

Goal: confirm the app refuses unsupported estimates safely.

Test examples:

```text
What percent of adults had migraines last year by SVI?
What percent of kids had diabetes last year by sexual orientation?
What percent of adults had COVID last year by county?
What percent of children had cancer last year by state?
```

Expected behavior:

- No invented estimate.
- Approved fallback language appears.
- Link to the relevant NHIS documentation/PUF page appears.
- If relevant, CDC topic/source links may appear, but only if configured/retrieved.

---

## 9. UI checks

For each type of result, check:

- The answer is short and readable.
- Estimate values do not display special codes like `999%`, `777%`, etc.
- CIs are shown when available.
- Suppressed/special values show the correct symbol and footnote.
- Source links are visible.
- “Why this answer?” is understandable.
- Debug/matched-source drawer shows the expected topic, year, population, grouping, and row count.
- Feedback buttons are visible, but remember they are only local/demo labels until backend logging is added.

---

## 10. What to send back if something fails

For each failure, send:

```text
Question asked:
Expected behavior:
Actual behavior:
Screenshot if useful:
Debug drawer text or batch debug CSV row:
```

Best files to send back:

```text
batch debug output CSV
screenshots of wrong UI answers
matched-source/debug details
```
