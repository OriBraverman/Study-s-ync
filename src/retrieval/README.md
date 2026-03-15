# Retrieval Module (Planned)

This folder will hold retrieval logic over local course materials.

## Planned Responsibilities

- Document chunking and embedding.
- Vector index management (ChromaDB or FAISS).
- Search API that returns ranked passages with metadata.
- Citation extraction support for downstream planner output.

## Data Contract

- Input: pruned topic list.
- Output: ranked documents/passages with course and source metadata.