# Project Plan: Academic Bridge AI (Hackathon MVP)

## General Overview
Building a personalized learning platform for engineering students to close academic gaps.
**Demo Focus:** Computer Architecture — Pipelining and Data Hazards in MIPS processors.
**Current Reality:** The backend multi-agent system is fully operational for any CS course with a BIU syllabus.

---

## Milestones & Task Breakdown

### Phase 1: Infrastructure & Setup ✅
- [x] **Repository Setup:** Initialize GitHub Repo, select Tech Stack (React/Next.js + Tailwind CSS for future frontend; Streamlit + FastAPI for MVP).
- [x] **Mock Database:** Create `data.json` containing mappings between dates, syllabus topics, and content.
  - *Evolved into:* `data/raw/syllabuses.json` + `data/mock_cs_drive/` + ChromaDB vector store.
- [x] **Environment Setup:** Configure environment variables and connect API keys for AI (Gemini/OpenAI).
  - *Implemented:* `USE_MOCK_LLM` toggle + `OPENAI_API_KEY` support in planner.

### Phase 2: Core Components Development (Frontend) 🔹
- [ ] **Website UI:** Input form for missed lectures, course selection, academic year, and dates.
  - *Assigned to:* Another team member (React/Next.js).
- [x] **Simulation Component:** Build the visual Pipelining component.
  - *Delivered:* **Visualizer Agent** (`src/agents/visualizer/`) generates interactive React components for any topic.
  - [x] Display the 5 stages: IF, ID, EX, MEM, WB.
  - [x] Implement "Step-by-step" command execution and highlight conflicts (Hazards) in red.

### Phase 3: AI Teacher Integration (Backend/AI) ✅
- [x] **Planner Agent:** Define the AI Teacher prompt and study plan generation.
  - *Delivered:* `src/agents/planner/` — unified agent that analyzes, prunes, retrieves, and plans.
- [x] **Context Injection:** Inject the current simulation state into the prompt so the bot understands which Hazard the student is viewing.
  - *Delivered:* Retrieved chunks injected into the planner prompt.
- [x] **Test Generation:** Create practice quizzes per topic.
  - *Delivered:* **Tester Agent** (`src/agents/tester/`) with multiple-choice, short-answer, and code-tracing questions.

### Phase 4: Integration & Polishing ✅ / 🔹
- [x] **Full Flow Integration:** Connect the input form to the learning screen and sync data between the simulation and the chat.
  - *Delivered:* End-to-end LangGraph pipeline (`src/orchestration/graph.py`) for the Planner Agent.
- [ ] **UI/UX Polish:** Add subtle animations for Pipeline transitions and improve overall UI aesthetics.
  - *Plan:* Main website by another team member; Streamlit is temporary.
- [ ] **Final Bug Fixes:** Test edge cases and prepare the environment for the final demo.

---

## System Architecture (High-Level)

| Component | Responsibility |
| :--- | :--- |
| **Website (React/Next.js)** | User-facing interface: form input, plan display, simulation embedding, test taking. |
| **FastAPI Backend** | API gateway for the three agents. |
| **Planner Agent** | Analyzes missed topics, retrieves material, generates study plan. |
| **Visualizer Agent** | Generates interactive React simulations for complex topics. |
| **Tester Agent** | Generates practice tests and quizzes per topic. |
| **Mock DB (JSON + ChromaDB)** | Mapping `Date -> Topic` + vector search over course materials. |

---

## Backend Agent Architecture

```text
┌─────────────────┐
│  Website UI     │
│  (React/Next.js)│  (another team member)
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────────────────────────┐
│           FastAPI Backend                   │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐ │
│  │/generate│   │/generate │   │/generate│ │
│  │_bootcamp│   │_visualizer  │_test    │ │
│  └────┬────┘   └────┬─────┘   └────┬────┘ │
│       │             │              │      │
│       ▼             ▼              ▼      │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐│
│  │ Planner │   │Visualizer│   │ Tester  ││
│  │ Agent   │   │ Agent    │   │ Agent   ││
│  │         │   │          │   │         ││
│  │Internal:│   │React     │   │Questions││
│  │Analyzer │   │Components│   │+Answers ││
│  │->Pruner │   │          │   │         ││
│  │->Retriever│ │          │   │         ││
│  │->Planner│   │          │   │         ││
│  └─────────┘   └──────────┘   └─────────┘│
└─────────────────────────────────────────────┘
```

---

## Demo Scenario (The "Happy Path")
1. **Input:** Student selects "Computer Architecture" and the date Pipelining was taught.
2. **Planner:** System displays a brief explanation of Data Dependency and a day-by-day study plan.
3. **Visualizer:** Student opens the MIPS Pipeline simulation and sees the 5 stages. They step through instructions and see a Hazard caused by register access before writing.
4. **Tester:** Student takes a 3-question quiz on Pipeline Hazards to verify understanding.
5. **AI:** The bot initiates a conversation: "What do you think happened here that caused a delay? Is there a way to pass the information faster?"
6. **Outcome:** Student proposes a solution, the bot confirms and explains the Forwarding principle.

---

## Out of Scope (For Future Versions)
- [ ] User Login and authentication system.
- [ ] PDF Syllabus scanning (Mock data usage only).
- [ ] Developing simulations for additional courses beyond Architecture.
- [ ] Real-time collaborative editing of bootcamp plans.
