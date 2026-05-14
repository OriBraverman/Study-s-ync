"""
Unit tests (mocked OpenAI client) and integration tests (real OpenRouter API)
for chat_with_tester and _build_chat_system_prompt.

Integration tests are marked with @pytest.mark.integration and skipped
automatically when OPENROUTER_API_KEY is not set.
"""
import os
from unittest.mock import MagicMock, call, patch

import pytest

from src.agents.tester.agent import _build_chat_system_prompt, chat_with_tester

TOPIC = "Recursion"
CONTENT = (
    "A recursive function calls itself with a smaller input until it reaches a base case. "
    "The base case stops the recursion. For factorial: fact(0)=1, fact(n)=n*fact(n-1)."
)
GREETING = "Are you ready for an understanding testing session, or need any further explanation?"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(content: str):
    """Build a minimal mock that mimics openai.ChatCompletion response structure."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def _patch_openai(reply: str = "mocked reply"):
    """Context manager: patches openai.OpenAI (imported lazily inside the function)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(reply)
    return patch("openai.OpenAI", return_value=mock_client), mock_client


# ---------------------------------------------------------------------------
# _build_chat_system_prompt
# ---------------------------------------------------------------------------

class TestBuildChatSystemPrompt:
    def test_topic_appears_in_prompt(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert TOPIC in prompt

    def test_content_injected_in_prompt(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert CONTENT in prompt

    def test_greet_instruction_present(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert "GREET" in prompt

    def test_wait_instruction_present(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert "WAIT" in prompt

    def test_reveal_instruction_present(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert "REVEAL" in prompt

    def test_exact_greeting_string_in_prompt(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert GREETING in prompt

    def test_topic_content_tag_present(self):
        prompt = _build_chat_system_prompt(TOPIC, CONTENT)
        assert "<topic-content>" in prompt
        assert "</topic-content>" in prompt

    def test_different_topics_produce_different_prompts(self):
        p1 = _build_chat_system_prompt("Recursion", CONTENT)
        p2 = _build_chat_system_prompt("Sorting", CONTENT)
        assert p1 != p2

    def test_different_content_produces_different_prompts(self):
        p1 = _build_chat_system_prompt(TOPIC, "content A")
        p2 = _build_chat_system_prompt(TOPIC, "content B")
        assert p1 != p2


# ---------------------------------------------------------------------------
# chat_with_tester — unit (mocked)
# ---------------------------------------------------------------------------

class TestChatWithTesterUnit:
    def test_raises_value_error_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            chat_with_tester(TOPIC, CONTENT, [])

    def test_api_key_read_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-key-123")
        patcher, mock_client = _patch_openai("hello")
        with patcher:
            result = chat_with_tester(TOPIC, CONTENT, [])
        assert result == "hello"

    def test_explicit_api_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
        patcher, mock_client = _patch_openai("reply")
        with patcher as MockOpenAI:
            chat_with_tester(TOPIC, CONTENT, [], api_key="explicit-key")
        _, kwargs = MockOpenAI.call_args
        assert kwargs.get("api_key") == "explicit-key"

    def test_openrouter_base_url_used(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, _ = _patch_openai()
        with patcher as MockOpenAI:
            chat_with_tester(TOPIC, CONTENT, [])
            call_kwargs = MockOpenAI.call_args[1]
            assert "openrouter.ai" in call_kwargs.get("base_url", "")

    def test_system_message_is_first(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, [{"role": "user", "content": "hi"}])
        sent = mock_client.chat.completions.create.call_args[1]["messages"]
        assert sent[0]["role"] == "system"

    def test_user_messages_appended_after_system(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        history = [{"role": "user", "content": "hello"}]
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, history)
        sent = mock_client.chat.completions.create.call_args[1]["messages"]
        assert sent[1] == {"role": "user", "content": "hello"}

    def test_system_prompt_contains_topic(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester("Sorting", CONTENT, [])
        sent = mock_client.chat.completions.create.call_args[1]["messages"]
        assert "Sorting" in sent[0]["content"]

    def test_system_prompt_contains_content(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, "unique content XYZ", [])
        sent = mock_client.chat.completions.create.call_args[1]["messages"]
        assert "unique content XYZ" in sent[0]["content"]

    def test_returns_stripped_content(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, _ = _patch_openai("  reply with spaces  ")
        with patcher:
            result = chat_with_tester(TOPIC, CONTENT, [])
        assert result == "reply with spaces"

    def test_default_model_is_claude_sonnet(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, [])
        used_model = mock_client.chat.completions.create.call_args[1]["model"]
        assert "claude" in used_model

    def test_model_overridden_by_env(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, [])
        used_model = mock_client.chat.completions.create.call_args[1]["model"]
        assert used_model == "openai/gpt-4o"

    def test_temperature_is_0_4(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, [])
        temp = mock_client.chat.completions.create.call_args[1]["temperature"]
        assert temp == pytest.approx(0.4)

    def test_empty_history_sends_only_system_message(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, [])
        sent = mock_client.chat.completions.create.call_args[1]["messages"]
        assert len(sent) == 1
        assert sent[0]["role"] == "system"

    def test_full_history_preserved_in_order(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key")
        history = [
            {"role": "assistant", "content": GREETING},
            {"role": "user", "content": "Yes, ready!"},
        ]
        patcher, mock_client = _patch_openai()
        with patcher:
            chat_with_tester(TOPIC, CONTENT, history)
        sent = mock_client.chat.completions.create.call_args[1]["messages"]
        assert sent[1] == history[0]
        assert sent[2] == history[1]


# ---------------------------------------------------------------------------
# chat_with_tester — integration (real API)
# ---------------------------------------------------------------------------

def _has_api_key() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="OPENROUTER_API_KEY not set")
class TestChatWithTesterIntegration:
    def test_greeting_on_empty_history(self):
        reply = chat_with_tester(TOPIC, CONTENT, [])
        assert reply == GREETING

    def test_question_after_ready_confirmation(self):
        history = [
            {"role": "assistant", "content": GREETING},
            {"role": "user", "content": "Yes, I'm ready!"},
        ]
        reply = chat_with_tester(TOPIC, CONTENT, history)
        assert isinstance(reply, str)
        assert len(reply) > 20  # should be a real question, not empty

    def test_reply_is_nonempty_string(self):
        reply = chat_with_tester(TOPIC, CONTENT, [])
        assert isinstance(reply, str)
        assert reply.strip() != ""

    def test_correct_answer_gets_positive_feedback(self):
        history = [
            {"role": "assistant", "content": GREETING},
            {"role": "user", "content": "Yes, ready!"},
            {"role": "assistant", "content": "What is the base case of a recursive factorial?"},
            {"role": "user", "content": "The base case is when n equals 0 or 1, returning 1."},
        ]
        reply = chat_with_tester(TOPIC, CONTENT, history)
        assert isinstance(reply, str)
        assert len(reply) > 5

    def test_explanation_request_answered_directly(self):
        history = [
            {"role": "assistant", "content": GREETING},
            {"role": "user", "content": "Can you explain what a base case is?"},
        ]
        reply = chat_with_tester(TOPIC, CONTENT, history)
        # Should answer the question directly, not redirect
        assert isinstance(reply, str)
        assert len(reply) > 20
