"""/api/public-help/* and /api/chatbot/* — public, rate-limited, privacy-preserving."""

from __future__ import annotations

import io
import logging
import sys

import pytest
from py_testkit import BACKEND_ROOT
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.connection import get_engine
from app.services import public_help_service

sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
import seed_database  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_cache():
    public_help_service.clear_cache()
    yield
    public_help_service.clear_cache()


@pytest.fixture
def api(make_client):
    client = make_client(lambda r: None)  # these routes never reach the proxy
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as db, db.begin():
        seed_database.seed(db)  # synthetic shops, items, schemes (no users: no SEED_* passwords)
    return client


def data(r):
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    return body["data"]


def test_welcome_in_three_languages(api):
    en = data(api.get("/api/chatbot/welcome"))
    assert en["kind"] == "welcome" and en["text"].startswith("Namaste! 👋")
    assert len(en["suggestions"]) == 8 and en["suggestions"][0] == {"topic": "ration_card", "label": "Ration Card", "ask": "What is a ration card?"}
    assert data(api.get("/api/chatbot/welcome?language=mr"))["text"].startswith("नमस्कार")
    assert data(api.get("/api/chatbot/welcome?language=xx"))["language"] == "en"


def test_answers_a_question(api):
    reply = data(api.post("/api/chatbot/message", json={"message": "What documents are required?", "language": "en"}))
    assert reply["kind"] == "answer" and reply["articleId"] == "required_documents"
    assert "Proof of address" in reply["text"]
    assert reply["requiresLogin"] is False and reply["suggestions"]


def test_quick_button_topic_and_related_article(api):
    assert data(api.post("/api/chatbot/message", json={"topic": "token_slots", "language": "hi"}))["articleId"] == "book_slot"
    assert data(api.post("/api/chatbot/message", json={"articleId": "onorc"}))["title"].startswith("One Nation")


def test_live_data_from_the_database(api):
    shops = data(api.post("/api/chatbot/message", json={"message": "where is the ration shop in Koradi"}))["text"]
    assert "Koradi Ration Shop — Station Road, Koradi (Kamptee)" in shops and "Hingna Ration Shop" not in shops
    quotas = data(api.post("/api/chatbot/message", json={"message": "how much rice will I get"}))["text"]
    assert "Demo National Food Security Scheme (DEMO-NFSA):" in quotas
    assert "Rice (Tandul): 5 kg per eligible member per month" in quotas
    assert "Salt (Mith): 0.25 kg" in quotas


@pytest.mark.parametrize("body,message", [
    ({"message": "   "}, "Message: Please type a question."),
    ({}, "Message: Please type a question."),
    ({"message": "x" * 501}, "Message: Please keep your question under 500 characters."),
])
def test_rejects_empty_and_oversized_messages(api, body, message):
    r = api.post("/api/chatbot/message", json=body)
    assert r.status_code == 400
    assert r.json()["errors"] == [message]


def test_rejects_malformed_json(api):
    r = api.post("/api/chatbot/message", content=b"{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 400 and r.json()["success"] is False


def test_private_questions_require_login_even_with_a_token(api):
    anonymous = data(api.post("/api/chatbot/message", json={"message": "What is my token number?"}))
    with_header = data(api.post("/api/chatbot/message", json={"message": "What is my token number?"},
                                headers={"Authorization": "Bearer anything"}))
    assert anonymous == with_header                      # the public chat never looks at who is asking
    assert anonymous["kind"] == "private_data" and anonymous["requiresLogin"] is True


def test_sensitive_input_is_never_echoed_or_logged(api):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.getLogger().handlers[0].formatter)
    logger = logging.getLogger("smartration")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        reply = data(api.post("/api/chatbot/message", json={"message": "my aadhaar is 4321 8765 2109, otp 556677"}))
        data(api.post("/api/chatbot/message", json={"message": "What documents are required for Rahul Patil?"}))
    finally:
        logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)
    logs = stream.getvalue()
    assert reply["kind"] == "sensitive_input"
    assert "4321" not in reply["text"] and "556677" not in reply["text"]
    assert '"message": "chatbot reply"' in logs                       # the outcome is logged...
    for secret in ("4321", "8765", "556677", "Rahul", "aadhaar is"):   # ...the message never is
        assert secret not in logs


def test_markup_in_questions_is_never_reflected(api):
    reply = data(api.post("/api/chatbot/message", json={"message": "<script>alert(1)</script><img src=x onerror=alert(2)>"}))
    assert "<script>" not in reply["text"] and "onerror" not in reply["text"]


def test_rate_limited_per_client(make_client):
    client = make_client(lambda r: None, chatbot_rate_limit_per_minute=3)
    Base.metadata.create_all(get_engine())
    codes = [client.post("/api/chatbot/message", json={"message": "hello"}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]


def test_help_categories_and_articles(api):
    cats = data(api.get("/api/public-help/categories?language=mr"))
    assert [c["id"] for c in cats][:3] == ["ration_card", "eligibility", "how_to_apply"]
    assert cats[0]["title"] == "रेशन कार्ड" and cats[0]["articles"] and cats[0]["primaryArticle"] == "what_is_ration_card"
    article = data(api.get("/api/public-help/articles/required_documents?language=hi"))
    assert article["title"] == "आमतौर पर ज़रूरी दस्तावेज़"
    r = api.get("/api/public-help/articles/does-not-exist")
    assert r.status_code == 404 and r.json()["message"] == "Help article not found."


def test_help_search(api):
    results = data(api.get("/api/public-help/search", params={"q": "lost card"}))
    assert results[0]["id"] == "lost_card"
    assert api.get("/api/public-help/search").status_code == 400          # q is required
    assert api.get("/api/public-help/search", params={"q": "x" * 101}).status_code == 400


def test_routes_are_in_the_openapi_document(api):
    paths = api.get("/openapi.json").json()["paths"]
    assert {"/api/chatbot/message", "/api/chatbot/welcome", "/api/public-help/search"} <= set(paths)


def test_unknown_provider_fails_at_startup(tmp_path):
    from py_testkit import make_settings

    from app.ai.chatbot.providers import UnsupportedProvider
    from app.main import create_app

    with pytest.raises(UnsupportedProvider):
        create_app(make_settings(tmp_path, chatbot_provider="some-llm"))


# ---------------------------------------------------------------- signed-in citizens: their OWN bookings only

def _seed_bookings(tmp_path):
    from datetime import time, timedelta

    from py_testkit import make_settings

    from app.database.models import RationShop, TimeSlot, Token, User
    from app.security.tokens import TokenUser, create_access_token
    from app.utils.time import utc_now

    settings = make_settings(tmp_path)
    now = utc_now()
    with Session(get_engine()) as db, db.begin():
        shop = db.scalar(select(RationShop).where(RationShop.ShopCode == "SR-SATNAVARI-001"))
        slot = TimeSlot(RationShopId=shop.Id, SlotDate=now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
                        StartTime=time(10, 5), EndTime=time(10, 10), Capacity=2, BookedCount=2)
        db.add(slot)
        users = [User(FullName=f"Citizen {i}", Email=f"c{i}@example.test", MobileNumber=f"700000000{i}", PasswordHash="x",
                      Role=1, IsActive=True, CreatedAt=now) for i in (1, 2)]
        owner = User(FullName="Owner", Email="o@example.test", MobileNumber="7000000009", PasswordHash="x", Role=2,
                     IsActive=True, CreatedAt=now, RationShopId=shop.Id)
        db.add_all([*users, owner])
        db.flush()
        for u, number in zip(users, ("TKN-MINE-001", "TKN-OTHER-002"), strict=True):
            db.add(Token(TokenNumber=number, UserId=u.Id, RationShopId=shop.Id, TimeSlotId=slot.Id, Status=2, CreatedAt=now))
        tokens = {name: create_access_token(TokenUser(u.Id, u.Email, u.FullName, role, u.RationShopId), settings)[0]
                  for name, u, role in (("mine", users[0], "RuralUser"), ("owner", owner, "ShopOwner"))}
    return tokens


def test_signed_in_citizen_sees_only_their_own_booking(api, tmp_path):
    tokens = _seed_bookings(tmp_path)
    reply = data(api.post("/api/chatbot/message", json={"message": "What is my appointment?"},
                          headers={"Authorization": f"Bearer {tokens['mine']}"}))
    assert reply["kind"] == "personal"
    assert "TKN-MINE-001" in reply["text"] and "10:05–10:10" in reply["text"] and "Satnavari" in reply["text"]
    assert "TKN-OTHER-002" not in reply["text"]
    assert reply["links"][0]["path"].startswith("/rural/token/")


def test_signed_in_family_question_links_to_the_secure_page_without_data(api, tmp_path):
    tokens = _seed_bookings(tmp_path)
    reply = data(api.post("/api/chatbot/message", json={"message": "show my family members", "language": "mr"},
                          headers={"Authorization": f"Bearer {tokens['mine']}"}))
    assert reply["kind"] == "personal" and reply["links"] == [{"path": "/rural/verification", "label": "माझी पडताळणी उघडा"}]


@pytest.mark.parametrize("header", ["Bearer not-a-token", None, "owner"])
def test_others_get_the_generic_login_reply(api, tmp_path, header):
    tokens = _seed_bookings(tmp_path)
    headers = {} if header is None else {"Authorization": f"Bearer {tokens['owner']}" if header == "owner" else header}
    reply = data(api.post("/api/chatbot/message", json={"message": "What is my appointment?"}, headers=headers))
    assert reply["kind"] == "private_data" and "TKN-" not in reply["text"]
