# Resume Job-Fit AI

Paste a **job description** and your **resume** (or upload a PDF) → get an instant **fit score (0–100)**, the **keywords you're missing**, **AI-rewritten resume bullets**, a **tailored cover letter**, **interview prep**, and a **skills gap roadmap**.

Built to answer a real question every applicant has: *"How well does my resume actually match this job — and what do I do about it?"*

![Resume Job-Fit AI screenshot](docs/screenshot.png)

---

## What it does

| Feature | Details |
|---|---|
| **Fit score (0–100)** | Honest one-line verdict on how well you match |
| **Matched / missing keywords** | Color-coded chips showing exactly which skills to surface |
| **Tailored bullet rewrites** | Your real bullets, rewritten for impact and keyword alignment — never fabricated |
| **ATS tips** | Concrete phrases to add so applicant-tracking systems don't filter you out |
| **Cover letter** | Three-paragraph, role-specific draft grounded in your actual resume |
| **Interview prep** | 5–7 tailored questions with why-asked context and tips from your real background |
| **Skills gap roadmap** | Prioritized gaps (High / Medium / Low), named courses + providers, quick wins this week |
| **PDF upload** | Upload your resume PDF — text is extracted automatically |
| **Download full analysis** | Export everything (score, cover letter, interview prep, roadmap) as a `.txt` file |

---

## Tech

- **Google Gemini** (free tier, no credit card needed) via the official `google-genai` Python SDK
- **Model:** `gemini-2.5-flash-lite` — the most reliable free-tier model (overridable via `GEMINI_MODEL` env var)
- **Structured outputs** — Pydantic schemas passed as Gemini's `response_schema`; the model returns clean, validated JSON every time
- **Streamlit** front end — no HTML/JS needed
- **pdfplumber** for PDF text extraction
- **XSS prevention** — all Gemini-generated strings are passed through `html.escape()` before rendering with `unsafe_allow_html`
- **Auto-retry** — exponential backoff on transient 429 rate-limits and 5xx server errors (up to 3 attempts)
- Defensive error handling: missing/invalid key, rate limits, oversized input, malformed responses all show friendly messages

---

## Run it in 60 seconds

```bash
git clone https://github.com/syzayd/resume-job-fit-ai.git
cd resume-job-fit-ai

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

cp .env.example .env             # paste your FREE key from aistudio.google.com/apikey
streamlit run app.py
```

Then click **Load sample → Analyze fit** to see it work instantly.

---

## Project structure

```
resume-job-fit-ai/
├── app.py              # Streamlit UI — 4 tabs, PDF upload, session state
├── analyzer.py         # All Gemini logic — schemas, prompts, retry, error handling
├── requirements.txt
├── .env.example        # GEMINI_API_KEY=your-key-here  (never commit .env)
├── .gitignore
├── README.md
├── docs/
│   └── screenshot.png
├── sample/
│   ├── sample_resume.txt
│   └── sample_job.txt
└── handoffs/           # session handoff documents
```

---

## What I learned building this

**Structured outputs are a multiplier.** Passing a Pydantic schema as Gemini's `response_schema` turns the model from "hope it returns valid JSON" into a reliable typed component. No brittle string parsing — the SDK validates the response against the schema on every call.

**Prompt design matters more than model size.** The single most impactful instruction was *"never invent experience the candidate doesn't have."* It's one sentence, but it's what makes the rewrites actually trustworthy and usable. Quality of instruction beats size of model.

**Good error handling is a feature.** Most of the polish was making every failure surface as a friendly, actionable message — bad API key, rate limit, empty input, oversized input, PDF parse failure — instead of a stack trace. Users see this first, not the happy path.

**Free-tier quirks are real constraints.** `gemini-2.0-flash` has 0 free-tier quota right now. `gemini-2.5-flash` 503s under load. `gemini-2.5-flash-lite` is the actual reliable free-tier choice — you only know this by hitting failures in production.

**Streamlit session state needs intentional keying.** Streamlit reruns the entire script on every widget interaction. Without tracking `pdf_name` in `st.session_state`, the app re-extracted the PDF on every keypress. One extra state key eliminated the problem entirely.

**`-> NoReturn` is not optional for always-raise functions.** If a function always raises, annotating it `-> None` breaks type checker flow analysis — callers after `_handle_api_error(exc)` appear reachable. `-> NoReturn` + `raise _handle_api_error(exc)` at the call site is the correct pattern.

---

## Commit history

```
9434fb4 feat: PDF upload, interview prep tab, and skills gap roadmap
a8ea8e7 Fix formatting issues in README.md
e21d603 fix: XSS escaping, retry 429s, and NoReturn annotation from code review
9de3492 feat: cover letter generator tab + download full analysis as .txt
0011c6b feat: auto-retry Gemini 503s with exponential backoff (up to 3 attempts)
7e6ce54 docs: add live demo screenshot
e89bc6b fix: default to gemini-2.5-flash-lite (reliable free tier)
ba46291 refactor: switch from Claude to free Google Gemini
```

---

## Roadmap

- [x] PDF resume upload
- [x] Cover letter generator
- [x] Interview prep tab
- [x] Skills gap roadmap
- [ ] Update demo screenshot (screenshot predates the 4-tab UI)
- [ ] Save & compare past analyses
- [ ] Side-by-side multi-job comparison
- [ ] Live hosted demo (Streamlit Community Cloud)

---

*Built in public by **Zaid Ali Syed** · [github.com/syzayd](https://github.com/syzayd)*
*Rewrites stay truthful to your resume — review before using.*
