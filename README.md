# ArmorAgent BIU Syllabus Extraction Pipeline

This project scrapes course syllabuses from the Bar-Ilan University course system at `https://courses.biu.ac.il/` and stores raw syllabus records in `data/raw/syllabuses.json`.

The pipeline targets Computer Science courses by filtering the BIU search portal to the Hebrew department query `המחלקה למדעי המחשב` and then collecting unique course codes (typically `89*`).

## What The Pipeline Does

1. Opens the BIU course search page with Selenium and waits for anti-bot verification to resolve.
2. Applies department filtering using `ContentPlaceHolder1_cmbDepartments` and searches for the CS department (`המחלקה למדעי המחשב`, value `84` fallback).
3. Traverses the paginated results grid and extracts unique `89*` course codes while handling postback pagination and recovery.
4. For each unique course, opens course details and attempts syllabus extraction from either:
	- dedicated syllabus link/tab, or
	- details-page fallback text when syllabus-like content is embedded.
5. Extracts weekly topics heuristically from syllabus text.
6. Loads existing JSON records (from `data/raw/syllabuses.json`, or legacy `src/data/raw/syllabuses.json`), merges by `course_num`, and keeps records deduplicated.
7. Validates output JSON structure and writes formatted UTF-8 JSON to `data/raw/syllabuses.json`.

## Output File

- Primary output: `data/raw/syllabuses.json`
- JSON structure: list of objects, each object contains:
	- `course_num` (string, format like `89-110`)
	- `found` (boolean)
	- `course_name` (string)
	- `lecturer` (string)
	- `semester` (string)
	- `department` (string)
	- `course_type` (string)
	- `search_term` (string)
	- `source_url` (string)
	- `scraped_at` (ISO timestamp)
	- `errors` (list of strings)
	- `syllabus_text` (string)
	- `topics` (list of objects with `week` and `topic`)

Example record:

```json
{
	"course_num": "89-110",
	"found": true,
	"course_name": "מבוא למדעי המחשב",
	"lecturer": "...",
	"semester": "סמסטר א'",
	"department": "המחלקה למדעי המחשב",
	"errors": [],
	"syllabus_text": "...",
	"topics": [
		{"week": "1", "topic": "..."}
	]
}
```

## Environment Setup

```powershell
conda activate agents
```

Install dependencies if needed:

```powershell
pip install -r requirements.txt
pip install selenium webdriver-manager
```

## Run The Full CS Scrape

```powershell
python src/batch_scrape_syllabuses.py
```

## Notes On Robustness

- The pipeline includes retry and backoff logic for intermittent network or anti-bot delays.
- Retries are skipped for deterministic outcomes (for example, no syllabus link on a course details page).
- It uses polite delays between requests to reduce load on the source system.
- Existing records are preserved and merged by `course_num` to avoid accidental overwrite.
