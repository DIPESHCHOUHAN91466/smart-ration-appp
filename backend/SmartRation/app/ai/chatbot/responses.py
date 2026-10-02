"""What the assistant sends back: the Reply model and every piece of answer text assembled in code
(signed-in booking lines, live shop and scheme lists). Article texts themselves live in
ai/chatbot/knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.ai.chatbot.text import normalize


@dataclass
class Reply:
    kind: str                       # answer | fallback | welcome | greeting | thanks | private_data | personal | sensitive_input | internal | health
    language: str
    text: str
    article_id: str | None = None
    title: str | None = None
    links: list[dict] = field(default_factory=list)
    suggestions: list[dict] = field(default_factory=list)
    related: list[dict] = field(default_factory=list)
    requires_login: bool = False
    confidence: float = 0.0


def reply_dto(reply: Reply) -> dict:
    """The JSON shape every chat answer is sent in (help chat and assistant)."""
    return {
        "kind": reply.kind, "language": reply.language, "text": reply.text, "articleId": reply.article_id,
        "title": reply.title, "links": reply.links, "suggestions": reply.suggestions, "related": reply.related,
        "requiresLogin": reply.requires_login, "confidence": reply.confidence,
    }


# ------------------------------------------------------------------ signed-in replies

_YOUR_BOOKINGS = {"en": "Your upcoming bookings:", "hi": "आपकी आने वाली बुकिंग:", "mr": "तुमची आगामी बुकिंग:"}
_NO_BOOKINGS = {"en": "You have no upcoming bookings. You can book a 5-minute slot from “Book Ration”.",
                "hi": "आपकी कोई आने वाली बुकिंग नहीं है। “राशन बुक करें” से 5 मिनट का स्लॉट बुक करें।",
                "mr": "तुमची कोणतीही आगामी बुकिंग नाही. “रेशन बुक करा” मधून 5 मिनिटांचा स्लॉट बुक करा."}
_SHOW_QR = {"en": "Show the QR code from “My Token” at the shop.", "hi": "दुकान पर “मेरा टोकन” से QR कोड दिखाएँ।",
            "mr": "दुकानात “माझे टोकन” मधील QR कोड दाखवा."}
_SEE_VERIFICATION = {"en": "Your family members, masked Aadhaar and passbook details are on your secure “My Verification” page.",
                     "hi": "आपके परिवार के सदस्य, छिपा हुआ आधार और पासबुक विवरण आपके सुरक्षित “मेरा सत्यापन” पेज पर हैं।",
                     "mr": "तुमचे कुटुंबातील सदस्य, लपवलेला आधार आणि पासबुक तपशील तुमच्या सुरक्षित “माझी पडताळणी” पानावर आहेत."}
_BOOK_LABEL = {"en": "Book a slot", "hi": "स्लॉट बुक करें", "mr": "स्लॉट बुक करा"}
_TOKEN_LABEL = {"en": "Show my token", "hi": "मेरा टोकन दिखाएँ", "mr": "माझे टोकन दाखवा"}
_VERIFICATION_LABEL = {"en": "Open My Verification", "hi": "मेरा सत्यापन खोलें", "mr": "माझी पडताळणी उघडा"}
_STATUS = {"en": {"Pending": "pending", "Confirmed": "confirmed"},
           "hi": {"Pending": "लंबित", "Confirmed": "पुष्ट"},
           "mr": {"Pending": "प्रलंबित", "Confirmed": "निश्चित"}}


def bookings_reply(bookings: list[dict], lang: str) -> Reply:
    """The signed-in citizen's own upcoming bookings ({id, token, date, start, end, shop, status})."""
    if not bookings:
        return Reply(kind="personal", language=lang, text=_NO_BOOKINGS[lang],
                     links=[{"path": "/rural/book", "label": _BOOK_LABEL[lang]}], confidence=1.0)
    lines = [_YOUR_BOOKINGS[lang]]
    for b in bookings:
        status = _STATUS[lang].get(b["status"], b["status"])
        lines.append(f"• {b['token']} — {b['date']} {b['start']}–{b['end']}, {b['shop']} ({status})")
    lines.append(_SHOW_QR[lang])
    return Reply(kind="personal", language=lang, text="\n".join(lines), confidence=1.0,
                 links=[{"path": f"/rural/token/{bookings[0]['id']}", "label": _TOKEN_LABEL[lang]}])


def verification_reply(lang: str) -> Reply:
    """Family, Aadhaar and passbook details are never shown in chat: point to the secured page."""
    return Reply(kind="personal", language=lang, text=_SEE_VERIFICATION[lang], confidence=1.0,
                 links=[{"path": "/rural/verification", "label": _VERIFICATION_LABEL[lang]}])


# ------------------------------------------------------------------ live public data

_PER_MEMBER = {"en": "per eligible member per month", "hi": "प्रति पात्र सदस्य प्रति माह", "mr": "प्रति पात्र सदस्य प्रति महिना"}
_NO_SHOPS = {"en": "No active shops are listed at the moment.", "hi": "अभी कोई सक्रिय दुकान सूचीबद्ध नहीं है।", "mr": "सध्या कोणतेही सक्रिय दुकान सूचीबद्ध नाही."}


def _qty(value) -> str:
    d = Decimal(str(value)).normalize()
    return format(d, "f")


def shops_text(shops: list[dict], norm: str, lang: str, limit: int = 10) -> str:
    if not shops:
        return _NO_SHOPS[lang]
    words = {w for w in norm.split() if len(w) >= 4}
    # Match on place names only: the shop *name* contains "Ration Shop", which every question mentions.
    matching = [s for s in shops if words & set(normalize(" ".join(str(s.get(k) or "") for k in ("village", "taluka", "district"))).split())]
    chosen = (matching or shops)[:limit]
    return "\n".join(f"• {s['name']} — {s['address']}" + (f" ({s['taluka']})" if s.get("taluka") else "") for s in chosen)


def schemes_text(schemes: list[dict], lang: str) -> str:
    blocks = []
    for scheme in schemes:
        lines = [f"{scheme['name']} ({scheme['code']}):"]
        for item in scheme["items"]:
            label = f"{item['name']} ({item['vernacular']})" if item.get("vernacular") else item["name"]
            lines.append(f"• {label}: {_qty(item['quota'])} {item['unit']} {_PER_MEMBER[lang]}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
