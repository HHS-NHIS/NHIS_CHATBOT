# NHIS Assistant — Railway Public Demo Deploy

This patch makes the current NHIS Assistant app Railway-ready for a public demo URL.

## What changed

- `api_server.py` now reads Railway's `PORT` environment variable.
- On Railway/public hosting, the app binds to `0.0.0.0` instead of `127.0.0.1`.
- Added `Procfile` with the start command: `python api_server.py`.
- Added `runtime.txt` and `requirements.txt`.

## Files to copy into the current project folder

Copy/replace these at the top level of your `dhis_nhis_chatbot` folder:

```text
api_server.py
requirements.txt
Procfile
runtime.txt
README_RAILWAY_DEPLOY.md
```

Your final project folder should still include the existing app files/folders:

```text
api_server.py
requirements.txt
Procfile
runtime.txt
src/
data/
config/
tests/
```

## Local test after applying this patch

From the project root:

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

Run QC:

```bat
python tests/run_phase7e_qc.py
```

## Deploy to Railway using GitHub

1. Create a GitHub repo for the `dhis_nhis_chatbot` folder.
2. Commit/push the full app folder, including:
   - `api_server.py`
   - `requirements.txt`
   - `Procfile`
   - `runtime.txt`
   - `src/`
   - `data/`
   - `config/`
   - `tests/`
3. In Railway, create a new project from the GitHub repo.
4. Railway should use the `Procfile` start command automatically:

```bash
python api_server.py
```

5. Add variables in Railway if you want GPT-style polishing:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Optional environment variable if you want model polishing enabled by default:

```text
USE_OPENAI=1
```

The app still works without OpenAI variables. It will use deterministic answers only.

## Public demo URLs

After Railway deploys, use your Railway domain:

```text
Main demo:
https://YOUR-RAILWAY-APP.up.railway.app/

Embeddable iframe version:
https://YOUR-RAILWAY-APP.up.railway.app/embed

Reviewer/debug version:
https://YOUR-RAILWAY-APP.up.railway.app/debug

Health check:
https://YOUR-RAILWAY-APP.up.railway.app/api/health
```

## Iframe example

```html
<iframe
  src="https://YOUR-RAILWAY-APP.up.railway.app/embed"
  title="NHIS Assistant"
  style="width:100%; max-width:820px; height:620px; border:0;">
</iframe>
```

## Important demo caveats

- Do not put your OpenAI API key in any HTML or JavaScript file.
- The OpenAI key belongs only in Railway Variables.
- Feedback CSV writing is fine for a demo, but Railway file storage may reset on redeploy/restart. Production feedback should use a persistent database, Google Sheet, or approved internal storage.
- This remains a prototype: adult/child estimates are deterministic from the local NHIS SHS files; teen estimate questions redirect to the teen SHS tool; participation/resource answers come from the local approved resource index.

## Quick smoke test after deploy

Try these in the public Railway URL:

```text
What percent of adults had diabetes last year?
What about by SVI?
Show last 2 years.
What about kids?
Why should teens participate in NHIS?
What percent of teens had asthma last year?
Is my information private and secure?
How has NHIS data helped with diabetes?
```

Expected:

- Adult/child estimates should return SHS estimates and CIs.
- Follow-up questions should remember prior context.
- Teen participation questions should route to participant/resource answers.
- Teen estimate questions should redirect to the teen SHS tool.
- `/embed` should show the compact iframe UI.
- `/debug` should show the reviewer/debug UI.
