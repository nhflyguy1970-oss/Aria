"""Tests for upgrade-roadmap extras (lang, session model, podcast mix)."""

from jarvis.lang_util import detect_text_language, language_reply_hint
from jarvis.session import SessionContext


def test_detect_text_language_cjk():
    assert detect_text_language("今天天气怎么样请问") == "zh"


def test_detect_text_language_english_none():
    assert detect_text_language("hello how are you today") is None


def test_language_reply_hint():
    assert "Chinese" in language_reply_hint("zh")
    assert language_reply_hint("en") == ""


def test_session_chat_model_round_trip():
    s = SessionContext(chat_model="qwen2.5:7b")
    restored = SessionContext.from_dict(s.to_dict())
    assert restored.chat_model == "qwen2.5:7b"
