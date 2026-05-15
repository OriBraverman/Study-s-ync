"""
Study[S]ync FastAPI Backend

Endpoints:
  GET  /                      — serve the main HTML UI
  GET  /health                — liveness check
  GET  /courses               — list courses that have syllabuses
  POST /auth/register        — register a new user
  POST /auth/login           — login and receive token
  POST /auth/logout          — invalidate token
  GET  /auth/me              — get current user info
  GET  /my_courses           — list user's registered courses
  POST /my_courses           — add a course to user
  DELETE /my_courses/{course_num} — remove a course from user
  POST /generate_bootcamp    — run the full LangGraph pipeline (Planner Agent)
  POST /generate_visualizer  — generate an interactive React visualizer (Visualizer Agent)
  POST /generate_test        — generate a practice test for a topic (Tester Agent)
  GET  /get_missed_class_all — list all lectures from the database (optionally filtered by user courses)
  GET  /get_missed_class/{course_name}/{date} — get a specific lecture
  POST /scrape_course        — trigger scraping for a specific course
  POST /chat                 — AI tutor chat

Run with:
    uvicorn src.api.main:app --reload --port 8000
"""
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.schemas.models import (
    BootcampPlanSchema,
    StudentInputSchema,
    TestSchema,
    VisualizerRequestSchema,
    VisualizerOutputSchema,
)
from src.orchestration.graph import run_pipeline
from src.agents.visualizer.agent import generate_visualizer
from src.agents.tester.agent import generate_test, chat_with_tester
from src.api.users import (
    create_user,
    authenticate_user,
    logout_user,
    get_user_by_token,
    add_user_course,
    remove_user_course,
    get_user_courses,
)

# Only default to mock mode when no API key is configured.
if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
    os.environ.setdefault("USE_MOCK_LLM", "true")
else:
    os.environ.setdefault("USE_MOCK_LLM", "false")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Study[S]ync API",
    description="BIU Academic Vest Recovery Bootcamp Generator",
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files (friend's HTML UI)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).resolve().parents[2] / "src" / "ui" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_syllabus_path() -> Path:
    env_path = os.getenv("SYLLABUS_JSON_PATH", "")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    # Try relative to project root
    candidates = [
        Path("data/raw/syllabuses.json"),
        Path(__file__).resolve().parents[2] / "data" / "raw" / "syllabuses.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("syllabuses.json not found. Check SYLLABUS_JSON_PATH env var.")


def _load_courses() -> list:
    path = _get_syllabus_path()
    with path.open(encoding="utf-8") as f:
        records = json.load(f)
    return [
        {
            "course_num": r.get("course_num", ""),
            "course_name": r.get("course_name", ""),
            "semester": r.get("semester", ""),
            "lecturer": r.get("lecturer", ""),
            "topics_count": len(r.get("topics", [])),
            "has_syllabus": bool(r.get("found") and r.get("syllabus_text", "").strip()),
        }
        for r in records
        if r.get("found") and r.get("course_num")
    ]


def _get_lectures_db_path() -> Path:
    candidates = [
        Path("data/lectures_database.json"),
        Path(__file__).resolve().parents[2] / "data" / "lectures_database.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("lectures_database.json not found.")


def _load_lectures() -> list:
    path = _get_lectures_db_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# React code sanitizer for in-browser Babel
# ---------------------------------------------------------------------------

def _sanitize_react_code(code: str) -> str:
    """
    Convert ES-module React imports/exports into globals that Babel standalone
    can execute directly in the browser (no bundler).

    Transforms:
      import React, { useState } from 'react'
      import ReactDOM from 'react-dom'
      export default MyComponent
    into:
      const { useState } = React;
      const ReactDOM = window.ReactDOM;
      // (export line removed)
    """
    import re
    lines_out = []
    for line in code.splitlines():
        stripped = line.strip()
        # Remove ES-module imports
        if stripped.startswith("import "):
            # import React, { useState, useEffect } from 'react'
            m = re.match(r'import\s+(.*?)\s+from\s+["\']([^"\']+)["\'];?', stripped)
            if m:
                bindings = m.group(1)
                module = m.group(2)
                if module == 'react':
                    # Extract named bindings like { useState, useEffect }
                    named_match = re.search(r'\{([^}]+)\}', bindings)
                    if named_match:
                        names = named_match.group(1).strip()
                        lines_out.append(f"const {{ {names} }} = React;")
                elif 'react-dom' in module:
                    # import ReactDOM from 'react-dom'
                    default_match = re.match(r'(\w+)', bindings)
                    if default_match:
                        lines_out.append(f"const {default_match.group(1)} = window.ReactDOM;")
                continue
        # Remove export statements
        if stripped.startswith("export default"):
            continue
        lines_out.append(line)
    return "\n".join(lines_out)


# ---------------------------------------------------------------------------
# System Prompt for AI Tutor
# ---------------------------------------------------------------------------

_TUTOR_SYSTEM_PROMPT: str = ""

def _load_tutor_prompt() -> str:
    global _TUTOR_SYSTEM_PROMPT
    if _TUTOR_SYSTEM_PROMPT:
        return _TUTOR_SYSTEM_PROMPT
    candidates = [
        Path("data/prompts/tutor_system_prompt.txt"),
        Path(__file__).resolve().parents[2] / "data" / "prompts" / "tutor_system_prompt.txt",
    ]
    for c in candidates:
        if c.exists():
            _TUTOR_SYSTEM_PROMPT = c.read_text(encoding="utf-8")
            return _TUTOR_SYSTEM_PROMPT
    # Fallback prompt
    _TUTOR_SYSTEM_PROMPT = (
        "You are a patient and encouraging Computer Science tutor. "
        "Help the student understand missed topics by asking guiding questions. "
        "Never give the final answer immediately. Keep responses concise and in Hebrew."
    )
    return _TUTOR_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class GenerateBootcampRequest(BaseModel):
    student_name: str
    course_name: str
    course_num: str
    absence_start: date
    absence_end: date


class ChatRequest(BaseModel):
    user_message: str
    history: list = []


class TesterChatRequest(BaseModel):
    topic: str
    topic_content: str
    messages: list  # [{"role": "user"|"assistant", "content": "..."}]


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AddCourseRequest(BaseModel):
    course_name: str
    course_num: str


class ScrapeRequest(BaseModel):
    course_num: str


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/register")
def register(request: RegisterRequest):
    """Register a new user."""
    try:
        user = create_user(request.username, request.password)
        return {"success": True, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Registration failed: {exc}")


@app.post("/auth/login")
def login(request: LoginRequest):
    """Login and receive a token."""
    token = authenticate_user(request.username, request.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"success": True, "token": token}


@app.post("/auth/logout")
def logout(x_token: str = Header(default="")):
    """Invalidate the current token."""
    logout_user(x_token)
    return {"success": True}


@app.get("/auth/me")
def get_me(x_token: str = Header(default="")):
    """Get current user info."""
    user = get_user_by_token(x_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "courses": user.get("courses", []),
        },
    }


# ---------------------------------------------------------------------------
# User course management
# ---------------------------------------------------------------------------

@app.get("/my_courses")
def list_my_courses(x_token: str = Header(default="")):
    """List the courses registered by the current user."""
    try:
        courses = get_user_courses(x_token)
        return {"success": True, "courses": courses}
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/my_courses")
def add_my_course(request: AddCourseRequest, x_token: str = Header(default="")):
    """Add a course to the current user's list."""
    try:
        result = add_user_course(x_token, request.course_name, request.course_num)
        return {"success": True, "courses": result["courses"]}
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/my_courses/{course_num}")
def delete_my_course(course_num: str, x_token: str = Header(default="")):
    """Remove a course from the current user's list."""
    try:
        result = remove_user_course(x_token, course_num)
        return {"success": True, "courses": result["courses"]}
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def serve_index():
    """Serve the main HTML UI."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        response = FileResponse(str(index_path))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    raise HTTPException(status_code=404, detail="Frontend not built.")


@app.get("/health")
def health_check():
    """Returns a simple alive signal and current configuration."""
    return {
        "status": "ok",
        "service": "Study[S]ync API",
        "version": "1.3.0",
        "mock_mode": os.getenv("USE_MOCK_LLM", "true").lower() == "true",
    }


@app.get("/courses")
def list_courses():
    """
    Return the list of courses that have syllabuses in the database.
    Useful for populating the UI dropdown.
    """
    try:
        courses = _load_courses()
        return {
            "courses": courses,
            "total": len(courses),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load courses: {exc}")


@app.post("/generate_bootcamp", response_model=dict)
async def generate_bootcamp(request: GenerateBootcampRequest):
    """
    Run the full Study[S]ync pipeline for the given student and absence window.

    Returns:
        {
            "bootcamp_plan": { ...BootcampPlanSchema... },
            "pruning_stats": { ...PruningStats... },
            "success": true
        }
    """
    try:
        student_input = StudentInputSchema(
            student_name=request.student_name,
            course_name=request.course_name,
            course_num=request.course_num,
            absence_start=request.absence_start,
            absence_end=request.absence_end,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid input: {exc}")

    try:
        plan: BootcampPlanSchema = run_pipeline(student_input)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    # Serialize with pydantic v2
    plan_dict = plan.model_dump(mode="json")

    return {
        "success": True,
        "bootcamp_plan": plan_dict,
        "pruning_stats": plan_dict.get("pruning_stats", {}),
    }


@app.post("/generate_visualizer", response_model=dict)
async def generate_visualizer_endpoint(request: VisualizerRequestSchema):
    """
    Generate an interactive React visualizer for a given topic.

    Returns:
        {
            "success": true,
            "visualizer": { ...VisualizerOutputSchema... }
        }
    """
    try:
        raw_markdown = generate_visualizer(
            topic=request.topic,
            concept_type=request.concept_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Visualizer generation failed: {exc}")

    # Parse the markdown output into structured fields (best-effort)
    explanation = ""
    react_code = ""
    html_wrapper = ""

    lines = raw_markdown.splitlines()
    current_section = None

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Skip markdown headers that introduce sections
        if lower.startswith("###") or lower.startswith("##"):
            if "react" in lower or "jsx" in lower:
                current_section = "react"
                continue
            elif "html" in lower or "wrapper" in lower:
                current_section = "html"
                continue
            elif "explanation" in lower or "overview" in lower or "introduction" in lower:
                current_section = None
                continue
            else:
                # Generic header – treat it as explanation text if we're not inside a code block
                if not current_section:
                    explanation += stripped.lstrip("#").strip() + "\n"
                continue

        # Code fence boundaries
        if stripped.startswith("```"):
            if "jsx" in lower or "javascript" in lower or "react" in lower:
                current_section = "react"
                continue
            elif "html" in lower:
                current_section = "html"
                continue
            else:
                # End of a code block
                current_section = None
                continue
        elif stripped == "```":
            current_section = None
            continue

        if current_section == "react":
            react_code += line + "\n"
        elif current_section == "html":
            html_wrapper += line + "\n"
        elif not current_section and stripped and not stripped.startswith("#"):
            explanation += line + "\n"

    # Sanitise React code for browser Babel (remove ES-module syntax)
    react_code = _sanitize_react_code(react_code)

    # Build a standard HTML wrapper ourselves so we don't rely on the LLM
    # to inline the React code correctly.
    # The wrapper has a single <script type="text/babel"> placeholder; the
    # render call is appended to react_code so both share the same Babel
    # eval scope (Babel standalone wraps each script in "use strict", which
    # prevents const declarations from leaking across script blocks).
    standard_html_wrapper = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="UTF-8" />\n'
        '  <title>Visualizer</title>\n'
        '  <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>\n'
        '  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>\n'
        '  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>\n'
        '</head>\n'
        '<body>\n'
        '  <div id="root"></div>\n'
        '  <script type="text/babel" src="index.jsx"></script>\n'
        '</body>\n'
        '</html>'
    )

    # Ensure the React component is rendered as <App /> (remove default export)
    react_code = re.sub(r'export\s+default\s+\w+;?', '', react_code).strip()
    # Find the component name from "const ComponentName = () =>{" or "function ComponentName("
    # Skip bindings like "const ReactDOM = window.ReactDOM" that are not components.
    # We look for a PascalCase name that is NOT React or ReactDOM.
    component_match = re.search(
        r'(?:const|function)\s+((?!ReactDOM\b|React\b)[A-Z][A-Za-z0-9_]*)\s*[=\(]',
        react_code,
    )
    component_name = component_match.group(1) if component_match else "App"

    # Append the render call to react_code so it runs in the same Babel script scope.
    # Skip if the LLM already included a render call.
    if 'ReactDOM.createRoot' not in react_code and 'ReactDOM.render' not in react_code:
        react_code += (
            f'\n\nReactDOM.createRoot(document.getElementById("root")).render('
            f'<React.StrictMode><{component_name} /></React.StrictMode>);'
        )

    output = VisualizerOutputSchema(
        topic=request.topic,
        concept_type=request.concept_type,
        explanation=explanation.strip(),
        react_code=react_code.strip(),
        html_wrapper=standard_html_wrapper,
        generated_at=datetime.utcnow().isoformat() + "Z",
    )

    return {
        "success": True,
        "visualizer": output.model_dump(mode="json"),
    }


@app.post("/generate_test", response_model=dict)
async def generate_test_endpoint(
    topic: str,
    num_questions: int = 3,
    difficulty: str = None,
):
    """
    Generate a practice test for a given topic.

    Args:
        topic: The study task topic (e.g., "Loops", "Recursion", "Sorting").
        num_questions: Number of questions to generate (default 3).
        difficulty: Optional difficulty filter ("easy", "medium", "hard").

    Returns:
        {
            "success": true,
            "test": { ...TestSchema... }
        }
    """
    try:
        test: TestSchema = generate_test(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {exc}")

    return {
        "success": True,
        "test": test.model_dump(mode="json"),
    }


# ---------------------------------------------------------------------------
# Friend's UI endpoints (integrated)
# ---------------------------------------------------------------------------

@app.get("/get_missed_class_all")
def get_all_lectures(x_token: str = Header(default="")):
    """Return all lectures from the lectures database, optionally filtered by user courses."""
    try:
        lectures = _load_lectures()
        user = get_user_by_token(x_token)
        if user and user.get("courses"):
            user_course_names = {c["course_name"] for c in user["courses"]}
            lectures = [l for l in lectures if l.get("course_name") in user_course_names]
        return lectures
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Lectures database not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load lectures: {exc}")


@app.get("/get_missed_class/{course_name}/{date}")
def get_missed_class(course_name: str, date: str):
    """Return a specific lecture by course name and date."""
    try:
        lectures = _load_lectures()
        for lecture in lectures:
            if lecture.get("course_name") == course_name and lecture.get("lecture_date") == date:
                return {
                    "topic": lecture.get("topic"),
                    "content": lecture.get("content"),
                    "ai_question": lecture.get("ai_questions"),
                }
        raise HTTPException(status_code=404, detail="Lecture not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error loading lecture: {exc}")


@app.post("/tester/chat")
def tester_chat(request: TesterChatRequest):
    """
    Conversational comprehension-checking endpoint powered by chat_with_tester.

    The UI sends the full conversation history plus the topic and its content.
    Returns the assistant's next message.

    Request body:
        topic         — study topic name (e.g., "Recursion")
        topic_content — raw study material injected into the system prompt
        messages      — full conversation so far: [{"role": "user"|"assistant", "content": "..."}]

    Response:
        {"reply": "<assistant message>"}
    """
    try:
        reply = chat_with_tester(
            topic=request.topic,
            topic_content=request.topic_content,
            messages=request.messages,
        )
        return {"reply": reply}
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tester chat error: {exc}")


@app.post("/scrape_course")
async def scrape_course(request: ScrapeRequest):
    """
    Trigger scraping for a specific course number.
    Returns the scraped syllabus data.
    """
    try:
        from src.scraper.syllabus_scraper import get_course_syllabus
        result = get_course_syllabus(request.course_num, headless=True)
        return {"success": True, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {exc}")


@app.post("/chat")
def chat_with_tutor(request: ChatRequest):
    """
    AI tutor chat endpoint.
    Uses an OpenAI-compatible API (default: localhost:8080).
    Set OPENAI_BASE_URL and OPENAI_API_KEY env vars to override.
    """
    system_prompt = _load_tutor_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(request.history)
    messages.append({"role": "user", "content": request.user_message})

    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1")
    api_key = os.getenv("OPENAI_API_KEY", "none")
    model = os.getenv("TUTOR_MODEL", "ibm-granite/granite-3.3-8b-instruct-GGUF")

    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        ai_reply = response.choices[0].message.content
        return {"reply": ai_reply}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AI tutor error: {exc}")
