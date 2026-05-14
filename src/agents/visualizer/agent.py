r"""
Study[S]ync Visualizer Agent

Translates a study task topic into a self-contained, interactive React
visualization component that students can run directly in the browser.

Inspired by VisoAgent (C:\src\apps\VisoAgent).
"""
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv()

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an Expert React Developer & Educational Tooling Specialist.
Your mission is to translate a student's topic or concept into a fully
functional, interactive React visualizer component that can be embedded
into a standard HTML website.

Follow these steps strictly:
1. Concept Extraction & Analysis: Identify the primary algorithm/concept and
determine the visualization strategy.
2. Component Design & UI/UX: Layout the visualization area, controls
(Play/Pause, Step, Reset, Speed), and basic color coding.
3. Code Generation (React): Generate a stand-alone React functional component
using Hooks and inline styles/standard CSS. No external arbitrary dependencies.
4. HTML Integration Guide: Provide the exact HTML boilerplate, including
React/Babel CDNs to load the component directly.

Strict Constraints:
- No Placeholders: Complete working code only.
- Safety First: Avoid infinite loops or blocking operations.
- Accessibility: Provide basic ARIA labels.
- Tone: Encouraging, educational, and brief.

Output Structure:
1. Brief Encouragement & Explanation
2. The React Code (index.jsx)
3. The HTML Wrapper (index.html)
"""

MOCK_RESPONSE = """
## Visualizer Ready!

I've prepared a conceptual bubble-sort visualizer for you.

### React Code (index.jsx)
```jsx
import React, { useState, useEffect, useCallback } from 'react';

const BubbleSortVisualizer = () => {
  const [array, setArray] = useState([5, 3, 8, 4, 2]);
  const [isSorting, setIsSorting] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(-1);

  const reset = () => {
    setArray([5, 3, 8, 4, 2]);
    setIsSorting(false);
    setCurrentIdx(-1);
  };

  const stepSort = useCallback(() => {
    setArray((prev) => {
      const arr = [...prev];
      for (let i = 0; i < arr.length - 1; i++) {
        if (arr[i] > arr[i + 1]) {
          [arr[i], arr[i + 1]] = [arr[i + 1], arr[i]];
          setCurrentIdx(i);
          return arr;
        }
      }
      setIsSorting(false);
      return arr;
    });
  }, []);

  useEffect(() => {
    if (!isSorting) return;
    const timer = setTimeout(stepSort, 500);
    return () => clearTimeout(timer);
  }, [array, isSorting, stepSort]);

  return (
    <div style={{ fontFamily: 'sans-serif', padding: 20 }}>
      <h2>Bubble Sort Visualizer</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {array.map((val, idx) => (
          <div
            key={idx}
            style={{
              width: 40,
              height: val * 20 + 20,
              background: idx === currentIdx || idx === currentIdx + 1 ? '#f39c12' : '#3498db',
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'center',
              color: '#fff',
              borderRadius: 4,
              transition: 'background 0.3s',
            }}
            aria-label={`Bar value ${val}`}
          >
            {val}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => setIsSorting(true)} aria-label="Play">▶️ Play</button>
        <button onClick={() => setIsSorting(false)} aria-label="Pause">⏸️ Pause</button>
        <button onClick={stepSort} aria-label="Step">⏭️ Step</button>
        <button onClick={reset} aria-label="Reset">🔄 Reset</button>
      </div>
    </div>
  );
};

export default BubbleSortVisualizer;
```

### HTML Wrapper (index.html)
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Visualizer</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel" src="index.jsx"></script>
  <script type="text/babel">
    ReactDOM.createRoot(document.getElementById('root')).render(
      <React.StrictMode>
        <BubbleSortVisualizer />
      </React.StrictMode>
    );
  </script>
</body>
</html>
```
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def generate_visualizer(
    topic: str,
    concept_type: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Generate a React visualizer for the given topic.

    Args:
        topic: The study task topic (e.g., "Bubble Sort", "Pipeline Hazards").
        concept_type: Optional hint (e.g., "sorting", "cpu_pipeline", "graph").
        api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.

    Returns:
        Markdown string containing the React code and HTML wrapper.
    """
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    if use_mock:
        return MOCK_RESPONSE

    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        return MOCK_RESPONSE

    try:
        from openai import OpenAI
    except ImportError:
        return MOCK_RESPONSE

    client = OpenAI(api_key=key)

    user_prompt = f"""
Topic: {topic}
Concept type hint: {concept_type or "auto-detect"}

Generate a fully functional, interactive React visualizer for this concept.
Follow the output structure exactly.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to visualizer agent: {str(e)}"


if __name__ == "__main__":
    test_query = "hi chat i have a problem I dont understand about a bubble sort"
    print(f"User: {test_query}\n")
    print("Agent Response:")
    print(generate_visualizer(test_query))
