# 🎯 Resume Job-Fit AI

Paste a **job description** and your **resume** → get an instant **fit score (0–100)**, the
**keywords you're missing**, and **AI-rewritten resume bullets** tailored to the role.

Built to answer a real question every applicant has: *"How well does my resume actually match this job — and what should I change?"*

> 📸 *Demo screenshot coming soon — clone it and click **Load sample → Analyze fit** to try it in seconds.*

---

## What it does

- **Fit score (0–100)** with an honest one-line verdict
- **Matched vs. missing keywords** so you see exactly which skills to surface
- **Tailored bullet rewrites** — your real bullets, rewritten for impact and keyword alignment (never fabricated)
- **ATS tips** — concrete phrases to add so applicant-tracking systems don't filter you out

## Tech

- **Claude Sonnet 4.6** via the official `anthropic` Python SDK
- **Structured outputs** (Pydantic schema) so the model returns clean, validated JSON every time
- **Streamlit** front end — no HTML/JS needed
- Defensive error handling (missing/invalid key, rate limits, oversized input, malformed responses)

## Run it in 60 seconds

```bash
git clone https://github.com/<your-username>/resume-job-fit-ai.git
cd resume-job-fit-ai

python -m venv venv
venv\Scripts\activate            # Windows  (use: source venv/bin/activate  on macOS/Linux)
pip install -r requirements.txt

cp .env.example .env             # then paste your key from console.anthropic.com
streamlit run app.py
```

Then click **Load sample → Analyze fit** to see it work instantly.

## What I learned building this

- **Structured outputs** turn an LLM from "hope it returns JSON" into a reliable component — defining a
  Pydantic schema and using `messages.parse` removed all the brittle string-parsing I'd normally need.
- **Prompt design matters more than model size** — the single most important instruction was *"never invent
  experience the candidate doesn't have,"* which keeps the rewrites honest and usable.
- **Good error handling is a feature** — most of the polish was making every failure (bad key, rate limit,
  empty input) show a friendly message instead of a stack trace.

## Roadmap

- [ ] PDF resume upload
- [ ] Save & compare past analyses
- [ ] Side-by-side multi-job comparison
- [ ] Live hosted demo

---

*Built in public by **Zaid Ali Syed** while learning AI engineering. Rewrites are suggestions — always review before using.*
