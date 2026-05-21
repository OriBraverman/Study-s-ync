import json
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
SYLLABUSES_PATH = PROJECT_ROOT / "data" / "raw" / "syllabuses.json"
SYLLABUSES_FALLBACK_PATH = PROJECT_ROOT / "data" / "raw" / "syllabuses_with_fallback.json"

# Course details to insert
algorithms_course_entry = {
    "course_num": "89-210",
    "found": True,
    "course_name": "אלגוריתמים ומבני נתונים 1",
    "lecturer": "פרופ' שמואל וימר",
    "semester": "סמסטר א'",
    "syllabus_text": (
        "הקורס מציג מבני נתונים בסיסיים ולינאריים, עצי חיפוש, עצי AVL, "
        "שיטות לעיצוב וניתוח אלגוריתמים כולל הפרד ומשול, תכנות דינמי, אלגוריתמים חמדניים, "
        "חסמים תחתונים למיון, מיונים בזמן לינארי, וסריקת גרפים ומסלולים קצרים ביותר."
    ),
    "topics": [
        {"week": "1", "topic": "מבני נתונים לינאריים וערימות"},
        {"week": "2", "topic": "רקורסיה, סיבוכיות ומשפט המאסטר"},
        {"week": "3", "topic": "עצי חיפוש בינאריים ועצי AVL"},
        {"week": "4", "topic": "אלגוריתמי מיון וחסמים"},
        {"week": "5", "topic": "תכנות דינמי ובעיית חיתוך המוט"},
        {"week": "6", "topic": "אלגוריתמים חמדניים ובעיית בחירת הפעילויות"},
        {"week": "7", "topic": "סריקת גרפים ואלגוריתמי מסלול קצר ביותר"}
    ]
}

probability_course_entry = {
    "course_num": "89-230",
    "found": True,
    "course_name": "מבוא להסתברות ולסטטיסטיקה",
    "lecturer": "ד\"ר עמית שפירא",
    "semester": "סמסטר א'",
    "syllabus_text": (
        "קורס מבוא להסתברות ולסטטיסטיקה מיועד להקנות לסטודנטים מושגים בסיסיים בתורת ההסתברות וסטטיסטיקה יישומית. "
        "נושאי הלימוד כוללים: הגדרת מרחב מדגם, מאורעות, אקסיומות ההסתברות, הסתברות מותנית, נוסחת בייס, "
        "משתנים מקריים בדידים, התפלגויות מיוחדות (התפלגות ברנולי, התפלגות בינומית, התפלגות גיאומטרית, והתפלגות פואסון), "
        "משתנים מקריים רציפים, התפלגות אחידה, פונקציית התפלגות מצטברת CDF, וחישובי שטחי הסתברות."
    ),
    "topics": [
        {"week": "1", "topic": "מושגי יסוד: מרחב מדגם, אירועים והסתברות"},
        {"week": "2", "topic": "הסתברות מותנית ובייס"},
        {"week": "3", "topic": "משתנים מקריים והתפלגויות בדידות"},
        {"week": "4", "topic": "התפלגות פואסון והתפלגות רציפה אחידה"}
    ]
}

def update_file(file_path):
    if not file_path.exists():
        print(f"[WARN] File not found: {file_path}")
        return
        
    print(f"Loading {file_path.name} ...")
    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        
    original_len = len(records)
    # Remove existing 89-210 and 89-230 entries if any
    records = [r for r in records if r.get("course_num") not in ("89-210", "89-230")]
    
    # Append the new found entries
    records.append(algorithms_course_entry)
    records.append(probability_course_entry)
    print(f"Added course 89-210 and 89-230 syllabuses to {file_path.name}.")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)
        
    print(f"Successfully saved {len(records)} entries to {file_path.name}.")

def main():
    print("=" * 60)
    print("Study[S]ync - Syllabus Update Script")
    print("=" * 60)
    
    update_file(SYLLABUSES_PATH)
    update_file(SYLLABUSES_FALLBACK_PATH)
    
    print("=" * 60)
    print("Syllabus update complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
