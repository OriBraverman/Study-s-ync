"""
Unit tests for generate_test and _topic_to_key.
Runs entirely in mock mode — no API key required.
"""
import os
import re

import pytest

os.environ["USE_MOCK_LLM"] = "true"

from src.agents.tester.agent import MOCK_QUESTIONS, _topic_to_key, generate_test
from src.schemas.models import QuestionSchema, TestSchema


# ---------------------------------------------------------------------------
# _topic_to_key
# ---------------------------------------------------------------------------

class TestTopicToKey:
    def test_loops_english(self):
        assert _topic_to_key("Loops and iteration") == "loops"

    def test_loops_hebrew(self):
        assert _topic_to_key("לולאה בפייתון") == "loops"

    def test_iteration_keyword(self):
        assert _topic_to_key("iteration and range") == "loops"

    def test_recursion_english(self):
        assert _topic_to_key("Recursion and base cases") == "recursion"

    def test_recursion_hebrew(self):
        assert _topic_to_key("רקורסיה") == "recursion"

    def test_recursive_keyword(self):
        assert _topic_to_key("recursive factorial") == "recursion"

    def test_sorting_bubble(self):
        assert _topic_to_key("Bubble sort algorithm") == "sorting"

    def test_sorting_merge(self):
        assert _topic_to_key("Merge sort and quick sort") == "sorting"

    def test_sorting_hebrew(self):
        assert _topic_to_key("אלגוריתם מיון") == "sorting"

    def test_graphs_english(self):
        assert _topic_to_key("Graph traversal") == "graphs"

    def test_graphs_bfs(self):
        assert _topic_to_key("BFS and DFS") == "graphs"

    def test_graphs_hebrew(self):
        assert _topic_to_key("גרף ומסלולים") == "graphs"

    def test_unknown_falls_back_to_loops(self):
        assert _topic_to_key("Quantum computing") == "loops"

    def test_case_insensitive(self):
        assert _topic_to_key("RECURSION") == "recursion"


# ---------------------------------------------------------------------------
# generate_test
# ---------------------------------------------------------------------------

class TestGenerateTest:
    def test_returns_test_schema(self):
        result = generate_test("Loops")
        assert isinstance(result, TestSchema)

    def test_questions_are_question_schema_instances(self):
        result = generate_test("Recursion")
        for q in result.questions:
            assert isinstance(q, QuestionSchema)

    def test_num_questions_respected(self):
        result = generate_test("Loops", num_questions=1)
        assert result.total_questions == 1
        assert len(result.questions) == 1

    def test_num_questions_capped_by_bank_size(self):
        result = generate_test("Sorting", num_questions=10)
        bank_size = len(MOCK_QUESTIONS["sorting"])
        assert len(result.questions) <= bank_size

    def test_topic_preserved_in_output(self):
        result = generate_test("My Custom Topic")
        assert result.topic == "My Custom Topic"

    def test_estimated_minutes_matches_question_count(self):
        result = generate_test("Recursion", num_questions=2)
        assert result.estimated_minutes == result.total_questions * 5

    def test_total_questions_matches_list_length(self):
        result = generate_test("Loops")
        assert result.total_questions == len(result.questions)

    def test_generated_at_is_iso_format(self):
        result = generate_test("Graphs")
        # Should parse as ISO 8601 — ends with Z and has T separator
        assert "T" in result.generated_at
        assert result.generated_at.endswith("Z")

    def test_recursion_topic_stored_on_schema(self):
        # TestSchema.topic carries the caller's string; question topics are from the mock bank
        result = generate_test("Recursion and base cases", num_questions=2)
        assert result.topic == "Recursion and base cases"

    def test_sorting_topic(self):
        result = generate_test("Bubble sort", num_questions=1)
        assert len(result.questions) == 1

    def test_graphs_topic(self):
        result = generate_test("Graph BFS DFS", num_questions=1)
        assert len(result.questions) == 1

    def test_unknown_topic_returns_loops_fallback(self):
        result = generate_test("Quantum computing", num_questions=1)
        assert len(result.questions) == 1

    def test_question_types_are_valid_values(self):
        valid_types = {"multiple_choice", "short_answer", "code_tracing"}
        result = generate_test("Loops")
        for q in result.questions:
            assert q.question_type in valid_types

    def test_difficulty_values_are_valid(self):
        valid = {"easy", "medium", "hard"}
        result = generate_test("Recursion")
        for q in result.questions:
            assert q.difficulty in valid

    def test_multiple_choice_has_options(self):
        result = generate_test("Loops", num_questions=2)
        mc_questions = [q for q in result.questions if q.question_type == "multiple_choice"]
        for q in mc_questions:
            assert len(q.options) > 0

    def test_correct_answer_nonempty(self):
        result = generate_test("Recursion")
        for q in result.questions:
            assert q.correct_answer.strip() != ""

    def test_explanation_nonempty(self):
        result = generate_test("Sorting")
        for q in result.questions:
            assert q.explanation.strip() != ""
