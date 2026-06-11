# DHIS/NHIS Assistant Phase 3: API + FAQ Wrapper

This phase keeps the deterministic adult/child DHIS Summary Health Statistics estimate engine as the authority for estimates and adds:

- `/api/ask` routing endpoint
- `/api/estimate` deterministic estimate endpoint
- `/api/faq` CDC/NCHS FAQ retrieval endpoint
- `/api/sources` source inventory endpoint
- Widget-style local UI
- Optional OpenAI model polishing hook, off by default
- Seed NHIS FAQ index from approved CDC/NCHS sources

## Run locally

```bash
cd dhis_nhis_chatbot
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018
```

## API examples

```bash
curl "http://127.0.0.1:8018/api/ask?q=What%20is%20NHIS%3F"
curl "http://127.0.0.1:8018/api/estimate?q=What%20percent%20of%20adults%20had%20diabetes%20last%20year%20by%20SVI%3F"
curl "http://127.0.0.1:8018/api/faq?q=Where%20do%20I%20get%202024%20NHIS%20public%20use%20files%3F"
```

## Optional OpenAI model polishing

The prototype does not need OpenAI to return answers. If configured, the model only rewrites the already-retrieved answer/evidence. It is instructed not to add estimates, facts, years, or sources.

```bash
set OPENAI_API_KEY=your_key_here
set OPENAI_MODEL=gpt-4.1-mini
set USE_OPENAI=1
python api_server.py
```

Use the UI checkbox or `use_model=true` in API calls.

## FAQ retrieval

The included FAQ index is a small seed index from approved CDC/NCHS NHIS pages. For a fuller demo, run:

```bash
python scripts/build_faq_index.py
```

That fetches only URLs from `config/faq_sources.json` and writes a refreshed FAQ index. Review the output before using it in a CDC-facing demo.

## QC

```bash
python tests/run_qc.py
python tests/run_phase3_qc.py
```

The estimate engine remains deterministic. If an estimate is not in the DHIS adult/child SHS files, the tool should use the approved fallback rather than inventing an estimate.
