# Retrieval Module

This folder holds retrieval logic over local course materials.

## Implemented Responsibilities

- `vector_store.py` — ChromaDB `VectorStoreManager` wrapper.
  - Persistent client with default embedding function (`all-MiniLM-L6-v2`).
  - Batch upsert, query with cosine distance, and collection reset.
- `ingest.py` — ingestion pipeline.
  - Loads `data/raw/syllabuses.json` and splits into course-level + topic-level documents.
  - Ingests inline mock CS drive documents and optional `.txt` files from `data/mock_cs_drive/`.

## Data Contract

- Input: pruned topic list (`PrunedTopicsSchema`).
- Output: ranked documents/passages with course and source metadata (`List[RetrievedChunk]`).

## Run

```powershell
python src/retrieval/ingest.py
```
