# NHIS Assistant — GitHub/Railway Demo Package

This folder is the cleaned, Railway-ready demo version of the NHIS Assistant prototype.

## What this prototype does

- Answers natural-language NHIS adult/child Summary Health Statistics estimate questions.
- Supports follow-up questions within the same browser session, such as “what about by SVI?” or “show last 2 years.”
- Routes teen estimate questions to the NHIS Teen Summary Health Statistics tool.
- Routes participation/privacy/benefit/what-to-expect questions to the local approved participant-resource index.
- Provides three UI views:
  - `/` production-style demo UI
  - `/embed` iframe-friendly demo UI
  - `/debug` reviewer/debug UI
- OpenAI/GPT polishing is optional. Estimates are still retrieved deterministically from the local SHS files.

## Folder contents

Required app files:

```text
api_server.py
requirements.txt
Procfile
runtime.txt
src/
data/
config/
```

Helpful but optional support files:

```text
tests/
README_RAILWAY_DEPLOY.md
nhis_demo_readme_management_summary/
nhis_keyword_mapping_qc_kit/
dhis_nhis_batch_qc_input_csvs/
```

## Local run

From this folder:

```bat
python -m pip install -r requirements.txt
python api_server.py
```

Open:

```text
http://127.0.0.1:8018/
http://127.0.0.1:8018/embed
http://127.0.0.1:8018/debug
http://127.0.0.1:8018/api/health
```

## Railway deploy

1. Create a new GitHub repo.
2. Upload/push this folder to that repo.
3. In Railway, create a new project from the GitHub repo.
4. Railway should use the `Procfile` start command:

```text
web: python api_server.py
```

5. Optional GPT polishing variables:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

6. After deploy, open:

```text
https://YOUR-RAILWAY-APP.up.railway.app/
https://YOUR-RAILWAY-APP.up.railway.app/embed
https://YOUR-RAILWAY-APP.up.railway.app/debug
```

## Iframe example

```html
<iframe
  src="https://YOUR-RAILWAY-APP.up.railway.app/embed"
  title="NHIS Assistant"
  style="width:100%; max-width:820px; height:620px; border:0;">
</iframe>
```

## Quick QC

```bat
python tests/run_phase7e_qc.py
```

Suggested smoke-test questions:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
What about kids?
Explain the confidence interval.
Where do I get the data?
Why should teens participate in NHIS?
What percent of teens had asthma last year?
Why should adults participate in NHIS?
```

## Notes

- Do not commit an OpenAI API key to GitHub.
- Feedback logs are local runtime files and are intentionally excluded from Git.
- Railway file storage is not intended as a permanent feedback database. For production, route feedback to an approved persistent storage location.
