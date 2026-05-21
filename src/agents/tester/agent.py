"""
Study[S]ync Tester Agent

Generates quizzes, tests, and practice exams for a given study topic.
Helps students verify their understanding of missed material.
"""
import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv

from src.schemas.models import (
    QuestionSchema,
    TestSchema,
)

load_dotenv()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an Expert Computer Science Educator & Exam Writer.
Your mission is to create high-quality practice questions for university
computer science topics.

Rules:
- Generate multiple-choice, short-answer, and code-tracing questions.
- Each question must test a specific concept (not just trivia).
- Provide the correct answer and a brief explanation.
- Adjust difficulty based on the topic complexity.
- Output valid JSON only — no markdown fences, no extra text.

Output JSON Structure:
{
  "questions": [
    {
      "question_type": "multiple_choice|short_answer|code_tracing",
      "question_text": "string",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "string",
      "explanation": "string",
      "difficulty": "easy|medium|hard",
      "topic": "string"
    }
  ]
}
"""

# ---------------------------------------------------------------------------
# Mock data for default mode
# ---------------------------------------------------------------------------

MOCK_QUESTIONS = {
    "functions": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="What is the output of the following Python code?\ndef double_val(x):\n    x = x * 2\n\nval = 5\ndouble_val(val)\nprint(val)",
            options=["A. 5", "B. 10", "C. None", "D. Error"],
            correct_answer="A. 5",
            explanation="In Python, arguments are passed by assignment. Since integers are immutable, the variable 'val' outside the function remains unchanged (5).",
            difficulty="easy",
            topic="Functions",
        ),
        QuestionSchema(
            question_type="code_tracing",
            question_text="Trace this function execution:\ndef add_suffix(s):\n    return s + '!'\n\ndef greet(name):\n    return 'Hello ' + add_suffix(name)\n\nprint(greet('student'))",
            options=["A. Hello student", "B. Hello student!", "C. Hello !", "D. Error"],
            correct_answer="B. Hello student!",
            explanation="greet('student') calls add_suffix('student') which returns 'student!'. greet then returns 'Hello ' + 'student!' which is 'Hello student!'.",
            difficulty="easy",
            topic="Functions",
        ),
    ],
    "loops": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="What is the output of the following Python loop?\nfor i in range(3):\n    print(i)",
            options=["A. 1 2 3", "B. 0 1 2", "C. 0 1 2 3", "D. Error"],
            correct_answer="B. 0 1 2",
            explanation="range(3) generates 0, 1, 2. The loop prints each value.",
            difficulty="easy",
            topic="Loops",
        ),
        QuestionSchema(
            question_type="code_tracing",
            question_text="Trace this loop:\narr = [3, 1, 4]\nfor i in range(len(arr)):\n    arr[i] = arr[i] * 2\nWhat is arr after the loop?",
            options=["A. [3, 1, 4]", "B. [6, 2, 8]", "C. [3, 2, 4]", "D. Error"],
            correct_answer="B. [6, 2, 8]",
            explanation="Each element is multiplied by 2: 3*2=6, 1*2=2, 4*2=8.",
            difficulty="easy",
            topic="Loops",
        ),
    ],
    "recursion": [
        QuestionSchema(
            question_type="short_answer",
            question_text="What is the base case in a recursive factorial function?",
            options=[],
            correct_answer="n <= 1 (or n == 0, returning 1)",
            explanation="The base case stops the recursion. For factorial, it's when n reaches 0 or 1.",
            difficulty="medium",
            topic="Recursion",
        ),
        QuestionSchema(
            question_type="code_tracing",
            question_text="What is the result of fib(4) where fib(n) = fib(n-1) + fib(n-2) with base cases fib(0)=0, fib(1)=1?",
            options=["A. 2", "B. 3", "C. 5", "D. 8"],
            correct_answer="B. 3",
            explanation="fib(4) = fib(3) + fib(2) = (fib(2)+fib(1)) + (fib(1)+fib(0)) = (1+1) + (1+0) = 3.",
            difficulty="medium",
            topic="Recursion",
        ),
    ],
    "sorting": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="What is the worst-case time complexity of Bubble Sort?",
            options=["A. O(n)", "B. O(n log n)", "C. O(n²)", "D. O(2ⁿ)"],
            correct_answer="C. O(n²)",
            explanation="Bubble Sort compares and swaps adjacent elements repeatedly, leading to O(n²) in the worst case.",
            difficulty="easy",
            topic="Sorting",
        ),
    ],
    "graphs": [
        QuestionSchema(
            question_type="multiple_choice",
            question_text="Which data structure is typically used in Breadth-First Search (BFS)?",
            options=["A. Stack", "B. Queue", "C. Heap", "D. Priority Queue"],
            correct_answer="B. Queue",
            explanation="BFS explores nodes level by level, using a queue to track the frontier.",
            difficulty="easy",
            topic="Graphs",
        ),
    ],
}


def _topic_to_key(topic: str) -> str:
    """Map a topic string to a mock question bank key."""
    t = topic.lower()
    if any(k in t for k in ["loop", "לולאה", "iteration"]):
        return "loops"
    if any(k in t for k in ["recursion", "רקורסיה", "recursive"]):
        return "recursion"
    if any(k in t for k in ["sort", "מיון", "bubble", "merge", "quick"]):
        return "sorting"
    if any(k in t for k in ["graph", "גרף", "bfs", "dfs"]):
        return "graphs"
    if any(k in t for k in ["function", "פונקצי", "def "]):
        return "functions"
    return "loops"  # default fallback


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def generate_test(
    topic: str,
    num_questions: int = 3,
    difficulty: Optional[str] = None,
    api_key: Optional[str] = None,
) -> TestSchema:
    """
    Generate a practice test for the given topic.

    Args:
        topic: The study task topic (e.g., "Loops", "Recursion", "Sorting").
        num_questions: Number of questions to generate.
        difficulty: Optional difficulty filter ("easy", "medium", "hard").
        api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.

    Returns:
        TestSchema containing the list of questions.
    """
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    if use_mock:
        key = _topic_to_key(topic)
        questions = MOCK_QUESTIONS.get(key, MOCK_QUESTIONS["loops"])[:num_questions]
        return TestSchema(
            topic=topic,
            questions=questions,
            total_questions=len(questions),
            estimated_minutes=len(questions) * 5,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

    # Real LLM generation with Gemini
    gemini_key = api_key or os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = os.getenv("TUTOR_MODEL", "gemini-2.5-flash")
            client = ChatGoogleGenerativeAI(model=model_name, google_api_key=gemini_key, temperature=0.3)
            user_prompt = f"""
Generate {num_questions} practice questions for the topic: {topic}.
Difficulty preference: {difficulty or "mixed"}.
Output only valid JSON matching the specified structure.
"""
            response = client.invoke([
                ("system", SYSTEM_PROMPT),
                ("human", user_prompt)
            ])
            raw = response.content.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()

            import json
            data = json.loads(raw)
            questions = []
            for q in data.get("questions", []):
                questions.append(
                    QuestionSchema(
                        question_type=q.get("question_type", "multiple_choice"),
                        question_text=q.get("question_text", ""),
                        options=q.get("options", []),
                        correct_answer=q.get("correct_answer", ""),
                        explanation=q.get("explanation", ""),
                        difficulty=q.get("difficulty", "medium"),
                        topic=topic,
                    )
                )
            return TestSchema(
                topic=topic,
                questions=questions,
                total_questions=len(questions),
                estimated_minutes=len(questions) * 5,
                generated_at=datetime.utcnow().isoformat() + "Z",
            )
        except Exception:
            pass

    # Fallback to OpenRouter (original behavior)
    openrouter_key = api_key or os.getenv("OPENROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not openrouter_key:
        # Final fallback to mock if no keys are found
        return generate_test(topic, num_questions, difficulty, api_key=None)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openrouter_key)
        user_prompt = f"""
Generate {num_questions} practice questions for the topic: {topic}.
Difficulty preference: {difficulty or "mixed"}.
Output only valid JSON matching the specified structure.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])

        import json
        data = json.loads(raw)
        questions = []
        for q in data.get("questions", []):
            questions.append(
                QuestionSchema(
                    question_type=q.get("question_type", "multiple_choice"),
                    question_text=q.get("question_text", ""),
                    options=q.get("options", []),
                    correct_answer=q.get("correct_answer", ""),
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", "medium"),
                    topic=topic,
                )
            )
        return TestSchema(
            topic=topic,
            questions=questions,
            total_questions=len(questions),
            estimated_minutes=len(questions) * 5,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
    except Exception:
        # Fallback to mock
        return generate_test(topic, num_questions, difficulty, api_key=None)


# ---------------------------------------------------------------------------
# Chat agent (ported from Ofek educational chatbot)
# ---------------------------------------------------------------------------

def _build_chat_system_prompt(topic: str, topic_content: str) -> str:
    return f"""אתה עוזר AI חינוכי שעוזר לסטודנט ללמוד את הנושא: "{topic}".

שפת התקשורת: עברית בלבד. ענה תמיד בעברית, גם אם הסטודנט כותב באנגלית.

נוסחאות מתמטיות: השתמש ב-LaTeX לכתיבת סמלים ונוסחאות מתמטיות.
- נוסחאות בתוך שורה: $...$ (לדוגמה: $O(n^2)$, $f(n) = n \\cdot f(n-1)$)
- נוסחאות בשורה נפרדת: $$...$$ (לדוגמה: $$T(n) = 2T(n/2) + O(n)$$)

להלן תוכן החומר שהסטודנט לומד:

<topic-content>
{topic_content}
</topic-content>

תפקידיך — פעל לפי הסדר הבא:
1. פתיחה: ההודעה הראשונה שלך חייבת להיות בדיוק: "האם אתה מוכן לסשן בדיקת הבנה, או שאתה זקוק להסבר נוסף?"
   אל תסכם ואל תשאל שאלות בשלב זה.
2. המתנה: רק לאחר שהסטודנט מאשר שהוא מוכן, התחל את הסשן.
3. בדיקה: שאל 1–2 שאלות הבנה ממוקדות על התוכן שלמעלה. מושג אחד בכל פעם.
4. הערכה: אם התשובה נכונה, אשר זאת ועבור למושג הבא.
   אם התשובה שגויה או חלקית, הסבר את המושג בבירור תוך שימוש בתוכן שלמעלה, והוסף [חזור-לתוכן] בסוף תגובתך.
5. חשיפה: אל תחשוף את התשובה אלא אם הסטודנט מבקש זאת במפורש.

חשוב — שאלות ובקשות הסטודנט:
- אם הסטודנט שואל שאלה או מבקש הסבר, ענה עליה מיד ובמלואה.
- אל תפנה אותו חזרה לשאלתך הקודמת. לאחר המענה, הצע להמשיך באופן טבעי.
- התייחס לכל שאלה או בקשת הסבר כהבהרה, לא כניסיון לענות."""


def _mock_chat_response(topic: str, messages: List[dict]) -> str:
    """
    Rule-based mock for chat_with_tester.
    Conversation shape (message list passed in):
      []                                       → opening greeting
      [assistant, user]                        → ask Q1
      [assistant, user, assistant, user]       → evaluate Q1, ask Q2
      ...after last question wraps to Q1 again with a new-round notice.
    """
    if not messages:
        return "האם אתה מוכן לסשן בדיקת הבנה, או שאתה זקוק להסבר נוסף?"

    # Use MOCK_QUESTIONS directly to avoid calling generate_test, which
    # can infinitely recurse when USE_MOCK_LLM=false and no OPENAI_API_KEY.
    mock_key = _topic_to_key(topic)
    questions = MOCK_QUESTIONS.get(mock_key, MOCK_QUESTIONS["loops"])[:3]
    if not questions:
        return f"אין שאלות זמינות לנושא {topic}."
    n = len(questions)

    def _fmt(idx: int) -> str:
        q = questions[idx]
        text = f"שאלה {idx + 1}:\n\n{q.question_text}"
        if q.options:
            text += "\n\n" + "\n".join(q.options)
        return text

    # messages == [greeting, user_ready] → ask Q1
    if len(messages) == 2:
        return "מצוין! " + _fmt(0)

    # prev_q_idx: index (in questions list) of the question the user just answered
    # Formula: after greeting+ready (2 msgs), each Q&A pair adds 2 msgs.
    prev_q_idx = (len(messages) - 4) // 2  # 0 when len=4, 1 when len=6, …
    answered_total = (len(messages) - 4) // 2  # same, kept for clarity
    prev_q = questions[prev_q_idx % n]

    last_user = messages[-1]["content"].lower()
    correct_lower = prev_q.correct_answer.lower()
    is_correct = any(w in last_user for w in correct_lower.split() if len(w) > 2)

    feedback = f"נכון מאוד! {prev_q.explanation}\n\n" if is_correct \
               else f"לא בדיוק. {prev_q.explanation} [חזור-לתוכן]\n\n"

    next_idx = answered_total + 1      # absolute question counter (never wraps)
    next_in_round = next_idx % n       # which question inside current round

    # Completed a round → add transition message
    if next_idx % n == 0:
        feedback += "כל הכבוד על סיום הסבב! בוא נמשיך לתרגל:\n\n"

    return feedback + _fmt(next_in_round)


def chat_with_tester(
    topic: str,
    topic_content: str,
    messages: List[dict],
    api_key: Optional[str] = None,
) -> str:
    """
    Conduct a conversational comprehension-checking session on a topic.

    Args:
        topic: The study topic (e.g., "Recursion", "BFS").
        topic_content: The raw study material/notes for the topic (injected into system prompt).
        messages: Conversation history as [{"role": "user"|"assistant", "content": "..."}].
        api_key: API key. Falls back to GEMINI_API_KEY or OPENROUTER_API_KEY.

    Returns:
        The assistant's next message as a plain string.
    """
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
    gemini_key = api_key or os.getenv("GEMINI_API_KEY", "")
    openrouter_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    # If mock mode is forced, or if no API keys are configured, fallback to mock response
    if use_mock or (not gemini_key and not openrouter_key):
        return _mock_chat_response(topic, messages)

    # Prefer Gemini API
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

            system_prompt = _build_chat_system_prompt(topic, topic_content)
            formatted_messages = [SystemMessage(content=system_prompt)]
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    formatted_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    formatted_messages.append(AIMessage(content=content))

            model_name = os.getenv("TUTOR_MODEL", "gemini-2.5-flash")
            client = ChatGoogleGenerativeAI(model=model_name, google_api_key=gemini_key, temperature=0.4)
            response = client.invoke(formatted_messages)
            return response.content.strip()
        except Exception:
            if not openrouter_key:
                return _mock_chat_response(topic, messages)

    # Fallback to OpenRouter
    if openrouter_key:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")
        system_prompt = _build_chat_system_prompt(topic, topic_content)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, *messages],
                temperature=0.4,
                max_tokens=2048,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return _mock_chat_response(topic, messages)

    return _mock_chat_response(topic, messages)


if __name__ == "__main__":
    test = generate_test("Recursion and base cases", num_questions=2)
    print(f"Generated test for: {test.topic}")
    for q in test.questions:
        print(f"\n[{q.difficulty.upper()}] {q.question_type}: {q.question_text}")
        if q.options:
            for opt in q.options:
                print(f"  {opt}")
        print(f"Answer: {q.correct_answer}")
        print(f"Explanation: {q.explanation}")

    print("\n--- Chat Demo ---")
    sample_content = (
        "A recursive function calls itself with a smaller input until it reaches a base case. "
        "The base case stops the recursion. For factorial: fact(0) = 1, fact(n) = n * fact(n-1)."
    )
    history: List[dict] = []
    reply = chat_with_tester("Recursion", sample_content, history)
    print(f"Agent: {reply}")
    history.append({"role": "assistant", "content": reply})
    history.append({"role": "user", "content": "כן, אני מוכן!"})
    reply = chat_with_tester("Recursion", sample_content, history)
    print(f"User: כן, אני מוכן!")
    print(f"Agent: {reply}")
