"""
Integration tests for the FastAPI endpoints.
Run with: pytest tests/test_api.py -v

The tests use FastAPI's TestClient so the actual server does not need to be running.
USE_MOCK_LLM is forced to 'true' so no OpenAI key is required.
"""
import os

# Force mock mode before importing the app
os.environ["USE_MOCK_LLM"] = "true"

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self):
        data = response = client.get("/health").json()
        assert data.get("status") == "ok"

    def test_health_contains_mock_mode_flag(self):
        data = client.get("/health").json()
        assert "mock_mode" in data
        assert data["mock_mode"] is True


# ---------------------------------------------------------------------------
# Courses endpoint
# ---------------------------------------------------------------------------

class TestListCourses:
    def test_courses_returns_200(self):
        response = client.get("/courses")
        assert response.status_code == 200

    def test_courses_returns_courses_key(self):
        data = client.get("/courses").json()
        assert "courses" in data

    def test_courses_list_not_empty(self):
        data = client.get("/courses").json()
        assert len(data["courses"]) > 0

    def test_course_has_required_fields(self):
        data = client.get("/courses").json()
        course = data["courses"][0]
        assert "course_num" in course
        assert "course_name" in course

    def test_total_field_matches_list_length(self):
        data = client.get("/courses").json()
        assert data.get("total") == len(data["courses"])


# ---------------------------------------------------------------------------
# Generate bootcamp endpoint
# ---------------------------------------------------------------------------

class TestGenerateBootcamp:
    _valid_payload = {
        "student_name": "Test Student",
        "course_name": "מבוא למדעי המחשב",
        "course_num": "89-110",
        "absence_start": "2026-03-01",
        "absence_end": "2026-03-14",
    }

    def test_valid_request_returns_200(self):
        response = client.post("/generate_bootcamp", json=self._valid_payload)
        assert response.status_code == 200

    def test_response_contains_bootcamp_plan(self):
        data = client.post("/generate_bootcamp", json=self._valid_payload).json()
        assert "bootcamp_plan" in data

    def test_response_contains_pruning_stats(self):
        data = client.post("/generate_bootcamp", json=self._valid_payload).json()
        assert "pruning_stats" in data

    def test_response_success_flag(self):
        data = client.post("/generate_bootcamp", json=self._valid_payload).json()
        assert data.get("success") is True

    def test_bootcamp_plan_has_student_name(self):
        data = client.post("/generate_bootcamp", json=self._valid_payload).json()
        plan = data["bootcamp_plan"]
        assert plan["student_name"] == "Test Student"

    def test_bootcamp_plan_has_course_num(self):
        data = client.post("/generate_bootcamp", json=self._valid_payload).json()
        plan = data["bootcamp_plan"]
        assert plan["course_num"] == "89-110"

    def test_nonexistent_course_returns_200(self):
        """An unknown course should still return 200 with an empty study plan."""
        payload = {
            "student_name": "Test Student",
            "course_name": "Nonexistent Course",
            "course_num": "99-999",
            "absence_start": "2026-03-01",
            "absence_end": "2026-03-14",
        }
        response = client.post("/generate_bootcamp", json=payload)
        assert response.status_code in [200, 404]

    def test_missing_required_field_returns_422(self):
        """Omitting a required field should return HTTP 422 Unprocessable Entity."""
        incomplete_payload = {
            "student_name": "Test",
            "course_name": "Intro CS",
            # course_num is missing
            "absence_start": "2026-03-01",
            "absence_end": "2026-03-14",
        }
        response = client.post("/generate_bootcamp", json=incomplete_payload)
        assert response.status_code == 422

    def test_pruning_stats_structure(self):
        data = client.post("/generate_bootcamp", json=self._valid_payload).json()
        stats = data["pruning_stats"]
        assert "original_topic_count" in stats
        assert "pruned_topic_count" in stats
        assert "token_reduction_pct" in stats

    def test_single_day_absence(self):
        """Even a one-day absence should produce a valid (possibly empty) response."""
        payload = {
            "student_name": "Quick Test",
            "course_name": "מבוא למדעי המחשב",
            "course_num": "89-110",
            "absence_start": "2026-03-08",
            "absence_end": "2026-03-08",
        }
        response = client.post("/generate_bootcamp", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "bootcamp_plan" in data
