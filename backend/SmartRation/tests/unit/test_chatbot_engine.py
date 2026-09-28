"""Public Help assistant: retrieval quality in en/hi/mr, safety rules, and knowledge-base integrity."""

from __future__ import annotations

import json
import shutil

import pytest
from py_testkit import REPO_ROOT

from app.ai.chatbot.engine import Assistant
from app.ai.chatbot.knowledge_base import KNOWLEDGE_DIR, LANGUAGES, KnowledgeError, load
from app.ai.chatbot.text import detect_language, normalize


class StubData:
    def shops(self):
        return [
            {"name": "Koradi Ration Shop", "address": "Station Road, Koradi", "village": "Koradi", "taluka": "Kamptee", "district": "Nagpur"},
            {"name": "Hingna Ration Shop", "address": "Main Road, Hingna", "village": "Hingna", "taluka": "Hingna", "district": "Nagpur"},
        ]

    def schemes(self):
        return [{"code": "DEMO-NFSA", "name": "Demo National Food Security Scheme",
                 "items": [{"name": "Rice", "vernacular": "Tandul", "unit": "kg", "quota": "5.000000"},
                           {"name": "Edible Oil", "vernacular": "Tel", "unit": "L", "quota": "0.500"}]}]


@pytest.fixture(scope="module")
def bot() -> Assistant:
    return Assistant(load())


# The evaluation set lives with the AI assets: <repo>/ai/chatbot/evaluation/questions.json
EVALUATION = json.loads((REPO_ROOT / "ai" / "chatbot" / "evaluation" / "questions.json").read_text(encoding="utf-8"))
QUESTIONS = [(c["message"], c["language"], c["expected_article"]) for c in EVALUATION["answers"]]
SAFETY = [(c["message"], c["language"], c["expected_kind"]) for c in EVALUATION["safety"]]


@pytest.mark.parametrize("message,language,expected", QUESTIONS)
def test_questions_find_the_right_article(bot, message, language, expected):
    reply = bot.reply(message, language, StubData())
    assert (reply.kind, reply.article_id) == ("answer", expected)


@pytest.mark.parametrize("message,language,kind", SAFETY)
def test_safety_and_conversation_rules(bot, message, language, kind):
    assert bot.reply(message, language, StubData()).kind == kind


def test_sensitive_and_private_replies_never_echo_the_message(bot):
    for message in ("my aadhaar is 1234 5678 9012", "What is my token?", "the otp is 482913"):
        reply = bot.reply(message, "en", StubData())
        assert "1234" not in reply.text and "482913" not in reply.text
    private = bot.reply("What is my token?", "en", StubData())
    assert private.requires_login and private.links == [{"path": "/login", "label": "Log in securely"}]


def test_health_reply_is_guidance_not_diagnosis(bot):
    text = bot.reply("my child has fever", "en").text
    assert "can't give medical advice" in text and "112" in text and "108" in text


def test_replies_follow_the_language(bot):
    assert bot.reply("How can I apply for a ration card?", "hi").text.startswith("राशन कार्ड राज्य सरकार")
    assert bot.reply("How can I apply for a ration card?", "mr").text.startswith("रेशन कार्ड राज्य सरकार")


def test_language_detection():
    assert detect_language("How to apply", "hi") == "hi"            # the user's chosen UI language wins for Latin text
    assert detect_language("रेशन कार्ड कसे काढावे", "en") == "mr"   # Devanagari with Marathi words
    assert detect_language("राशन कार्ड कैसे बनवाएं", "en") == "hi"
    assert detect_language("माझे रेशन कुठे आहे", "hi") == "mr"
    assert detect_language("anything", "fr") == "en"


def test_normalize_unifies_devanagari_variants():
    assert normalize("दस्तावेज़") == normalize("दस्तावेज")
    assert normalize("गेहूँ") == normalize("गेहूं")
    assert normalize("  Ration-Card!!  ") == "ration card"


def test_topic_and_article_shortcuts(bot):
    assert bot.reply(None, "en", topic="documents").article_id == "required_documents"
    assert bot.reply(None, "mr", article_id="onorc").title.startswith("वन नेशन")
    assert bot.reply(None, "en", topic="no-such-topic").kind == "fallback"


def test_dynamic_shop_list_filters_by_place(bot):
    text = bot.reply("where is ration shop in koradi", "en", StubData()).text
    assert "Koradi Ration Shop" in text and "Hingna Ration Shop" not in text
    text = bot.reply("where is the nearest ration shop", "en", StubData()).text
    assert "Koradi Ration Shop" in text and "Hingna Ration Shop" in text


def test_dynamic_entitlements_come_from_the_database(bot):
    text = bot.reply("how much rice will i get", "en", StubData()).text
    assert "Rice (Tandul): 5 kg per eligible member per month" in text
    assert "Edible Oil (Tel): 0.5 L" in text


def test_welcome_and_quick_suggestions(bot):
    welcome = bot.welcome("hi")
    assert welcome.text.startswith("नमस्ते")
    assert [s["topic"] for s in welcome.suggestions] == [
        "ration_card", "eligibility", "how_to_apply", "documents", "token_slots", "qr_verification", "find_help", "contact_support"]


def test_search(bot):
    results = bot.search("documents", "en")
    assert results[0]["id"] == "required_documents" and results[0]["title"] == "Documents usually required"
    assert bot.search("zzzz qqqq", "en") == []


def test_input_is_capped_and_cleaned(bot):
    reply = bot.reply("documents " * 200 + "\x00\x07", "en")
    assert reply.article_id == "required_documents"


# ------------------------------------------------------------------ knowledge-base integrity

def test_every_text_exists_in_every_language():
    kb = load()
    assert len(kb.articles) >= 25 and len(kb.categories) >= 12
    for article in kb.articles.values():
        assert set(article.title) == set(article.answer) == set(LANGUAGES)
    for category in kb.categories:
        assert category.primary in kb.articles


def test_knowledge_contains_no_personal_identifiers():
    import re
    for path in KNOWLEDGE_DIR.glob("*.json"):
        content = path.read_text(encoding="utf-8")
        assert not re.search(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)", content), path.name  # no Aadhaar-like numbers
        assert "@" not in content or "example" in content, path.name


def test_broken_knowledge_fails_fast(tmp_path):
    for f in KNOWLEDGE_DIR.glob("*.json"):
        shutil.copy(f, tmp_path / f.name)
    data = json.loads((tmp_path / "faq.json").read_text(encoding="utf-8"))
    del data["articles"][0]["answer"]["mr"]
    (tmp_path / "faq.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(KnowledgeError, match="missing text"):
        load(tmp_path)


def test_external_links_are_rejected(tmp_path):
    for f in KNOWLEDGE_DIR.glob("*.json"):
        shutil.copy(f, tmp_path / f.name)
    data = json.loads((tmp_path / "ration-help.json").read_text(encoding="utf-8"))
    data["articles"][0]["links"][0]["path"] = "https://evil.example.com"
    (tmp_path / "ration-help.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(KnowledgeError, match="in-app"):
        load(tmp_path)
