"""Streamlit UI for the AI Resume / Job-Fit Tool.

Run: streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from analyzer import Analysis, AnalyzerError, CoverLetter, analyze, generate_cover_letter

SAMPLE_DIR = Path(__file__).parent / "sample"

st.set_page_config(page_title="Resume Job-Fit AI", page_icon="🎯", layout="wide")


# --- Helpers -----------------------------------------------------------------

def load_sample(name: str) -> str:
    try:
        return (SAMPLE_DIR / name).read_text(encoding="utf-8")
    except OSError:
        return ""


def score_color(score: int) -> str:
    if score >= 75:
        return "#16a34a"
    if score >= 50:
        return "#d97706"
    return "#dc2626"


def chips(items: list[str], bg: str, fg: str) -> None:
    if not items:
        st.caption("None found.")
        return
    html = " ".join(
        f"<span style='background:{bg};color:{fg};padding:4px 10px;border-radius:14px;"
        f"font-size:0.85rem;margin:2px;display:inline-block;'>{item}</span>"
        for item in items
    )
    st.markdown(html, unsafe_allow_html=True)


def analysis_as_text(result: Analysis, cover: CoverLetter | None = None) -> str:
    """Serialize results to a clean plain-text string for download."""
    lines = [
        "RESUME JOB-FIT ANALYSIS",
        "=" * 40,
        f"Score: {result.score}/100",
        f"Verdict: {result.verdict}",
        "",
        "MATCHED KEYWORDS",
        ", ".join(result.matched_keywords) or "None",
        "",
        "MISSING KEYWORDS",
        ", ".join(result.missing_keywords) or "None",
        "",
        "BULLET REWRITES",
    ]
    for rw in result.bullet_rewrites:
        lines += [f"  Before: {rw.original}", f"  After:  {rw.improved}", ""]
    lines += [
        "HOW TO IMPROVE",
        result.summary,
        "",
        "ATS TIPS",
    ]
    lines += [f"  - {tip}" for tip in result.ats_tips]
    if cover:
        lines += [
            "",
            "=" * 40,
            "COVER LETTER",
            "=" * 40,
            "",
            cover.opening,
            "",
            cover.body,
            "",
            cover.closing,
        ]
    return "\n".join(lines)


# --- Result panels -----------------------------------------------------------

def render_analysis(result: Analysis) -> None:
    color = score_color(result.score)
    st.markdown(
        f"<div style='text-align:center;margin:0.5rem 0;'>"
        f"<span style='font-size:3.5rem;font-weight:800;color:{color};'>{result.score}</span>"
        f"<span style='font-size:1.2rem;color:#888;'>/100</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:1.1rem;'>{result.verdict}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("Matched keywords")
        chips(result.matched_keywords, "#dcfce7", "#166534")
    with right:
        st.subheader("Missing keywords")
        chips(result.missing_keywords, "#fee2e2", "#991b1b")

    st.divider()
    st.subheader("Tailored bullet rewrites")
    for rw in result.bullet_rewrites:
        with st.container(border=True):
            st.markdown(f"**Before:** {rw.original}")
            st.markdown(f"**After &nbsp; :** {rw.improved}")

    st.divider()
    st.subheader("How to improve this application")
    st.write(result.summary)
    if result.ats_tips:
        st.markdown("**ATS tips:**")
        for tip in result.ats_tips:
            st.markdown(f"- {tip}")


def render_cover_letter(cover: CoverLetter) -> None:
    st.write(cover.opening)
    st.write(cover.body)
    st.write(cover.closing)


# --- Session state init ------------------------------------------------------

def _init() -> None:
    defaults = {
        "resume": "",
        "job": "",
        "result": None,
        "cover_letter": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# --- Layout ------------------------------------------------------------------

st.title("Resume Job-Fit AI")
st.caption(
    "Paste a job description and your resume — get a fit score, keyword gaps, "
    "tailored rewrites, and a cover letter. Powered by Google Gemini (free tier)."
)

col_a, col_b = st.columns(2)
with col_a:
    st.session_state.job = st.text_area(
        "Job description", value=st.session_state.job,
        height=300, placeholder="Paste the job posting here...",
    )
with col_b:
    st.session_state.resume = st.text_area(
        "Your resume", value=st.session_state.resume,
        height=300, placeholder="Paste your resume text here...",
    )

btn_analyze, btn_sample, btn_clear, _ = st.columns([1, 1, 1, 3])
with btn_analyze:
    analyze_clicked = st.button("Analyze fit", type="primary", use_container_width=True)
with btn_sample:
    if st.button("Load sample", use_container_width=True):
        st.session_state.resume = load_sample("sample_resume.txt")
        st.session_state.job = load_sample("sample_job.txt")
        st.session_state.result = None
        st.session_state.cover_letter = None
        st.rerun()
with btn_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.resume = ""
        st.session_state.job = ""
        st.session_state.result = None
        st.session_state.cover_letter = None
        st.rerun()

if analyze_clicked:
    with st.spinner("Analyzing with Gemini..."):
        try:
            st.session_state.result = analyze(st.session_state.resume, st.session_state.job)
            st.session_state.cover_letter = None  # clear stale letter on re-analysis
        except AnalyzerError as err:
            st.error(str(err))

# --- Results (persist across reruns) -----------------------------------------

if st.session_state.result:
    result: Analysis = st.session_state.result

    tab_analysis, tab_cover = st.tabs(["Analysis", "Cover Letter"])

    with tab_analysis:
        render_analysis(result)

    with tab_cover:
        cover: CoverLetter | None = st.session_state.cover_letter
        if cover is None:
            if st.button("Generate cover letter", type="primary"):
                with st.spinner("Writing your cover letter with Gemini..."):
                    try:
                        cover = generate_cover_letter(
                            st.session_state.resume, st.session_state.job
                        )
                        st.session_state.cover_letter = cover
                        st.rerun()
                    except AnalyzerError as err:
                        st.error(str(err))
        if cover:
            render_cover_letter(cover)

    st.divider()
    st.download_button(
        label="Download full analysis (.txt)",
        data=analysis_as_text(result, st.session_state.cover_letter),
        file_name="resume_analysis.txt",
        mime="text/plain",
    )

st.divider()
st.caption(
    "Built in public by Zaid Ali Syed "
    "· github.com/syzayd/resume-job-fit-ai "
    "· Rewrites stay truthful to your resume — review before using."
)
