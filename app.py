"""Streamlit UI for the AI Resume / Job-Fit Tool.

Run: streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from analyzer import Analysis, AnalyzerError, analyze

SAMPLE_DIR = Path(__file__).parent / "sample"

st.set_page_config(page_title="Resume Job-Fit AI", page_icon="🎯", layout="wide")


def load_sample(name: str) -> str:
    try:
        return (SAMPLE_DIR / name).read_text(encoding="utf-8")
    except OSError:
        return ""


def score_color(score: int) -> str:
    if score >= 75:
        return "#16a34a"  # green
    if score >= 50:
        return "#d97706"  # amber
    return "#dc2626"      # red


def chips(items, bg: str, fg: str) -> None:
    if not items:
        st.caption("None found.")
        return
    html = " ".join(
        f"<span style='background:{bg};color:{fg};padding:4px 10px;border-radius:14px;"
        f"font-size:0.85rem;margin:2px;display:inline-block;'>{item}</span>"
        for item in items
    )
    st.markdown(html, unsafe_allow_html=True)


def render_results(result: Analysis) -> None:
    color = score_color(result.score)
    st.markdown(
        f"<div style='text-align:center;margin:0.5rem 0;'>"
        f"<span style='font-size:3.5rem;font-weight:800;color:{color};'>{result.score}</span>"
        f"<span style='font-size:1.2rem;color:#888;'>/100</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='text-align:center;font-size:1.1rem;'>{result.verdict}</p>", unsafe_allow_html=True)
    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("✅ Matched keywords")
        chips(result.matched_keywords, "#dcfce7", "#166534")
    with right:
        st.subheader("⚠️ Missing keywords")
        chips(result.missing_keywords, "#fee2e2", "#991b1b")

    st.divider()
    st.subheader("✍️ Tailored bullet rewrites")
    for i, rw in enumerate(result.bullet_rewrites, 1):
        with st.container(border=True):
            st.markdown(f"**Before:** {rw.original}")
            st.markdown(f"**After:** {rw.improved}")

    st.divider()
    st.subheader("📋 How to improve this application")
    st.write(result.summary)
    if result.ats_tips:
        st.markdown("**ATS tips:**")
        for tip in result.ats_tips:
            st.markdown(f"- {tip}")


# --- Layout ------------------------------------------------------------------

st.title("🎯 Resume Job-Fit AI")
st.caption("Paste a job description and your resume → get a fit score, keyword gaps, and tailored rewrites. "
           "Powered by Claude Sonnet 4.6.")

if "resume" not in st.session_state:
    st.session_state.resume = ""
    st.session_state.job = ""

col_a, col_b = st.columns(2)
with col_a:
    st.session_state.job = st.text_area("Job description", value=st.session_state.job, height=300,
                                        placeholder="Paste the job posting here...")
with col_b:
    st.session_state.resume = st.text_area("Your resume", value=st.session_state.resume, height=300,
                                           placeholder="Paste your resume text here...")

btn_analyze, btn_sample, _ = st.columns([1, 1, 4])
with btn_analyze:
    analyze_clicked = st.button("Analyze fit", type="primary", use_container_width=True)
with btn_sample:
    if st.button("Load sample", use_container_width=True):
        st.session_state.resume = load_sample("sample_resume.txt")
        st.session_state.job = load_sample("sample_job.txt")
        st.rerun()

if analyze_clicked:
    with st.spinner("Analyzing with Claude..."):
        try:
            result = analyze(st.session_state.resume, st.session_state.job)
            render_results(result)
        except AnalyzerError as err:
            st.error(str(err))

st.divider()
st.caption("Built in public by Zaid Ali Syed · Rewrites stay truthful to your resume — review before using.")
