"""The AI assistant's understand endpoint: complaint pre-fill, navigation, the user's own collection time,
role limits, safety refusals and privacy of the user's words. Rule-based understanding; synthetic data."""

from __future__ import annotations

import logging

import pytest
from ration_world import book


def ask(env, text, who="citizen", language="en", screen=None):
    r = env["client"].post("/api/assistant/understand", headers=env[who],
                           json={"text": text, "language": language, "screen": screen})
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.mark.parametrize("text, language, category, item", [
    ("मुझे शिकायत करनी है कि इस महीने मुझे गेहूं कम मिला।", "hi", "LessRation", "Wheat"),
    ("मला तक्रार करायची आहे, मला गहू कमी मिळाला.", "mr", "LessRation", "Wheat"),
    ("I want to complain, the shopkeeper asked for extra money for rice.", "en", "Overcharged", "Rice"),
    ("शिकायत: दुकान आज बंद थी", "hi", "ShopClosed", None),
    ("I want to file a complaint, the dal was full of insects", "en", "PoorQuality", "Pulses"),
])
def test_a_spoken_complaint_prefills_the_form(env, text, language, category, item):
    d = ask(env, text, language=language)
    assert (d["action"], d["form"], d["language"], d["understoodBy"]) == ("fill_form", "grievance", language, "rules")
    expected = {"category": category, "description": text}
    if item:
        expected["rationType"] = item
    assert d["fields"] == expected
    assert d["missing"] == []


def test_just_wanting_to_complain_opens_an_empty_form_that_asks_what_happened(env):
    d = ask(env, "मुझे शिकायत करनी है", language="hi")
    assert (d["action"], d["fields"], d["missing"]) == ("fill_form", {}, ["category", "description"])


def test_on_the_complaint_form_a_described_problem_fills_it(env):
    d = ask(env, "the rice was spoiled", screen="complaint_form")
    assert d["action"] == "fill_form" and d["fields"]["category"] == "PoorQuality" and d["fields"]["rationType"] == "Rice"
    assert ask(env, "the rice was spoiled")["action"] == "answer"   # elsewhere it is just a question


@pytest.mark.parametrize("text, language, target", [
    ("मेरा टोकन दिखाओ", "hi", "my_tokens"),
    ("show my family", "en", "family"),
    ("माझे कुटुंब दाखवा", "mr", "family"),
    ("ration card", "en", "ration_card"),
    ("मेरी शिकायत का स्टेटस", "hi", "my_complaints"),
])
def test_asking_for_a_screen_opens_it(env, text, language, target):
    d = ask(env, text, language=language)
    assert (d["action"], d["target"]) == ("navigate", target)


def test_actions_are_limited_to_the_callers_role(env):
    assert ask(env, "show stock", who="shop")["target"] == "stock"
    assert ask(env, "show stock")["action"] == "answer"                     # citizens have no stock screen
    assert ask(env, "show my family", who="shop")["action"] == "answer"     # shop owners have no family screen
    assert ask(env, "show alerts", who="official")["target"] == "alerts"
    assert ask(env, "I want to complain, I got less wheat", who="shop")["action"] == "answer"   # only citizens file


def test_when_to_collect_comes_from_the_citizens_real_bookings(env):
    none_yet = ask(env, "मेरा राशन कब मिलेगा?", language="hi")
    assert (none_yet["action"], none_yet["intent"], none_yet["reply"]["kind"]) == ("answer", "collection_time", "personal")
    assert "कोई आने वाली बुकिंग नहीं" in none_yet["reply"]["text"]

    token = book(env).json()["data"]
    d = ask(env, "मेरा टोकन बताओ", language="hi")
    assert d["intent"] == "collection_time" and token["tokenNumber"] in d["reply"]["text"]
    assert token["tokenNumber"] in ask(env, "When can I collect my ration?")["reply"]["text"]


def test_language_read_and_explain_are_handed_to_the_phone(env):
    d = ask(env, "भाषा मराठी करो", language="hi")
    assert (d["action"], d["target"]) == ("change_language", "mr")
    assert ask(env, "Read this page")["action"] == "read_screen"
    assert ask(env, "यह समझाओ", language="hi")["action"] == "explain_screen"


def test_private_numbers_are_refused_before_anything_else(env):
    d = ask(env, "I want to complain, my Aadhaar is 1234 5678 9012")
    assert d["action"] == "answer" and d["intent"] == "sensitive" and d["reply"]["kind"] == "sensitive_input"


def test_other_questions_get_the_verified_help_answer(env):
    d = ask(env, "What documents do I need for a new ration card?")
    assert d["action"] == "answer" and d["intent"] == "ask" and d["reply"]["kind"] in ("answer", "fallback")


def test_sign_in_and_input_are_required_and_words_are_never_logged(env, caplog):
    c = env["client"]
    assert c.post("/api/assistant/understand", json={"text": "show my family"}).status_code == 401
    assert c.post("/api/assistant/understand", headers=env["citizen"], json={"text": "   "}).status_code == 400
    assert c.post("/api/assistant/understand", headers=env["citizen"], json={"text": "x" * 501}).status_code == 400
    with caplog.at_level(logging.INFO):
        ask(env, "मुझे शिकायत करनी है कि गेहूं कम मिला", language="hi")
    assert caplog.records and all("गेहूं" not in r.getMessage() and "गेहूं" not in str(getattr(r, "fields", "")) for r in caplog.records)
