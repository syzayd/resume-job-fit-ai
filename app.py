"""Streamlit UI for the AI Resume / Job-Fit Tool.

Run: streamlit run app.py
"""

import html as _html
import io
from pathlib import Path

import streamlit as st

from analyzer import (
    Analysis, AnalyzerError, CoverLetter, InterviewPrep, SkillsRoadmap,
    analyze, generate_cover_letter, generate_interview_prep, generate_skills_roadmap,
)

SAMPLE_DIR = Path(__file__).parent / "sample"

st.set_page_config(page_title="Resume Job-Fit AI", page_icon="🎯", layout="wide")


# --- Helpers -----------------------------------------------------------------

def load_sample(name: str) -> str:
    try:
        return (SAMPLE_DIR / name).read_text(encoding="utf-8")
    except OSError:
        return ""


def extract_pdf_text(uploaded_file) -> str:
    import pdfplumber
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()


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
        f"font-size:0.85rem;margin:2px;display:inline-block;'>{_html.escape(item)}</span>"
        for item in items
    )
    st.markdown(html, unsafe_allow_html=True)


def analysis_as_text(
    result: Analysis,
    cover: CoverLetter | None = None,
    prep: InterviewPrep | None = None,
    roadmap: SkillsRoadmap | None = None,
) -> str:
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
    lines += ["HOW TO IMPROVE", result.summary, "", "ATS TIPS"]
    lines += [f"  - {tip}" for tip in result.ats_tips]
    if cover:
        lines += ["", "=" * 40, "COVER LETTER", "=" * 40, "",
                  cover.opening, "", cover.body, "", cover.closing]
    if prep:
        lines += ["", "=" * 40, "INTERVIEW PREP", "=" * 40, ""]
        lines += [f"Key advice: {prep.opening_tip}", ""]
        for i, q in enumerate(prep.questions, 1):
            lines += [f"Q{i}: {q.question}", f"    Why asked: {q.why_asked}",
                      f"    Tip: {q.tip}", ""]
    if roadmap:
        lines += ["", "=" * 40, "SKILLS ROADMAP", "=" * 40, "",
                  f"Timeline: {roadmap.timeline}", "",
                  "Quick wins this week:"]
        lines += [f"  - {w}" for w in roadmap.quick_wins]
        lines += ["", "Skill gaps (priority order):"]
        for gap in roadmap.gaps:
            lines += [f"\n  [{gap.importance}] {gap.skill}", f"  {gap.how_to_learn}"]
            for r in gap.resources:
                lines += [f"    - {r.name} ({r.provider}, {r.type})"]
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
        f"<p style='text-align:center;font-size:1.1rem;'>{_html.escape(result.verdict)}</p>",
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


def render_interview_prep(prep: InterviewPrep) -> None:
    st.info(f"**Key advice:** {prep.opening_tip}")
    st.divider()
    for i, q in enumerate(prep.questions, 1):
        with st.container(border=True):
            st.markdown(f"**Q{i}: {q.question}**")
            st.caption(f"Why asked: {q.why_asked}")
            st.markdown(f"Tip: {q.tip}")


def render_skills_roadmap(roadmap: SkillsRoadmap) -> None:
    st.markdown(f"**Estimated timeline to close key gaps:** {roadmap.timeline}")
    if roadmap.quick_wins:
        st.subheader("Quick wins this week")
        for win in roadmap.quick_wins:
            st.markdown(f"- {win}")
    st.divider()
    st.subheader("Skill gaps — priority order")
    importance_color = {"High": "#fee2e2", "Medium": "#fef9c3", "Low": "#f0fdf4"}
    importance_fg = {"High": "#991b1b", "Medium": "#854d0e", "Low": "#166534"}
    for gap in roadmap.gaps:
        bg = importance_color.get(gap.importance, "#f3f4f6")
        fg = importance_fg.get(gap.importance, "#374151")
        with st.container(border=True):
            st.markdown(
                f"<span style='background:{bg};color:{fg};padding:2px 8px;"
                f"border-radius:10px;font-size:0.8rem;font-weight:600;'>{_html.escape(gap.importance)}</span>"
                f" &nbsp; **{_html.escape(gap.skill)}**",
                unsafe_allow_html=True,
            )
            st.write(gap.how_to_learn)
            if gap.resources:
                for r in gap.resources:
                    st.markdown(f"- **{r.name}** — {r.provider} _{r.type}_")


# --- Session state init ------------------------------------------------------

def _init() -> None:
    defaults = {
        "resume": "",
        "job": "",
        "pdf_name": None,
        "result": None,
        "cover_letter": None,
        "interview_prep": None,
        "skills_roadmap": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# --- Layout ------------------------------------------------------------------

st.title("Resume Job-Fit AI")
st.caption(
    "Paste or upload your resume + a job description — get a fit score, keyword gaps, "
    "tailored rewrites, cover letter, interview prep, and a skills roadmap. "
    "Powered by Google Gemini (free tier)."
)

col_a, col_b = st.columns(2)
with col_a:
    st.session_state.job = st.text_area(
        "Job description", value=st.session_state.job,
        height=300, placeholder="Paste the job posting here...",
    )
with col_b:
    uploaded_pdf = st.file_uploader(
        "Upload resume PDF (or paste below)", type="pdf", label_visibility="visible",
    )
    if uploaded_pdf is not None and uploaded_pdf.name != st.session_state.pdf_name:
        try:
            st.session_state.resume = extract_pdf_text(uploaded_pdf)
            st.session_state.pdf_name = uploaded_pdf.name
            st.session_state.result = None
            st.session_state.cover_letter = None
            st.session_state.interview_prep = None
            st.session_state.skills_roadmap = None
            st.rerun()
        except Exception:
            st.error("Could not read the PDF. Try a text-based PDF or paste your resume below.")

    st.session_state.resume = st.text_area(
        "Your resume", value=st.session_state.resume,
        height=220, placeholder="Paste your resume text here...",
        label_visibility="collapsed",
    )

btn_analyze, btn_sample, btn_clear, _ = st.columns([1, 1, 1, 3])
with btn_analyze:
    analyze_clicked = st.button("Analyze fit", type="primary", use_container_width=True)
with btn_sample:
    if st.button("Load sample", use_container_width=True):
        st.session_state.resume = load_sample("sample_resume.txt")
        st.session_state.job = load_sample("sample_job.txt")
        st.session_state.pdf_name = None
        st.session_state.result = None
        st.session_state.cover_letter = None
        st.session_state.interview_prep = None
        st.session_state.skills_roadmap = None
        st.rerun()
with btn_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.resume = ""
        st.session_state.job = ""
        st.session_state.pdf_name = None
        st.session_state.result = None
        st.session_state.cover_letter = None
        st.session_state.interview_prep = None
        st.session_state.skills_roadmap = None
        st.rerun()

if analyze_clicked:
    with st.spinner("Analyzing with Gemini..."):
        try:
            st.session_state.result = analyze(st.session_state.resume, st.session_state.job)
            st.session_state.cover_letter = None
            st.session_state.interview_prep = None
            st.session_state.skills_roadmap = None
        except AnalyzerError as err:
            st.error(str(err))

# --- Results (persist across reruns) -----------------------------------------

if st.session_state.result:
    result: Analysis = st.session_state.result

    tab_analysis, tab_cover, tab_interview, tab_roadmap = st.tabs(
        ["Analysis", "Cover Letter", "Interview Prep", "Skills Roadmap"]
    )

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

    with tab_interview:
        prep: InterviewPrep | None = st.session_state.interview_prep
        if prep is None:
            if st.button("Generate interview prep", type="primary"):
                with st.spinner("Generating interview questions with Gemini..."):
                    try:
                        prep = generate_interview_prep(
                            st.session_state.resume, st.session_state.job
                        )
                        st.session_state.interview_prep = prep
                        st.rerun()
                    except AnalyzerError as err:
                        st.error(str(err))
        if prep:
            render_interview_prep(prep)

    with tab_roadmap:
        roadmap: SkillsRoadmap | None = st.session_state.skills_roadmap
        if roadmap is None:
            if st.button("Generate skills roadmap", type="primary"):
                with st.spinner("Building your skills roadmap with Gemini..."):
                    try:
                        roadmap = generate_skills_roadmap(
                            st.session_state.resume, st.session_state.job
                        )
                        st.session_state.skills_roadmap = roadmap
                        st.rerun()
                    except AnalyzerError as err:
                        st.error(str(err))
        if roadmap:
            render_skills_roadmap(roadmap)

    st.divider()
    st.download_button(
        label="Download full analysis (.txt)",
        data=analysis_as_text(
            result,
            st.session_state.cover_letter,
            st.session_state.interview_prep,
            st.session_state.skills_roadmap,
        ),
        file_name="resume_analysis.txt",
        mime="text/plain",
    )

st.divider()
st.caption(
    "Built in public by Zaid Ali Syed "
    "· github.com/syzayd/resume-job-fit-ai "
    "· Rewrites stay truthful to your resume — review before using."
)
