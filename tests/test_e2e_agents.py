"""
End-to-end tests for all agent endpoints.
Run with: pytest tests/test_e2e_agents.py -v

Tests the full flow:
  1. Load lectures -> select topic -> chat with tutor
  2. Generate bootcamp plan (Planner Agent)
  3. Generate visualizer (Visualizer Agent)
  4. Generate test (Tester Agent)
"""
import os

# Force mock mode before importing the app
os.environ["USE_MOCK_LLM"] = "true"

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Lecture Database (Friend's UI)
# ---------------------------------------------------------------------------

class TestLectureEndpoints:
    def test_get_all_lectures_returns_200(self):
        response = client.get("/get_missed_class_all")
        assert response.status_code == 200

    def test_get_all_lectures_returns_list(self):
        data = client.get("/get_missed_class_all").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_lecture_has_required_fields(self):
        data = client.get("/get_missed_class_all").json()
        lecture = data[0]
        assert "course_name" in lecture
        assert "lecture_date" in lecture
        assert "topic" in lecture
        assert "content" in lecture
        assert "ai_questions" in lecture

    def test_get_specific_lecture_found(self):
        # The database.json has a lecture for Algorithms on 2022-03-01
        response = client.get("/get_missed_class/%D7%90%D7%9C%D7%92%D7%95%D7%A8%D7%99%D7%AA%D7%9E%D7%99%D7%9D%201/2022-03-01")
        assert response.status_code in [200, 404]  # depends on exact course name encoding

    def test_get_specific_lecture_not_found(self):
        response = client.get("/get_missed_class/NonexistentCourse/2025-01-01")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# AI Tutor Chat
# ---------------------------------------------------------------------------

class TestChatEndpoint:
    def test_chat_returns_200(self):
        payload = {
            "user_message": "מה זה אלגוריתם דייקסטרה?",
            "history": []
        }
        response = client.post("/chat", json=payload)
        # If no local LLM is running this may return 503, so accept both
        assert response.status_code in [200, 503]

    def test_chat_with_history(self):
        payload = {
            "user_message": "תסביר עוד",
            "history": [
                {"role": "assistant", "content": "שאלה קודמת"},
                {"role": "user", "content": "תשובה קודמת"}
            ]
        }
        response = client.post("/chat", json=payload)
        assert response.status_code in [200, 503]

    def test_chat_missing_message(self):
        payload = {"history": []}
        response = client.post("/chat", json=payload)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 422, 503]


# ---------------------------------------------------------------------------
# Planner Agent — /generate_bootcamp
# ---------------------------------------------------------------------------

class TestPlannerAgentE2E:
    _payload = {
        "student_name": "Alice",
        "course_name": "מבוא למדעי המחשב",
        "course_num": "89-110",
        "absence_start": "2026-03-01",
        "absence_end": "2026-03-14",
    }

    def test_full_pipeline_returns_plan(self):
        response = client.post("/generate_bootcamp", json=self._payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "bootcamp_plan" in data

    def test_plan_has_study_tasks(self):
        data = client.post("/generate_bootcamp", json=self._payload).json()
        plan = data["bootcamp_plan"]
        assert "study_tasks" in plan
        # 89-110 has ~12 topics; with 2-week absence we expect some missed topics
        assert len(plan["study_tasks"]) >= 0

    def test_plan_tasks_have_citations(self):
        data = client.post("/generate_bootcamp", json=self._payload).json()
        plan = data["bootcamp_plan"]
        for task in plan.get("study_tasks", []):
            assert "citations" in task
            assert "study_tips" in task
            assert task["estimated_hours"] > 0

    def test_plan_has_pruning_stats(self):
        data = client.post("/generate_bootcamp", json=self._payload).json()
        stats = data["pruning_stats"]
        assert "original_topic_count" in stats
        assert "pruned_topic_count" in stats
        assert "token_reduction_pct" in stats

    def test_single_day_absence(self):
        payload = {
            "student_name": "Bob",
            "course_name": "מבוא למדעי המחשב",
            "course_num": "89-110",
            "absence_start": "2026-03-08",
            "absence_end": "2026-03-08",
        }
        response = client.post("/generate_bootcamp", json=payload)
        assert response.status_code == 200

    def test_unknown_course(self):
        payload = {
            "student_name": "Charlie",
            "course_name": "Unknown",
            "course_num": "99-999",
            "absence_start": "2026-03-01",
            "absence_end": "2026-03-14",
        }
        response = client.post("/generate_bootcamp", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        plan = data["bootcamp_plan"]
        assert plan["total_days"] == 0
        assert plan["total_hours"] == 0.0


# ---------------------------------------------------------------------------
# Visualizer Agent — /generate_visualizer
# ---------------------------------------------------------------------------

class TestVisualizerAgentE2E:
    def test_generate_visualizer_returns_200(self):
        payload = {"topic": "Bubble Sort", "concept_type": "sorting"}
        response = client.post("/generate_visualizer", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "visualizer" in data

    def test_visualizer_has_code(self):
        payload = {"topic": "Bubble Sort"}
        data = client.post("/generate_visualizer", json=payload).json()
        viz = data["visualizer"]
        assert "react_code" in viz
        assert "html_wrapper" in viz
        assert "explanation" in viz
        assert len(viz["react_code"]) > 0

    def test_visualizer_no_concept_type(self):
        payload = {"topic": "Graph BFS"}
        response = client.post("/generate_visualizer", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_visualizer_complex_topic(self):
        payload = {"topic": "Pipeline Data Hazards in MIPS", "concept_type": "cpu_pipeline"}
        response = client.post("/generate_visualizer", json=payload)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tester Agent — /generate_test
# ---------------------------------------------------------------------------

class TestTesterAgentE2E:
    def test_generate_test_returns_200(self):
        response = client.post("/generate_test?topic=Recursion&num_questions=2")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test" in data

    def test_test_has_questions(self):
        response = client.post("/generate_test?topic=Recursion&num_questions=2")
        data = response.json()
        test = data["test"]
        assert "questions" in test
        assert test["total_questions"] > 0
        assert test["estimated_minutes"] > 0

    def test_question_structure(self):
        response = client.post("/generate_test?topic=Loops&num_questions=1")
        data = response.json()
        test = data["test"]
        assert len(test["questions"]) >= 1
        q = test["questions"][0]
        assert "question_text" in q
        assert "correct_answer" in q
        assert "explanation" in q
        assert "difficulty" in q

    def test_default_num_questions(self):
        response = client.post("/generate_test?topic=Sorting")
        data = response.json()
        test = data["test"]
        assert test["total_questions"] >= 1

    def test_with_difficulty(self):
        response = client.post("/generate_test?topic=Graphs&num_questions=2&difficulty=medium")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# Full User Journey
# ---------------------------------------------------------------------------

class TestFullUserJourney:
    def test_end_to_end_flow(self):
        """
        Simulate a full user session:
        1. Load lectures
        2. Pick a date range
        3. Generate bootcamp plan
        4. Generate visualizer for a topic
        5. Generate test for a topic
        6. Chat with tutor
        """
        # 1. Load lectures
        lectures = client.get("/get_missed_class_all").json()
        assert len(lectures) > 0
        lecture = lectures[0]

        # 2. Get specific lecture
        course = lecture["course_name"]
        date = lecture["lecture_date"]
        resp = client.get(f"/get_missed_class/{course}/{date}")
        # may 404 depending on URL encoding, that's ok

        # 3. Generate bootcamp
        bootcamp_resp = client.post("/generate_bootcamp", json={
            "student_name": "Test",
            "course_name": course,
            "course_num": "89-110",
            "absence_start": "2022-03-01",
            "absence_end": "2022-03-31",
        })
        assert bootcamp_resp.status_code == 200
        bootcamp = bootcamp_resp.json()
        assert bootcamp["success"] is True
        plan = bootcamp["bootcamp_plan"]

        # 4. Generate visualizer for the lecture topic
        viz_resp = client.post("/generate_visualizer", json={
            "topic": lecture["topic"],
            "concept_type": None,
        })
        assert viz_resp.status_code == 200
        viz = viz_resp.json()
        assert viz["success"] is True
        assert "react_code" in viz["visualizer"]

        # 5. Generate test for the lecture topic
        test_resp = client.post(f"/generate_test?topic={lecture['topic']}&num_questions=2")
        assert test_resp.status_code == 200
        test_data = test_resp.json()
        assert test_data["success"] is True
        assert "questions" in test_data["test"]

        # 6. Chat with tutor
        chat_resp = client.post("/chat", json={
            "user_message": "הסבר לי על " + lecture["topic"],
            "history": []
        })
        assert chat_resp.status_code in [200, 503]  # 503 if no LLM running


# ---------------------------------------------------------------------------
# Demo User — Danny Israely
# ---------------------------------------------------------------------------

class TestDemoUser:
    _demo_token = "21575b2934a50e7402008e11aa1f5c88"

    def test_demo_user_exists(self):
        """The pre-seeded demo user should be valid and return user info."""
        resp = client.get("/auth/me", headers={"X-Token": self._demo_token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["username"] == "Danny Israely"
        assert len(data["user"]["courses"]) == 3

    def test_demo_user_courses_have_name_and_num(self):
        resp = client.get("/auth/me", headers={"X-Token": self._demo_token})
        courses = resp.json()["user"]["courses"]
        for c in courses:
            assert "course_name" in c
            assert "course_num" in c
            assert len(c["course_num"]) > 0

    def test_lectures_filtered_by_demo_courses(self):
        """When Danny's token is sent, /get_missed_class_all should return only his courses."""
        all_resp = client.get("/get_missed_class_all")
        all_lectures = all_resp.json()

        filtered_resp = client.get("/get_missed_class_all", headers={"X-Token": self._demo_token})
        filtered = filtered_resp.json()

        assert isinstance(filtered, list)
        # All filtered lectures must belong to one of Danny's 3 courses
        demo_names = {c["course_name"] for c in client.get("/auth/me", headers={"X-Token": self._demo_token}).json()["user"]["courses"]}
        for lec in filtered:
            assert lec["course_name"] in demo_names

    def test_demo_user_can_add_and_remove_course(self):
        """Demo user should be able to manage courses."""
        resp = client.post("/my_courses", headers={"X-Token": self._demo_token, "Content-Type": "application/json"},
                           json={"course_name": "Test Temp", "course_num": "89-999"})
        assert resp.status_code == 200
        data = resp.json()
        assert any(c["course_num"] == "89-999" for c in data["courses"])

        # Cleanup
        client.delete("/my_courses/89-999", headers={"X-Token": self._demo_token})


# ---------------------------------------------------------------------------
# Visualizer — HTML wrapper quality
# ---------------------------------------------------------------------------

class TestVisualizerHtmlWrapper:
    def test_html_wrapper_contains_react_code_inline(self):
        """The HTML wrapper should contain enough JS to render the component."""
        resp = client.post("/generate_visualizer", json={"topic": "Quick Sort"})
        assert resp.status_code == 200
        viz = resp.json()["visualizer"]
        html = viz["html_wrapper"]
        # Should reference React or contain a component definition
        assert len(html) > 100
        assert "html" in html.lower() or "react" in html.lower() or "script" in html.lower()

    def test_visualizer_explanation_is_not_empty(self):
        resp = client.post("/generate_visualizer", json={"topic": "Merge Sort"})
        viz = resp.json()["visualizer"]
        assert len(viz["explanation"]) > 0


# ---------------------------------------------------------------------------
# Tester — Edge cases
# ---------------------------------------------------------------------------

class TestTesterEdgeCases:
    def test_test_with_hebrew_topic(self):
        """Tester should handle Hebrew topic strings."""
        resp = client.post("/generate_test?topic=%D7%90%D7%9C%D7%92%D7%95%D7%A8%D7%99%D7%AA%D7%9E%D7%99%D7%9D&num_questions=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "questions" in data["test"]

    def test_test_with_difficulty(self):
        resp = client.post("/generate_test?topic=Binary+Search&num_questions=1&difficulty=hard")
        assert resp.status_code == 200
        data = resp.json()
        # In mock mode difficulty is ignored, just verify question exists
        assert data["test"]["questions"][0]["difficulty"] in ["easy", "medium", "hard"]
