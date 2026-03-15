# Scraper Module

This folder contains the BIU syllabus scraping implementation.

## Purpose

- Discover CS course codes (prefix `89`) from `https://courses.biu.ac.il/`.
- Scrape syllabus content for each discovered course.
- Normalize and save records to `data/raw/syllabuses.json`.

## Main Files

- `syllabus_scraper.py`: Single-course scraping and syllabus parsing.
- `batch_scrape_syllabuses.py`: Full batch pipeline with retries, dedupe, and merge.
- `inspect_biu_home.py`: Utility script for portal inspection/debug.
- `last_biu_home.html`: Captured HTML snapshot for troubleshooting.

## Run

From repository root:

```powershell
python src/scraper/batch_scrape_syllabuses.py
```

Single course:

```powershell
python src/scraper/syllabus_scraper.py 89-110
```