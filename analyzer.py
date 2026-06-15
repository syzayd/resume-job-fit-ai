"""Core analysis logic: compares a resume against a job description using Google Gemini.

Returns a validated `Analysis` object (Pydantic) describing fit score, keyword
gaps, tailored bullet rewrites, and ATS tips. Kept UI-agnostic so it can be
reused from Streamlit, a CLI, or tests. Uses Gemini's free tier.
"""

from __future__ import annotations

import json
import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

# Free-tier friendly default; override with GEMINI_MODEL if you like (e.g. gemini-2.5-flash).
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
MAX_INPUT_CHARS = 6000  # guard against runaway usage; we warn rather than truncate


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


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise AnalyzerError(
            "No GEMINI_API_KEY found. Create a FREE key (no credit card needed) at "
            "https://aistudio.google.com/apikey and add it to a .env file as GEMINI_API_KEY=your-key-here."
        )
    return genai.Client(api_key=api_key)


def analyze(resume: str, job: str) -> Analysis:
    """Compare resume against job and return a validated Analysis.

    Raises AnalyzerError with a friendly message on any expected failure.
    """
    _validate(resume, job)
    client = _client()
    user_prompt = _build_user_prompt(resume, job)

    try:
        # Primary path: schema-validated structured output (same Pydantic model Gemini fills in).
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=Analysis,
                temperature=0.3,
            ),
        )
        if isinstance(response.parsed, Analysis):
            return response.parsed
        # Fallback: parse the raw text ourselves if structured parsing returned nothing.
        return _parse_from_text(response.text)
    except genai_errors.ClientError as exc:
        msg = str(getattr(exc, "message", "") or exc).lower()
        code = getattr(exc, "code", None)
        if code in (401, 403) or any(t in msg for t in ("api key", "api_key", "unauthenticated", "permission")):
            raise AnalyzerError(
                "Your GEMINI_API_KEY looks invalid. Get a free key at "
                "https://aistudio.google.com/apikey and check your .env file."
            )
        if code == 429 or any(t in msg for t in ("quota", "rate", "resource_exhausted")):
            raise AnalyzerError("Hit the free-tier rate limit. Wait a minute and try again.")
        raise AnalyzerError(f"The Gemini API rejected the request: {getattr(exc, 'message', exc)}")
    except genai_errors.ServerError:
        raise AnalyzerError("Gemini is having a server issue right now. Try again shortly.")
    except genai_errors.APIError as exc:
        raise AnalyzerError(f"Gemini API error: {getattr(exc, 'message', exc)}")


def _parse_from_text(text: str | None) -> Analysis:
    """Defensive fallback: extract the first JSON object from the response text."""
    if not text:
        raise AnalyzerError("The model returned an empty response. Please try again.")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise AnalyzerError("Could not read the analysis from the model response. Please try again.")
    try:
        return Analysis(**json.loads(text[start : end + 1]))
    except (json.JSONDecodeError, ValueError):
        raise AnalyzerError("The model response was malformed. Please try again.")
