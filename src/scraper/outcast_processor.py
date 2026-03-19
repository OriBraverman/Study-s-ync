"""
Outcast Detector & Processor
Processes failed course records from syllabuses.json.
- Loads all records where found=False or topics=[]
- Saves them to data/outcasts/ for offline analysis
- Attempts fallback topic extraction using loose heuristics
- Writes updated data to data/raw/syllabuses_with_fallback.json

Run with:
    python src/scraper/outcast_processor.py
"""
import json
import re
import sys
from pathlib import Path

# Ensure project root on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

OUTCAST_DIR = PROJECT_ROOT / "data" / "outcasts"
SYLLABUS_PATH = PROJECT_ROOT / "data" / "raw" / "syllabuses.json"


# ---------------------------------------------------------------------------
# Outcast detection
# ---------------------------------------------------------------------------

def is_outcast(record: dict) -> bool:
    """
    A record is an outcast if it:
    - has found=False, OR
    - has no topics (empty list or missing key)
    """
    if not record.get("found"):
        return True
    topics = record.get("topics")
    if not topics or len(topics) == 0:
        return True
    return False


# ---------------------------------------------------------------------------
# Fallback topic extraction
# ---------------------------------------------------------------------------

def fallback_extract_topics(syllabus_text: str) -> list:
    """
    Fallback topic extraction for non-standard syllabuses.
    Uses looser heuristics: numbered lines, bullet points, Hebrew paragraphs.
    Returns a list of {"week": "?", "topic": str} dicts (max 15).
    """
    topics = []
    if not syllabus_text or not syllabus_text.strip():
        return topics

    lines = syllabus_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Numbered line: starts with digit or Hebrew letter followed by punctuation
        if re.match(r"^[\d\u05d0-\u05ea][.):\-\s]", line) and len(line) > 10:
            topics.append({"week": "?", "topic": line})
            continue

        # Bullet point
        if line.startswith(("•", "-", "*", "–", "→")) and len(line) > 10:
            topics.append({"week": "?", "topic": line.lstrip("•-*–→ \t")})
            continue

        # Hebrew content paragraph (likely a topic or description)
        hebrew_chars = sum(1 for c in line if "\u05d0" <= c <= "\u05ea")
        if len(line) > 20 and hebrew_chars >= 3:
            topics.append({"week": "?", "topic": line})

    # Deduplicate by text while preserving order
    seen = set()
    unique = []
    for t in topics:
        key = t["topic"].strip().lower()
        if key not in seen and len(key) > 5:
            seen.add(key)
            unique.append(t)

    return unique[:15]


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------

def process_outcasts() -> dict:
    """
    Find all outcast records, save them individually for analysis,
    apply fallback extraction, and write an updated JSON file.

    Returns a summary dict with counts.
    """
    OUTCAST_DIR.mkdir(parents=True, exist_ok=True)

    # Load records
    with SYLLABUS_PATH.open(encoding="utf-8") as f:
        records = json.load(f)

    outcasts = [r for r in records if is_outcast(r)]
    non_outcasts = [r for r in records if not is_outcast(r)]

    print(f"Total records  : {len(records)}")
    print(f"Successful     : {len(non_outcasts)}")
    print(f"Outcasts       : {len(outcasts)}")
    print()

    recovered = 0
    for record in outcasts:
        course_num = record.get("course_num", "unknown")
        safe_num = course_num.replace("-", "_").replace("/", "_")

        # Save outcast record to its own file for inspection
        outcast_file = OUTCAST_DIR / f"{safe_num}_outcast.json"
        with outcast_file.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # Attempt fallback extraction if we have any text
        syllabus_text = record.get("syllabus_text", "") or ""
        if syllabus_text.strip():
            fallback_topics = fallback_extract_topics(syllabus_text)
            if fallback_topics:
                record["topics"] = fallback_topics
                record["found"] = True
                record.setdefault("errors", []).append(
                    "[FALLBACK] Topics extracted via loose heuristics"
                )
                recovered += 1
                print(
                    f"  RECOVERED : {course_num} — "
                    f"{len(fallback_topics)} topic(s) via fallback"
                )
            else:
                print(
                    f"  FAILED    : {course_num} — "
                    "has syllabus text but no extractable topics"
                )
        else:
            print(f"  OUTCAST   : {course_num} — no syllabus text, cannot recover")

    print()
    print(f"Recovered via fallback : {recovered}/{len(outcasts)}")
    print(f"Outcast records saved to: {OUTCAST_DIR}/")

    # Write updated records
    updated_path = PROJECT_ROOT / "data" / "raw" / "syllabuses_with_fallback.json"
    with updated_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Updated data written to : {updated_path}")

    return {
        "total": len(records),
        "successful": len(non_outcasts),
        "outcasts": len(outcasts),
        "recovered": recovered,
        "still_failed": len(outcasts) - recovered,
    }


if __name__ == "__main__":
    summary = process_outcasts()
    print()
    print("=== Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
