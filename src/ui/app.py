"""
Study[S]ync Streamlit Frontend

Run with:
    streamlit run src/ui/app.py --server.port 8501

Requires the FastAPI backend to be running at http://localhost:8000.
"""
import json
from datetime import date, timedelta

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Study[S]ync — BIU Recovery Bootcamp",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def fetch_courses():
    """Fetch available courses from the API (cached 5 min)."""
    try:
        resp = requests.get(f"{API_BASE}/courses", timeout=5)
        resp.raise_for_status()
        return resp.json().get("courses", [])
    except Exception:
        return []


def call_generate(payload: dict) -> dict:
    """POST to /generate_bootcamp and return the JSON response."""
    resp = requests.post(
        f"{API_BASE}/generate_bootcamp",
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def check_api_health() -> bool:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def priority_color(priority: str) -> str:
    return {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60"}.get(
        priority.lower(), "#7f8c8d"
    )


def priority_emoji(priority: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority.lower(), "⚪")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/he/thumb/8/82/BIU_Logo.svg/200px-BIU_Logo.svg.png",
        width=80,
    )
    st.title("🛡️ Study[S]ync")
    st.caption("Academic Recovery Bootcamp Generator")
    st.markdown("---")

    api_ok = check_api_health()
    if api_ok:
        st.success("API: Online", icon="✅")
    else:
        st.error("API: Offline — start the FastAPI backend", icon="❌")

    st.markdown("---")
    st.markdown(
        """
**How it works:**
1. Enter your course & absence dates
2. Study[S]ync analyses which topics you missed
3. Smart pruning removes duplicates & admin entries
4. Vector retrieval finds relevant study material
5. A personalised bootcamp plan is generated

**Architecture:**
- LangGraph multi-agent pipeline
- ChromaDB semantic search
- AgentPrune-inspired topic pruning
"""
    )

    st.markdown("---")
    demo_mode = st.checkbox("Demo Mode (pre-fill sample data)", value=False)

# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------
st.title("🛡️ Study[S]ync — Academic Recovery Bootcamp")
st.subheader("Bar-Ilan University · Computer Science Department")
st.markdown(
    "Missed lectures? Study[S]ync analyses your syllabus, "
    "retrieves relevant material, and builds a personalised study bootcamp."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Course list
# ---------------------------------------------------------------------------
courses = fetch_courses()
course_options = {
    f"{c['course_num']} — {c['course_name']} ({c['semester']})": c
    for c in courses
    if c.get("course_num") and c.get("course_name")
}

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Student Details")

    # Demo mode pre-fills values
    default_name = "Ori Ben-David" if demo_mode else ""
    default_course_key = (
        next(iter(course_options), None) if demo_mode else None
    )
    default_start = date(2026, 3, 8) if demo_mode else date.today()
    default_end = date(2026, 3, 21) if demo_mode else date.today() + timedelta(days=7)

    student_name = st.text_input(
        "Student Name",
        value=default_name,
        placeholder="e.g. Ori Ben-David",
    )

    if course_options:
        selected_key = st.selectbox(
            "Course",
            options=list(course_options.keys()),
            index=0,
        )
        selected_course = course_options[selected_key]
        course_name = selected_course["course_name"]
        course_num = selected_course["course_num"]
        st.caption(
            f"Lecturer: {selected_course.get('lecturer', 'N/A')} | "
            f"Topics: {selected_course.get('topics_count', '?')} weeks"
        )
    else:
        st.warning(
            "Could not fetch course list from API. Enter manually below.",
            icon="⚠️",
        )
        course_name = st.text_input(
            "Course Name",
            value="מבוא למדעי המחשב" if demo_mode else "",
            placeholder="e.g. מבוא למדעי המחשב",
        )
        course_num = st.text_input(
            "Course Number",
            value="89-110" if demo_mode else "",
            placeholder="e.g. 89-110",
        )

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        absence_start = st.date_input(
            "Absence Start Date",
            value=default_start,
            min_value=date(2025, 1, 1),
            max_value=date(2027, 12, 31),
        )
    with date_col2:
        absence_end = st.date_input(
            "Absence End Date",
            value=default_end,
            min_value=date(2025, 1, 1),
            max_value=date(2027, 12, 31),
        )

    if absence_end < absence_start:
        st.error("Absence end date must be on or after start date.")

with col2:
    st.subheader("Quick Info")
    if absence_end >= absence_start:
        duration = (absence_end - absence_start).days + 1
        st.metric("Absence Duration", f"{duration} days")
        st.metric(
            "Weeks Missed",
            f"~{max(1, duration // 7)} week{'s' if duration >= 14 else ''}",
        )
    st.markdown("---")
    st.info(
        "The pipeline runs entirely locally in mock mode "
        "(no OpenAI key required). Set `USE_MOCK_LLM=false` "
        "and provide `OPENAI_API_KEY` for GPT-4o-mini mode.",
        icon="ℹ️",
    )

# ---------------------------------------------------------------------------
# Generate button
# ---------------------------------------------------------------------------
st.markdown("---")
generate_col, _ = st.columns([1, 3])
with generate_col:
    generate_btn = st.button(
        "Generate Bootcamp Plan",
        type="primary",
        disabled=not api_ok or (absence_end < absence_start),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------
if generate_btn or (demo_mode and st.session_state.get("auto_demo_ran") is False):
    if not student_name.strip():
        st.warning("Please enter your student name.", icon="⚠️")
    elif not course_num.strip():
        st.warning("Please enter a course number.", icon="⚠️")
    else:
        st.session_state["auto_demo_ran"] = True
        payload = {
            "student_name": student_name,
            "course_name": course_name,
            "course_num": course_num,
            "absence_start": absence_start.isoformat(),
            "absence_end": absence_end.isoformat(),
        }

        with st.spinner("Running Study[S]ync pipeline… (Analyzer → Pruning → Retrieval → Planner)"):
            try:
                result = call_generate(payload)
            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot reach the API. Make sure the FastAPI server is running:\n"
                    "```\nuvicorn src.api.main:app --reload --port 8000\n```",
                    icon="❌",
                )
                st.stop()
            except requests.exceptions.HTTPError as e:
                st.error(f"API error: {e.response.text}", icon="❌")
                st.stop()
            except Exception as e:
                st.error(f"Unexpected error: {e}", icon="❌")
                st.stop()

        plan = result.get("bootcamp_plan", {})
        pruning = result.get("pruning_stats", {})

        st.success("Bootcamp plan generated!", icon="✅")

        # ----------------------------------------------------------------
        # Executive Summary
        # ----------------------------------------------------------------
        st.markdown("---")
        st.subheader("Executive Summary")
        st.info(plan.get("executive_summary", ""), icon="🎯")

        meta_col1, meta_col2, meta_col3 = st.columns(3)
        meta_col1.metric("Total Study Days", plan.get("total_days", 0))
        meta_col2.metric("Total Hours", f"{plan.get('total_hours', 0):.1f} hrs")
        meta_col3.metric("Topics Covered", len(plan.get("study_tasks", [])))

        # ----------------------------------------------------------------
        # Pruning Dashboard
        # ----------------------------------------------------------------
        st.markdown("---")
        st.subheader("AgentPrune Dashboard")
        st.caption(
            "The Pruning Router (inspired by AgentPrune) eliminated redundant "
            "and administrative entries before sending topics to the retriever, "
            "reducing LLM token usage."
        )

        p_col1, p_col2, p_col3 = st.columns(3)
        original = pruning.get("original_topic_count", 0)
        pruned_count = pruning.get("pruned_topic_count", 0)
        reduction = pruning.get("token_reduction_pct", 0.0)

        p_col1.metric("Original Topics", original)
        p_col2.metric(
            "After Pruning",
            pruned_count,
            delta=f"-{original - pruned_count}" if original > pruned_count else "0",
            delta_color="inverse",
        )
        p_col3.metric("Token Reduction", f"{reduction:.1f}%")

        if original > 0:
            st.progress(
                pruned_count / original if original > 0 else 0,
                text=f"{pruned_count}/{original} topics retained",
            )

        removed = pruning.get("topics_removed", [])
        reasons = pruning.get("removal_reasons", [])
        if removed:
            with st.expander(f"Topics removed ({len(removed)})", expanded=False):
                for topic, reason in zip(removed, reasons):
                    st.markdown(f"- **{topic}** — *{reason}*")

        pruning_log = pruning.get("pruning_log", [])
        if pruning_log:
            with st.expander("Full pruning log", expanded=False):
                for entry in pruning_log:
                    color = "#e74c3c" if "REMOVED" in entry else "#27ae60"
                    st.markdown(
                        f"<span style='color:{color}'>{entry}</span>",
                        unsafe_allow_html=True,
                    )

        # ----------------------------------------------------------------
        # Day-by-day study tasks
        # ----------------------------------------------------------------
        st.markdown("---")
        st.subheader("Day-by-Day Study Plan")

        tasks = plan.get("study_tasks", [])
        if not tasks:
            st.info(
                "No study tasks were generated. "
                "This may happen if all missed topics were pruned as administrative entries "
                "or if no topics could be mapped to your absence dates.",
                icon="ℹ️",
            )
        else:
            current_day = None
            for task in tasks:
                task_day = task.get("day", 1)
                if task_day != current_day:
                    current_day = task_day
                    st.markdown(f"#### Day {task_day}")

                priority = task.get("priority", "medium")
                emoji = priority_emoji(priority)
                color = priority_color(priority)

                with st.expander(
                    f"{emoji} {task.get('topic', '')} — {task.get('estimated_hours', 0):.1f}h",
                    expanded=(priority == "high"),
                ):
                    desc_col, meta_col = st.columns([3, 1])
                    with desc_col:
                        st.markdown(task.get("description", ""))
                    with meta_col:
                        st.markdown(
                            f"**Priority:** <span style='color:{color}'>{priority.upper()}</span>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**Time:** {task.get('estimated_hours', 0):.1f} hours")

                    # Study tips
                    tips = task.get("study_tips", [])
                    if tips:
                        st.markdown("**Study Tips:**")
                        for tip in tips:
                            st.markdown(f"  - {tip}")

                    # Citations
                    citations = task.get("citations", [])
                    if citations:
                        st.markdown("**Sources:**")
                        for cit in citations:
                            score_pct = int(cit.get("relevance_score", 0) * 100)
                            badge = (
                                "📄 Syllabus" if cit.get("source_type") == "syllabus"
                                else "📚 Reference"
                            )
                            st.markdown(
                                f"  - {badge} **{cit.get('source_name', '')}** "
                                f"(relevance: {score_pct}%)"
                            )

        # ----------------------------------------------------------------
        # Sources used
        # ----------------------------------------------------------------
        sources = plan.get("sources_used", [])
        if sources:
            st.markdown("---")
            st.subheader("Sources Used")
            for src in sources:
                st.markdown(f"- {src}")

        # ----------------------------------------------------------------
        # Raw JSON (debug)
        # ----------------------------------------------------------------
        with st.expander("Raw JSON response (debug)", expanded=False):
            st.json(result)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Study[S]ync v1.0 · Bar-Ilan University CS · "
    "Powered by LangGraph, ChromaDB, and AgentPrune-inspired routing."
)
