# Resume Job-Fit AI - Claude Instructions

Streamlit app scoring resume vs job description via Gemini. Live: https://resume-job-fit-ai.streamlit.app
Repo: https://github.com/syzayd/resume-job-fit-ai

## Run (one terminal)

```powershell
cd C:\Users\Asus\projects\resume-job-fit-ai
$env:PYTHONIOENCODING = "utf-8"
& "venv\Scripts\python" -m streamlit run app.py
```
URL: http://localhost:8501

## Python environment

- Venv folder is `venv` (Python 3.14), NOT `.venv`. Install deps with `& "venv\Scripts\python" -m pip install -r requirements.txt`.

## Tests

```powershell
& "venv\Scripts\python" -m pytest tests/ -q
```
Expected: 26 passed (all Gemini calls are mocked; no API key needed). GitHub Actions runs pytest on every push to main (`.github/workflows/ci.yml`).

## Env

- `.env` at repo root needs `GEMINI_API_KEY`; template in `.env.example`. Never read `.env` directly; ask the user for values.
- Streamlit Cloud deploy uses `.streamlit/secrets.toml` instead (format in `.streamlit/secrets.toml.example`).

## Model gotcha

- The Gemini model is `gemini-2.5-flash-lite` on purpose: `gemini-2.0-flash` had zero actual free quota and `gemini-2.5-flash` 503'd under load. Do not "upgrade" the model.

## Logs and handoffs (required every session)

- Master log: `MASTER_LOG.md` - append only, read just the tail (it is long).
- Handoffs: `handoffs/HANDOFF-YYYY-MM-DD-HHMM.md`.
- Before ending a session: update the master log AND write a handoff.

## Other gotchas

- `job_tracker.db` (SQLite) is gitignored and ephemeral on Streamlit Cloud.
- MASTER_LOG mentions auto-commit git hooks; no hooks are currently active in `.git/hooks` (verified 2026-07-02), so commit normally.
- Never use the em dash character (U+2014) anywhere; use " - " instead.
