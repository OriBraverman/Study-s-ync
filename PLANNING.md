
# 🚀 Project Plan: Academic Bridge AI (Hackathon MVP)

## 📋 General Overview
Building a personalized learning platform for engineering students to close academic gaps.
**Demo Focus:** Computer Architecture - Pipelining and Data Hazards in MIPS processors.

---

## 🛠 Milestones & Task Breakdown

### Phase 1: Infrastructure & Setup 
- [ ] **Repository Setup:** Initialize GitHub Repo, select Tech Stack (React/Next.js + Tailwind CSS).
- [ ] **Mock Database:** Create `data.json` containing mappings between dates, syllabus topics, and content.
- [ ] **Environment Setup:** Configure environment variables and connect API keys for AI (Gemini/OpenAI).

### Phase 2: Core Components Development (Frontend) 
- [ ] **Landing Page:** Build a simple input form for course selection and missed dates.
- [ ] **Learning Dashboard:** Layout the learning page including text summaries, simulation area, and chat panel.
- [ ] **Simulation Component:** Build the visual Pipelining component.
    - [ ] Display the 5 stages: IF, ID, EX, MEM, WB.
    - [ ] Implement "Step-by-step" command execution and highlight conflicts (Hazards) in red.

### Phase 3: AI Teacher Integration (Backend/AI) 
- [ ] **System Prompt Engineering:** Define the AI Teacher prompt (patient, asking guiding questions, guiding toward solutions without giving immediate answers).
- [ ] **Chat Interface:** Build the chat UI that communicates with the API and displays message history.
- [ ] **Context Injection:** Inject the current simulation state into the prompt so the bot understands which Hazard the student is viewing.

### Phase 4: Integration & Polishing 
- [ ] **Full Flow Integration:** Connect the input form to the learning screen and sync data between the simulation and the chat.
- [ ] **UI/UX Polish:** Add subtle animations for Pipeline transitions and improve overall UI aesthetics.
- [ ] **Final Bug Fixes:** Test edge cases and prepare the environment for the final demo.

---

##  System Architecture (High-Level)

| Component | Responsibility |
| :--- | :--- |
| **Frontend (React)** | State management for the simulation, interactive UI, and chat handling. |
| **Mock DB (JSON)** | Mapping `Date -> Topic` (e.g., May 14th -> Data Hazards). |
| **AI Controller** | Mediating between user actions in the simulation and the LLM. |

---

## Demo Scenario (The "Happy Path")
1. **Input:** Student selects "Computer Architecture" and the date Pipelining was taught.
2. **Content:** System displays a brief explanation of Data Dependency.
3. **Interaction:** Student runs commands in the simulation and sees a Hazard caused by register access before writing.
4. **AI:** The bot initiates a conversation: "What do you think happened here that caused a delay? Is there a way to pass the information faster?"
5. **Outcome:** Student proposes a solution, the bot confirms and explains the Forwarding principle.

---

##  Out of Scope (For Future Versions)
- [ ] User Login and authentication system.
- [ ] PDF Syllabus scanning (Mock data usage only).
- [ ] Developing simulations for additional courses beyond Architecture.
GITHUB_PLANNING_EN.md
הפריט GITHUB_PLANNING_EN.md מוצג.