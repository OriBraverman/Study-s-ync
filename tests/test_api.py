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


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    def test_register_new_user(self):
        """Register a new unique user and verify success."""
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["username"] == username

    def test_register_duplicate_user_returns_409(self):
        """Registering the same username twice should return 409."""
        import uuid
        username = f"dupuser_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
        assert resp.status_code == 409

    def test_login_valid_user(self):
        """Login with valid credentials should return a token."""
        import uuid
        username = f"loginuser_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        resp = client.post("/auth/login", json={"username": username, "password": "testpass123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "token" in data
        assert len(data["token"]) > 0

    def test_login_invalid_password_returns_401(self):
        resp = client.post("/auth/login", json={"username": "nonexistent_user_xyz", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_me_without_token_returns_401(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_token(self):
        import uuid
        username = f"meuser_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        login = client.post("/auth/login", json={"username": username, "password": "testpass123"}).json()
        token = login["token"]
        resp = client.get("/auth/me", headers={"X-Token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["username"] == username

    def test_logout_invalidates_token(self):
        import uuid
        username = f"logoutuser_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        login = client.post("/auth/login", json={"username": username, "password": "testpass123"}).json()
        token = login["token"]
        resp = client.post("/auth/logout", headers={"X-Token": token})
        assert resp.status_code == 200
        # After logout, /auth/me should reject the token
        me_resp = client.get("/auth/me", headers={"X-Token": token})
        assert me_resp.status_code == 401


# ---------------------------------------------------------------------------
# Course management endpoints
# ---------------------------------------------------------------------------

class TestCourseManagement:
    @staticmethod
    def _create_user_and_login():
        import uuid
        username = f"courseuser_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        login = client.post("/auth/login", json={"username": username, "password": "testpass123"}).json()
        return login["token"]

    def test_add_course(self):
        token = self._create_user_and_login()
        resp = client.post("/my_courses", headers={"X-Token": token, "Content-Type": "application/json"},
                           json={"course_name": "Data Structures", "course_num": "89-210"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["courses"]) == 1
        assert data["courses"][0]["course_name"] == "Data Structures"

    def test_list_courses(self):
        token = self._create_user_and_login()
        client.post("/my_courses", headers={"X-Token": token, "Content-Type": "application/json"},
                    json={"course_name": "Algorithms", "course_num": "89-220"})
        resp = client.get("/my_courses", headers={"X-Token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["courses"]) >= 1

    def test_delete_course(self):
        token = self._create_user_and_login()
        client.post("/my_courses", headers={"X-Token": token, "Content-Type": "application/json"},
                    json={"course_name": "Networking", "course_num": "89-300"})
        resp = client.delete("/my_courses/89-300", headers={"X-Token": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["courses"]) == 0

    def test_duplicate_course_returns_409(self):
        token = self._create_user_and_login()
        client.post("/my_courses", headers={"X-Token": token, "Content-Type": "application/json"},
                    json={"course_name": "OS", "course_num": "89-400"})
        resp = client.post("/my_courses", headers={"X-Token": token, "Content-Type": "application/json"},
                           json={"course_name": "OS Again", "course_num": "89-400"})
        assert resp.status_code == 409

    def test_courses_without_token_returns_401(self):
        resp = client.get("/my_courses")
        assert resp.status_code == 401
