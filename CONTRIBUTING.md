# Contributing

Thanks for looking at Resume Job-Fit AI. It is a personal project, but issues and
small, focused PRs are welcome.

## Ground rules

1. **Tests stay offline and keyless.** `pytest tests/ -q` must pass with a dummy
   `GEMINI_API_KEY` and no network - every Gemini call in `tests/test_analyzer.py` is
   mocked. A PR that adds a test requiring a real API key or network call will be
   asked to mock it.
2. **One concern per PR.** Small and surgical beats broad and clever.
3. **All Gemini logic stays in `analyzer.py`.** Schemas, prompts, retries, and error
   handling live there; `app.py` and the `pages/` scripts are UI only - keep them thin.
4. **Don't change the model without a reason in the PR description.**
   `gemini-2.5-flash-lite` is used on purpose (`gemini-2.0-flash` has no real free
   quota, `gemini-2.5-flash` 503s under load) - see the Model gotcha in `CLAUDE.md`.
5. **This app is live in production** (resume-job-fit-ai.streamlit.app). Do not modify
   `.streamlit/config.toml` or `.streamlit/secrets.toml.example` in a feature PR.

## Dev setup

Follow the Quickstart in [README.md](README.md), then:

```bash
pip install -r requirements.txt
pytest tests/ -q
```

All tests should pass before and after your change. CI runs the same command on every
push and PR.
