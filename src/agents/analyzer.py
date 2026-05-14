"""
Syllabus Analyzer Agent
Analyzes the syllabus JSON to determine which topics a student missed
based on their absence dates and course number.
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from src.schemas.models import StudentInputSchema, MissedTopicsSchema, WeeklyTopic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_course_num(course_num: str) -> str:
    """Normalize course number: strip spaces, allow '89-110' or '89110'."""
    return course_num.strip().replace(" ", "")


def load_syllabus(
    course_num: str,
    syllabus_path: str = "data/raw/syllabuses.json",
) -> Optional[dict]:
    """
    Load a single course record from syllabuses.json by course_num.
    Accepts both '89-110' and '89110' formats.
    Returns None if the course is not found.
    """
    path = Path(syllabus_path)
    if not path.exists():
        # Try relative to project root from file location
        alt = Path(__file__).resolve().parents[2] / "data" / "raw" / "syllabuses.json"
        if alt.exists():
            path = alt
        else:
            return None

    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    norm = _normalize_course_num(course_num)

    for record in records:
        rec_num = _normalize_course_num(record.get("course_num", ""))
        if rec_num == norm or rec_num == norm.replace("-", "") or rec_num.replace("-", "") == norm.replace("-", ""):
            return record

    return None


def estimate_missed_weeks(
    absence_start: date,
    absence_end: date,
    semester: str,
) -> list:
    """
    Estimate which week numbers were missed based on absence dates.

    BIU semesters:
      Semester A (סמסטר א') — starts ~October 15
      Semester B (סמסטר ב') — starts ~March 1
      Summer   (סמסטר ק') — starts ~July 1

    Returns a sorted list of 1-indexed week numbers in range [1, 15].
    """
    semester_starts = {
        "סמסטר א'": date(2025, 10, 15),
        "סמסטר ב'": date(2026, 3, 1),
        "סמסטר ק'": date(2026, 7, 1),
    }
    # Default to Semester B if unknown
    ref_start = semester_starts.get(semester, date(2026, 3, 1))

    missed_weeks = []
    current = absence_start
    while current <= absence_end:
        delta_days = (current - ref_start).days
        week_num = (delta_days // 7) + 1
        if 1 <= week_num <= 15 and week_num not in missed_weeks:
            missed_weeks.append(week_num)
        current += timedelta(days=1)

    return sorted(missed_weeks)


# ---------------------------------------------------------------------------
# Main Analyzer
# ---------------------------------------------------------------------------

def analyze_missed_topics(
    student_input: StudentInputSchema,
    syllabus_path: str = "data/raw/syllabuses.json",
) -> MissedTopicsSchema:
    """
    Main analyzer function.

    Steps:
    1. Load the syllabus record for the requested course_num.
    2. Estimate which weeks fall within the absence window.
    3. Mark topics from those weeks as missed.
    4. Return a MissedTopicsSchema.

    If the course is not found, returns a schema with a single informational
    entry in all_topics and an empty missed_topics list.
    """
    record = load_syllabus(student_input.course_num, syllabus_path)

    # --- Course not found ---------------------------------------------------
    if record is None:
        note = WeeklyTopic(
            week="N/A",
            topic=f"Course {student_input.course_num} not found in syllabus database.",
            is_missed=False,
        )
        return MissedTopicsSchema(
            course_name=student_input.course_name,
            course_num=student_input.course_num,
            absence_start=student_input.absence_start,
            absence_end=student_input.absence_end,
            semester="Unknown",
            all_topics=[note],
            missed_topics=[],
            total_weeks=0,
            missed_weeks_count=0,
        )

    # --- Extract course metadata --------------------------------------------
    course_name = record.get("course_name") or student_input.course_name
    semester = record.get("semester") or "סמסטר ב'"
    raw_topics: list = record.get("topics") or []

    # --- Build WeeklyTopic list for all topics ------------------------------
    all_topics: list = []
    for t in raw_topics:
        week_str = str(t.get("week", "?")).strip()
        topic_text = (t.get("topic") or "").strip()
        all_topics.append(
            WeeklyTopic(week=week_str, topic=topic_text, is_missed=False)
        )

    # --- Estimate missed weeks -----------------------------------------------
    missed_week_nums = estimate_missed_weeks(
        student_input.absence_start,
        student_input.absence_end,
        semester,
    )

    # Build a set of string representations for quick lookup
    missed_week_strs = {str(w) for w in missed_week_nums}

    # --- Mark missed topics --------------------------------------------------
    missed_topics: list = []
    for wt in all_topics:
        # Try to match week string to missed week numbers
        try:
            week_int = int(wt.week)
            is_missed = week_int in missed_week_nums
        except (ValueError, TypeError):
            # Week is "?" or non-numeric — cannot map, skip
            is_missed = False

        if is_missed:
            wt.is_missed = True
            missed_topics.append(wt)

    # If the syllabus has no structured weeks, fall back to positional indexing
    if not missed_topics and all_topics and missed_week_nums:
        for wn in missed_week_nums:
            idx = wn - 1
            if 0 <= idx < len(all_topics):
                all_topics[idx].is_missed = True
                missed_topics.append(all_topics[idx])

    return MissedTopicsSchema(
        course_name=course_name,
        course_num=student_input.course_num,
        absence_start=student_input.absence_start,
        absence_end=student_input.absence_end,
        semester=semester,
        all_topics=all_topics,
        missed_topics=missed_topics,
        total_weeks=len(all_topics),
        missed_weeks_count=len(missed_topics),
    )
