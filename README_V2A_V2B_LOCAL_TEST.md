# NHIS Assistant V2A/B Local Test Build

This build adds the first two V2 workstreams:

1. **V2A: GPT-like chat UI + improved conversation routing**
2. **V2B: Editable approved-resource index workflow**

## What changed in V2A

- The production UI (`/`) now behaves more like a normal GPT-style chat transcript.
- Turns display in chronological order instead of reverse-order debug cards.
- Suggested follow-up chips appear under assistant responses.
- The input stays at the bottom of the conversation.
- The embed UI (`/embed`) also uses a compact chat transcript.
- The debug UI (`/debug`) remains available for reviewer/router details.
- Conversation state now stores the previous answer type, not just prior estimate fields.
- Vague follow-ups like `tell me more` now inherit the prior answer lane.

Example fixed path:

```text
You: Why should I participate in NHIS?
Assistant: [participation/resource answer]
You: tell me more
Assistant: [more participation/resource information]
```

The `tell me more` follow-up should no longer fall through to the adult/child SHS estimate fallback.

## What changed in V2B

The resource layer is no longer only buried in `data/faq_index/faq_index_seed.json`.

Editable source files are now here:

```text
resources/approved_urls.csv
resources/approved_documents/
```

Generated files are here:

```text
resources/generated/faq_index_seed.json
resources/generated/resource_index_qc_report.csv
```

The app now prefers:

```text
resources/generated/faq_index_seed.json
```

and falls back to:

```text
data/faq_index/faq_index_seed.json
```

if the generated V2 index is not present.

## How to run locally

From the project root:

```bash
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018/
```

Other views:

```text
http://127.0.0.1:8018/embed
http://127.0.0.1:8018/debug
```

## How to test the V2 follow-up fix

Use this sequence in `/`:

```text
Why should I participate in NHIS?
tell me more
```

Expected behavior: the second answer stays in the participation/resource lane.

Also test:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
```

Expected behavior: estimate follow-ups still work.

## How to edit approved resource URLs

Edit:

```text
resources/approved_urls.csv
```

Columns:

```csv
source_id,title,url,category,enabled
```

Set `enabled` to `false` to exclude a source without deleting it.

## How to add approved documents

Place approved `.txt`, `.docx`, or `.pdf` files in:

```text
resources/approved_documents/
```

Then rebuild the local resource index:

```bash
python scripts/build_resource_index.py
```

The script writes:

```text
resources/generated/faq_index_seed.json
resources/generated/resource_index_qc_report.csv
```

It also copies the generated index to the legacy path:

```text
data/faq_index/faq_index_seed.json
```

## Important note about web content

The app does **not** do live open web search at question time.

The intended V2 workflow is:

1. Add approved URLs/documents.
2. Run `scripts/build_resource_index.py`.
3. Review `resources/generated/resource_index_qc_report.csv`.
4. Start/redeploy the app.
5. The app answers from the local generated index.

This keeps responses controlled and auditable while making the approved content editable.

## QC checks

Run:

```bash
python tests/run_v2ab_qc.py
python tests/run_phase7e_qc.py
```

Expected:

```text
V2A/B QC: 14 / 14 passed
Phase 7E router/UI QC: 8 / 8 passed
```

## Railway note

This build keeps the Railway-compatible server behavior from the prior package:

- Uses `PORT` when present.
- Binds to `0.0.0.0` on public hosts.
- Uses `Procfile` and `runtime.txt`.

For local testing, it still defaults to:

```text
http://127.0.0.1:8018
```
