"""
Tests for VectorStoreManager (src/retrieval/vector_store.py).
Uses a temporary directory for each test so no state leaks between tests.
Run with: pytest tests/test_retrieval.py -v
"""
import os
import tempfile

import pytest

from src.retrieval.vector_store import VectorStoreManager


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_vector_store():
    """Create a fresh VectorStoreManager backed by a temporary directory."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        store = VectorStoreManager(db_path=tmpdir)
        yield store


@pytest.fixture
def populated_store():
    """A store pre-loaded with three documents."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        store = VectorStoreManager(db_path=tmpdir)
        docs = [
            {
                "id": "doc_loops",
                "content": "Loops allow repeated execution of code blocks. "
                           "For loops iterate over sequences. While loops run while a condition is true.",
                "metadata": {"topic": "loops", "type": "mock_doc"},
            },
            {
                "id": "doc_recursion",
                "content": "Recursion is when a function calls itself. "
                           "Base case terminates recursion. Stack frames accumulate.",
                "metadata": {"topic": "recursion", "type": "mock_doc"},
            },
            {
                "id": "doc_sorting",
                "content": "Sorting algorithms arrange elements in order. "
                           "Merge sort uses divide and conquer. Quick sort uses pivots.",
                "metadata": {"topic": "sorting", "type": "mock_doc"},
            },
        ]
        store.add_documents(docs)
        yield store


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestVectorStoreManager:

    def test_empty_collection_count(self, temp_vector_store):
        """A freshly created store should have 0 documents."""
        assert temp_vector_store.get_collection_count() == 0

    def test_add_documents_increases_count(self, temp_vector_store):
        docs = [
            {"id": "a", "content": "Content A about algorithms.", "metadata": {"type": "test"}},
            {"id": "b", "content": "Content B about data structures.", "metadata": {"type": "test"}},
        ]
        temp_vector_store.add_documents(docs)
        assert temp_vector_store.get_collection_count() == 2

    def test_query_returns_results(self, populated_store):
        """Querying with a relevant term should return non-empty results."""
        results = populated_store.query("function calling itself", n_results=2)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_query_returns_correct_fields(self, populated_store):
        """Each result dict must contain content, metadata, and distance."""
        results = populated_store.query("sorting algorithms", n_results=1)
        assert len(results) >= 1
        r = results[0]
        assert "content" in r
        assert "metadata" in r
        assert "distance" in r
        assert isinstance(r["distance"], float)

    def test_query_returns_relevant_results(self, populated_store):
        """
        Querying 'divide and conquer merge sort' should return the sorting doc
        as the top result (most similar by cosine distance).
        """
        results = populated_store.query("divide and conquer merge sort", n_results=3)
        assert len(results) >= 1
        # Top result should mention sorting or merge
        top_content = results[0]["content"].lower()
        assert any(kw in top_content for kw in ["sort", "merge", "divide", "pivot"])

    def test_query_on_empty_store_returns_empty(self, temp_vector_store):
        """Querying an empty store should return [] without raising."""
        results = temp_vector_store.query("algorithms", n_results=5)
        assert results == []

    def test_reset_collection_clears_documents(self, populated_store):
        """After reset, the collection count should be 0."""
        assert populated_store.get_collection_count() == 3
        populated_store.reset_collection()
        assert populated_store.get_collection_count() == 0

    def test_add_documents_after_reset(self, populated_store):
        """Documents can be added again after a reset."""
        populated_store.reset_collection()
        populated_store.add_documents(
            [{"id": "new_doc", "content": "New content after reset.", "metadata": {"type": "test"}}]
        )
        assert populated_store.get_collection_count() == 1

    def test_upsert_deduplication(self, temp_vector_store):
        """Adding the same document id twice should not create duplicates."""
        doc = {"id": "dup_id", "content": "Original content.", "metadata": {"v": "1"}}
        temp_vector_store.add_documents([doc])
        doc_updated = {"id": "dup_id", "content": "Updated content.", "metadata": {"v": "2"}}
        temp_vector_store.add_documents([doc_updated])
        # Still only one document with this id
        assert temp_vector_store.get_collection_count() == 1

    def test_metadata_stored_correctly(self, temp_vector_store):
        """Metadata keys and values round-trip through the store."""
        doc = {
            "id": "meta_test",
            "content": "Test metadata storage.",
            "metadata": {"course_num": "89-110", "week": "3", "type": "syllabus_topic"},
        }
        temp_vector_store.add_documents([doc])
        results = temp_vector_store.query("Test metadata storage", n_results=1)
        assert len(results) == 1
        meta = results[0]["metadata"]
        assert meta.get("course_num") == "89-110"
        assert meta.get("week") == "3"
