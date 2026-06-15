"""Core analysis logic: compares a resume against a job description using Claude.

Returns a validated `Analysis` object (Pydantic) describing fit score, keyword
gaps, tailored bullet rewrites, and ATS tips. Kept UI-agnostic so it can be
reused from Streamlit, a CLI, or tests.
"""

from __future__ import annotations

import json
import os
from typing import List

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

MODEL = "claude-sonnet-4-6"
MAX_INPUT_CHARS = 6000  # guard against runaway cost; we warn rather than truncate


class AnalyzerError(Exception):
    """User-facing error the UI can display verbatim."""


# --- Output schema -----------------------------------------------------------

class BulletRewrite(BaseModel):
    original: str = Field(description="A weak bullet taken from the resume.")
    improved: str = Field(description="A stronger, job-tailored rewrite, still truthful to the resume.")


class Analysis(BaseModel):
    score: int = Field(description="Overall fit score from 0 to 100.")
    verdict: str = Field(description="One-line honest summary of the fit.")
    matched_keywords: List[str] = Field(description="Important skills/terms the resume already covers.")
    missing_keywords: List[str] = Field(description="Important skills/terms from the job the resume is missing.")
    bullet_rewrites: List[BulletRewrite] = Field(description="2-4 tailored rewrites of real resume bullets.")
    summary: str = Field(description="2-4 sentences of concrete advice to improve this application.")
    ats_tips: List[str] = Field(description="Specific applicant-tracking-system tips (exact phrases to add, etc.).")


# --- Prompts -----------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a senior technical recruiter and ATS (applicant tracking system) screening expert. "
    "You assess how well a resume fits a specific job. You are specific, honest, and constructive. "
    "Critically: you NEVER invent experience, skills, or metrics the candidate does not have. "
    "Bullet rewrites must stay truthful to the original resume — improve clarity, impact, and keyword "
    "alignment, and where a real number is unknown, use a clear placeholder like [X] rather than inventing one."
)


def _build_user_prompt(resume: str, job: str) -> str:
    return (
        "Analyze how well the following resume fits the job description.\n\n"
        "=== JOB DESCRIPTION ===\n"
        f"{job}\n\n"
        "=== RESUME ===\n"
        f"{resume}\n\n"
        "Score the fit 0-100. List the most important matched and missing keywords/skills. "
        "Rewrite 2-4 of the candidate's actual resume bullets to better target this job (truthfully). "
        "Give a short, concrete summary of how to improve the application and specific ATS tips."
    )


# --- Public API --------------------------------------------------------------

def _validate(resume: str, job: str) -> None:
    if not resume.strip() or not job.strip():
        raise AnalyzerError("Please paste both a resume and a job description before analyzing.")
    if len(resume) > MAX_INPUT_CHARS or len(job) > MAX_INPUT_CHARS:
        raise AnalyzerError(
            f"Inputs are too long (limit {MAX_INPUT_CHARS:,} characters each). "
            "Trim to the most relevant sections and try again."
        )


def _client() -> anthropic.Anthropic:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise AnalyzerError(
            "No ANTHROPIC_API_KEY found. Create a key at https://console.anthropic.com/ "
            "and add it to a .env file as ANTHROPIC_API_KEY=your-key-here."
        )
    return anthropic.Anthropic()


def analyze(resume: str, job: str) -> Analysis:
    """Compare resume against job and return a validated Analysis.

    Raises AnalyzerError with a friendly message on any expected failure.
    """
    _validate(resume, job)
    client = _client()
    user_prompt = _build_user_prompt(resume, job)

    try:
        # Primary path: schema-validated structured output.
        response = client.messages.parse(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            output_format=Analysis,
        )
        if response.parsed_output is not None:
            return response.parsed_output
        # Fallback: parse the raw text ourselves if structured parsing returned nothing.
        return _parse_from_text(response)
    except anthropic.AuthenticationError:
        raise AnalyzerError("Your ANTHROPIC_API_KEY looks invalid. Double-check it in your .env file.")
    except anthropic.RateLimitError:
        raise AnalyzerError("The API is rate-limited right now. Wait a few seconds and try again.")
    except anthropic.BadRequestError as exc:
        msg = str(getattr(exc, "message", "") or exc).lower()
        if any(term in msg for term in ("credit balance", "billing", "too low")):
            raise AnalyzerError(
                "Your Anthropic account is out of API credits. Add credits at "
                "https://console.anthropic.com/ → Plans & Billing, then try again."
            )
        raise AnalyzerError(f"The API rejected the request: {getattr(exc, 'message', exc)}")
    except anthropic.APIConnectionError:
        raise AnalyzerError("Network error reaching the Claude API. Check your internet connection.")
    except anthropic.APIStatusError as exc:
        raise AnalyzerError(f"The Claude API returned an error ({exc.status_code}). Try again shortly.")


def _parse_from_text(response) -> Analysis:
    """Defensive fallback: extract the first JSON object from the response text."""
    text = next((b.text for b in response.content if b.type == "text"), "")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise AnalyzerError("Could not read the analysis from the model response. Please try again.")
    try:
        return Analysis(**json.loads(text[start : end + 1]))
    except (json.JSONDecodeError, ValueError):
        raise AnalyzerError("The model response was malformed. Please try again.")
