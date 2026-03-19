"""
ChromaDB Vector Store Wrapper
Provides a clean interface for adding and querying course syllabus documents.
Uses ChromaDB's default embedding function for consistency.
"""
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import os


class VectorStoreManager:
    """
    Wraps a ChromaDB PersistentClient collection.
    Uses the default chromadb embedding function so all documents
    share the same embedding dimension (avoids InvalidDimensionException).
    """

    def __init__(
        self,
        db_path: str = "./data/chroma_db",
        collection_name: str = "armor_agent_syllabuses",
    ):
        self.db_path = db_path
        self.collection_name = collection_name

        os.makedirs(db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=db_path)

        # Use the built-in default embedding function (all-MiniLM-L6-v2 via chromadb)
        self._ef = embedding_functions.DefaultEmbeddingFunction()

        # Get or create the collection, always with the same embedding function
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add a list of documents to the collection.

        Each document dict must have:
            id       (str)  – unique identifier
            content  (str)  – text content to embed
            metadata (dict) – arbitrary key/value metadata (all values must be str/int/float/bool)
        """
        if not documents:
            return

        ids = [str(d["id"]) for d in documents]
        contents = [str(d["content"]) for d in documents]
        metadatas = []
        for d in documents:
            meta = {}
            for k, v in (d.get("metadata") or {}).items():
                # ChromaDB only accepts str/int/float/bool metadata values
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            # ChromaDB requires at least one metadata key
            if not meta:
                meta["_type"] = "document"
            metadatas.append(meta)

        # Upsert in batches of 100 to avoid potential size issues
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i : i + batch_size],
                documents=contents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    def query(
        self, query_text: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the collection for documents similar to query_text.

        Returns a list of dicts:
            { "content": str, "metadata": dict, "distance": float }
        """
        count = self.get_collection_count()
        if count == 0:
            return []

        # Clamp n_results to actual collection size
        n_results = min(n_results, count)

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            output.append(
                {
                    "content": doc,
                    "metadata": meta or {},
                    "distance": float(dist),
                }
            )
        return output

    def get_collection_count(self) -> int:
        """Return the number of documents currently in the collection."""
        return self.collection.count()

    def reset_collection(self) -> None:
        """Delete and recreate the collection (clears all documents)."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
