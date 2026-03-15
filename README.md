# ArmorAgent

Token-efficient multi-agent system for BIU students returning from reserve duty, aligned with the plan in `PLANNING.md`.

## Current Status

- Repository structure has been reorganized by responsibility.
- The BIU syllabus scraper is isolated in `src/scraper`.
- Legacy/experimental code was moved to `experiments`.
- The scraper is treated as working baseline for now.

## Project Goal

ArmorAgent will:

1. Receive absence window and course list.
2. Identify missed topics from official syllabus data.
3. Retrieve the most relevant course materials.
4. Generate a prioritized recovery bootcamp plan with citations.

## Repository Structure

```text
ArmorAgent/
├─ PLANNING.md
├─ README.md
├─ requirements.txt
├─ data/
│  ├─ README.md
│  ├─ raw/
│  │  └─ README.md
│  └─ processed/
│     └─ README.md
├─ src/
│  ├─ __init__.py
│  ├─ README.md
│  ├─ scraper/
│  │  ├─ __init__.py
│  │  ├─ README.md
│  │  ├─ syllabus_scraper.py
│  │  ├─ batch_scrape_syllabuses.py
│  │  ├─ inspect_biu_home.py
│  │  └─ last_biu_home.html
│  ├─ agents/
│  │  └─ README.md
│  ├─ retrieval/
│  │  └─ README.md
│  ├─ orchestration/
│  │  └─ README.md
│  ├─ api/
│  │  └─ README.md
│  ├─ schemas/
│  │  └─ README.md
│  └─ ui/
│     └─ README.md
└─ experiments/
   ├─ README.md
   ├─ legacy_scraper/
   │  └─ README.md
   └─ legacy_artifacts/
      ├─ README.md
      └─ src_data_snapshot/
         └─ README.md
```

## Active Scraper Pipeline

The active scraping code is now in `src/scraper`.

### What it does

1. Opens BIU course portal and handles delayed form availability.
2. Filters by CS department (`המחלקה למדעי המחשב`, with fallback logic).
3. Traverses paginated results and collects unique `89*` course codes.
4. Scrapes syllabus text from dedicated syllabus link or details fallback.
5. Extracts heuristic weekly topics.
6. Merges with existing records and writes deduplicated JSON.

### Output

- Primary output: `data/raw/syllabuses.json`

### Run

```powershell
conda activate agents
pip install -r requirements.txt
python src/scraper/batch_scrape_syllabuses.py
```

Single course test:

```powershell
python src/scraper/syllabus_scraper.py 89-110
```

## Alignment With Planning

Based on `PLANNING.md`, this repo now separates:

- Data collection (`src/scraper`)
- Future agent implementations (`src/agents`)
- Retrieval/indexing (`src/retrieval`)
- Orchestration graph (`src/orchestration`)
- Backend API (`src/api`)
- Schema contracts (`src/schemas`)
- Frontend/UI (`src/ui`)

This keeps hackathon implementation steps isolated and easier to execute.

## Notes

- `experiments/legacy_scraper` is preserved for reference and is not part of production flow.
- Raw/processed data are ignored in git by default.
