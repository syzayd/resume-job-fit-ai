"""Job Application Tracker — save, track, and export your analyses."""

import os

import streamlit as st

for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
    if _k in st.secrets and not os.environ.get(_k):
        os.environ[_k] = st.secrets[_k]

from db import (
    STATUSES,
    delete_application,
    export_csv,
    get_all_applications,
    get_stats,
    update_notes,
    update_status,
)

st.set_page_config(page_title="Job Tracker — Resume Job-Fit AI", page_icon="📋", layout="wide")

st.title("📋 Job Application Tracker")
st.caption("Every analysis you save lands here. Track status, take notes, export to CSV.")

# --- Summary stats -----------------------------------------------------------

stats = get_stats()

if stats["total"] == 0:
    st.info(
        "No applications saved yet. Go to the main page, run an analysis, "
        "and click **Save to tracker**."
    )
else:
    col_total, col_avg, col_applied, col_interview, col_offer = st.columns(5)
    col_total.metric("Total saved", stats["total"])
    col_avg.metric("Avg fit score", f"{stats['avg_score']}/100")
    col_applied.metric("Applied", stats["by_status"].get("Applied", 0))
    col_interview.metric("Interviewing", stats["by_status"].get("Interviewing", 0))
    col_offer.metric("Offers", stats["by_status"].get("Offer", 0))

    st.divider()

    # --- Filter bar ----------------------------------------------------------
    filter_col, sort_col, _ = st.columns([2, 2, 4])
    with filter_col:
        status_filter = st.selectbox(
            "Filter by status", ["All"] + STATUSES, index=0
        )
    with sort_col:
        sort_by = st.selectbox("Sort by", ["Newest first", "Score (high→low)", "Score (low→high)"])

    apps = get_all_applications()

    # Apply filter
    if status_filter != "All":
        apps = [a for a in apps if a["status"] == status_filter]

    # Apply sort
    if sort_by == "Score (high→low)":
        apps.sort(key=lambda a: a["score"], reverse=True)
    elif sort_by == "Score (low→high)":
        apps.sort(key=lambda a: a["score"])

    if not apps:
        st.info(f"No applications with status '{status_filter}'.")
    else:
        st.markdown(f"**{len(apps)} application{'s' if len(apps) != 1 else ''}**")

        for app in apps:
            score = app["score"]
            color = "#16a34a" if score >= 75 else "#d97706" if score >= 50 else "#dc2626"

            with st.container(border=True):
                head, score_col = st.columns([6, 1])
                with head:
                    st.markdown(f"### {app['job_title']}")
                    company_str = f" · {app['company']}" if app["company"] else ""
                    st.caption(f"Saved {app['saved_on']}{company_str}")
                with score_col:
                    st.markdown(
                        f"<div style='text-align:center;padding-top:0.3rem;'>"
                        f"<span style='font-size:2rem;font-weight:800;color:{color};'>{score}</span>"
                        f"<span style='font-size:0.85rem;color:#888;'>/100</span></div>",
                        unsafe_allow_html=True,
                    )

                ctrl_col, note_col, del_col = st.columns([2, 5, 1])

                with ctrl_col:
                    new_status = st.selectbox(
                        "Status",
                        STATUSES,
                        index=STATUSES.index(app["status"]),
                        key=f"status_{app['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != app["status"]:
                        update_status(app["id"], new_status)
                        st.rerun()

                with note_col:
                    new_notes = st.text_input(
                        "Notes",
                        value=app["notes"],
                        placeholder="Add notes (recruiter name, next steps…)",
                        key=f"notes_{app['id']}",
                        label_visibility="collapsed",
                    )
                    if new_notes != app["notes"]:
                        update_notes(app["id"], new_notes)
                        st.rerun()

                with del_col:
                    if st.button("🗑️", key=f"del_{app['id']}", help="Delete this entry"):
                        delete_application(app["id"])
                        st.rerun()

    # --- Export --------------------------------------------------------------
    st.divider()
    st.download_button(
        label="Export all as CSV",
        data=export_csv(),
        file_name="job_applications.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Built in public by Zaid Ali Syed "
    "· [Live demo](https://resume-job-fit-ai.streamlit.app) "
    "· [GitHub](https://github.com/syzayd/resume-job-fit-ai)"
)
