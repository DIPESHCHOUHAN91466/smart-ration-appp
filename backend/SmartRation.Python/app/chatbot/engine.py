"""The Public Help assistant: safety checks first, then retrieval over the knowledge base.

Deterministic and explainable: every answer is a reviewed article (plus live public data such
as the shop list), never generated text. That keeps it honest about what it knows and makes it
impossible for it to reveal data it was never given. A generative model can be added later
behind `ChatProvider` (app/chatbot/providers.py), grounded on the same articles.

Order of checks for each message:
  1. sensitive input (Aadhaar-like numbers, OTPs, passwords) → warn, don't process further
  2. requests for system/security internals or other people's data → refuse
  3. requests for the user's own records (my token, my family…) → ask them to log in
  4. health questions → general guidance, never diagnosis
  5. greetings / thanks
  6. knowledge-base search → best article, or a helpful fallback
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

from app.chatbot.knowledge_base import LANGUAGES, Article, KnowledgeBase

MAX_MESSAGE_LENGTH = 500
ANSWER_THRESHOLD = 2.0


class PublicData(Protocol):
    """Public, non-personal facts the assistant may include (read from the database)."""

    def shops(self) -> list[dict]: ...  # {name, address, village, taluka, district}

    def schemes(self) -> list[dict]: ...  # {code, name, items: [{name, vernacular, unit, quota}]}


class PersonalData(Protocol):
    """The signed-in citizen's OWN records, available only with a valid access token."""

    def upcoming_bookings(self) -> list[dict]: ...  # {id, token, date, start, end, shop, status}


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


# ------------------------------------------------------------------ text handling

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_AADHAAR_LIKE = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
_OTP_WITH_CODE = re.compile(r"(otp|ओटीपी|one time password)\D{0,20}\d{4,8}|\d{4,8}\D{0,20}(otp|ओटीपी)", re.IGNORECASE)
_PASSWORD_VALUE = re.compile(r"(password|passcode|पासवर्ड)\s*(is|was|:|=|है|आहे)\s*\S+", re.IGNORECASE)

STOPWORDS = {
    # en
    "a", "an", "the", "is", "are", "am", "was", "be", "to", "of", "in", "on", "at", "for", "and", "or", "i", "me",
    "we", "you", "it", "do", "does", "can", "could", "please", "tell", "about", "with", "from", "this", "that",
    "what", "which", "who", "when", "there", "any", "get", "have", "has", "need", "want", "will", "should", "my",
    # hi (and romanised)
    "का", "की", "के", "है", "हैं", "में", "से", "को", "और", "या", "क्या", "मुझे", "मैं", "हम", "पर", "भी", "तो",
    "kya", "hai", "ka", "ki", "ke", "mein", "se", "ko", "aur", "mujhe",
    # mr
    "चा", "ची", "चे", "आहे", "आहेत", "मध्ये", "ला", "ना", "व", "आणि", "किंवा", "काय", "मला", "मी", "आम्ही", "हे", "ते",
}
OWN_WORDS = {"my", "mine", "mera", "meri", "mere", "mujhe", "मेरा", "मेरी", "मेरे", "मुझे", "माझा", "माझी", "माझे", "माझ्या", "मला"}
OWN_RECORDS = {
    "token", "booking", "bookings", "slot", "appointment", "aadhaar", "aadhar", "otp", "qr", "collection", "history",
    "family", "status", "profile", "details", "entitlement", "balance",
    "टोकन", "बुकिंग", "आधार", "ओटीपी", "परिवार", "कुटुंब", "इतिहास", "स्थिति", "स्थिती", "प्रोफाइल", "तपशील",
}
BOOKING_WORDS = {"token", "booking", "bookings", "slot", "appointment", "qr", "time", "date", "when",
                 "टोकन", "बुकिंग", "स्लॉट", "अपॉइंटमेंट", "समय", "वेळ", "तारीख", "कब", "केव्हा"}
HOW_WORDS = {"how", "kaise", "kaisa", "steps", "process", "apply", "book", "cancel", "reschedule", "lost", "change",
             "कैसे", "कसे", "कसा", "कशी", "प्रक्रिया", "बुक", "रद्द", "बदल", "बदलना"}
INTERNAL_PHRASES = (
    "ignore previous", "ignore all", "ignore your", "system prompt", "your instructions", "your prompt", "developer mode",
    "jailbreak", "api key", "apikey", "jwt", "secret key", "database password", "db password", "admin password",
    "admin login", "root password", "sql", "drop table", "select from", "show all users", "list all users", "list users",
    "all beneficiaries", "someone else", "other people", "another person", "aadhaar of", "aadhar of", "credentials",
    "connection string", "server config",
)
HEALTH_WORDS = {
    "fever", "cough", "diabetes", "diabetic", "pregnant", "pregnancy", "malnutrition", "malnourished", "nutrition",
    "nutritious", "diet", "anemia", "anaemia", "symptom", "symptoms", "medicine", "medicines", "doctor", "hospital",
    "disease", "sick", "illness", "vaccine", "vaccination", "health", "healthy", "baby food", "breastfeeding",
    "बुखार", "खांसी", "गर्भवती", "पोषण", "डॉक्टर", "डाक्टर", "दवा", "बीमार", "बीमारी", "स्वास्थ्य", "ताप", "खोकला",
    "गरोदर", "औषध", "आजार", "आरोग्य", "कुपोषण", "दवाई", "रुग्णालय", "अस्पताल",
}
GREETINGS = {"hi", "hello", "hey", "hii", "helo", "namaste", "namaskar", "namaskaar", "नमस्ते", "नमस्कार", "राम राम",
             "good morning", "good afternoon", "good evening"}
THANKS = {"thanks", "thank you", "thankyou", "thx", "dhanyavad", "dhanyawad", "shukriya", "धन्यवाद", "शुक्रिया", "आभार", "थँक्यू"}
MARATHI_MARKERS = {"आहे", "आहेत", "काय", "कसे", "कसा", "कशी", "मला", "माझे", "माझा", "माझी", "आम्ही", "करू", "पाहिजे",
                   "कुठे", "किती", "नाही", "हवे", "मिळेल", "मिळते", "कोणती", "कोणते", "करावा", "करावे", "रेशन"}
HINDI_MARKERS = {"है", "हैं", "क्या", "कैसे", "मुझे", "मेरा", "मेरी", "कहाँ", "कहां", "कितना", "नहीं", "चाहिए", "मिलेगा",
                 "करें", "करूँ", "कौन", "राशन", "होता"}


def normalize(text: str) -> str:
    """Lower-case, strip punctuation/symbols/control characters, unify Devanagari spelling
    variants (nukta, chandrabindu → anusvara), collapse whitespace."""
    text = unicodedata.normalize("NFC", unicodedata.normalize("NFKC", text)).lower()
    text = text.replace("़", "").replace("ँ", "ं")  # ज़→ज, गेहूँ→गेहूं
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] in "PSZ" or cat in ("Cc", "Cs", "Co", "Cn"):
            out.append(" ")
        elif cat == "Cf":
            continue  # zero-width joiners etc.
        else:
            out.append(ch)
    return " ".join("".join(out).split())


def clean_input(message: str) -> str:
    """Remove control characters and cap the length (validation happens in the API layer)."""
    message = "".join(ch for ch in message if unicodedata.category(ch) not in ("Cc", "Cf") or ch in "\n\t")
    return message.strip()[:MAX_MESSAGE_LENGTH]


def detect_language(message: str, requested: str | None) -> str:
    requested = requested if requested in LANGUAGES else "en"
    if not _DEVANAGARI.search(message):
        return requested
    if requested in ("hi", "mr"):
        tokens = set(normalize(message).split())
        mr, hi = len(tokens & {normalize(w) for w in MARATHI_MARKERS}), len(tokens & {normalize(w) for w in HINDI_MARKERS})
        if requested == "hi" and mr > hi:
            return "mr"
        if requested == "mr" and hi > mr:
            return "hi"
        return requested
    tokens = set(normalize(message).split())
    return "mr" if len(tokens & {normalize(w) for w in MARATHI_MARKERS}) > len(tokens & {normalize(w) for w in HINDI_MARKERS}) else "hi"


# ------------------------------------------------------------------ the assistant

class Assistant:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        # (normalized keyword, weight): "~" marks generic nouns ("ration card", "shop") that appear in many
        # questions and shouldn't outweigh intent words ("apply", "documents", "less ration").
        self._keywords = {a.id: [(normalize(k.lstrip("~")), 0.5 if k.startswith("~") else 1.0) for k in a.keywords]
                          for a in kb.articles.values()}
        titles = {
            a.id: {t for lang in LANGUAGES for t in normalize(a.title[lang]).split() if t not in STOPWORDS and len(t) > 2}
            for a in kb.articles.values()
        }
        # Title words shared by many articles ("ration", "card", "shop") say nothing about intent.
        frequency: dict[str, int] = {}
        for tokens in titles.values():
            for t in tokens:
                frequency[t] = frequency.get(t, 0) + 1
        self._title_tokens = {aid: {t for t in tokens if frequency[t] <= 3} for aid, tokens in titles.items()}
        self._health = {normalize(w) for w in HEALTH_WORDS}
        self._own = {normalize(w) for w in OWN_WORDS}
        self._records = {normalize(w) for w in OWN_RECORDS}
        self._how = {normalize(w) for w in HOW_WORDS}
        self._greetings = {normalize(w) for w in GREETINGS}
        self._thanks = {normalize(w) for w in THANKS}
        self._stop = {normalize(w) for w in STOPWORDS}

    # ---------------------------------------------------------------- public API

    def welcome(self, language: str) -> Reply:
        lang = language if language in LANGUAGES else "en"
        return Reply(kind="welcome", language=lang, text=self.kb.responses["welcome"][lang],
                     suggestions=self.quick_suggestions(lang), confidence=1.0)

    def quick_suggestions(self, lang: str, exclude: str | None = None, limit: int = 8) -> list[dict]:
        return [{"topic": c.id, "label": c.title[lang], "ask": c.ask[lang]}
                for c in self.kb.categories if c.quick and c.id != exclude][:limit]

    def reply(self, message: str | None, language: str | None, data: PublicData | None = None,
              topic: str | None = None, article_id: str | None = None, personal: PersonalData | None = None) -> Reply:
        text = clean_input(message or "")
        lang = detect_language(text, language)

        if article_id:
            article = self.kb.articles.get(article_id)
            return self._answer(article, lang, data, 1.0) if article else self._fallback(lang)
        if topic:
            category = next((c for c in self.kb.categories if c.id == topic), None)
            return self._answer(self.kb.articles[category.primary], lang, data, 1.0) if category else self._fallback(lang)
        if not text:
            return self.welcome(lang)

        norm = normalize(text)
        tokens = norm.split()
        token_set = set(tokens)

        if _AADHAAR_LIKE.search(text) or _OTP_WITH_CODE.search(text) or _PASSWORD_VALUE.search(text):
            return self._fixed("sensitive_input", lang)
        if any(phrase in norm for phrase in INTERNAL_PHRASES):
            return self._fixed("internal", lang)
        if token_set & self._own and token_set & self._records and not token_set & self._how:
            if personal is not None:
                return self._personal(token_set, lang, personal)
            reply = self._fixed("private_data", lang)
            reply.requires_login = True
            reply.links = [{"path": "/login", "label": {"en": "Log in securely", "hi": "सुरक्षित लॉग इन करें", "mr": "सुरक्षित लॉग इन करा"}[lang]}]
            return reply
        if token_set & self._health or any(w in norm for w in self._health if " " in w):
            return self._fixed("health", lang)
        if len(tokens) <= 4 and (norm in self._greetings or tokens[0] in self._greetings or " ".join(tokens[:2]) in self._greetings) \
                and not self._scores(norm, tokens):
            return self._fixed("greeting", lang)
        if any(t in norm for t in self._thanks) and len(tokens) <= 5:
            return self._fixed("thanks", lang)

        scored = self._scores(norm, tokens)
        if not scored or scored[0][0] < ANSWER_THRESHOLD:
            return self._fallback(lang)
        best_score, best = scored[0]
        reply = self._answer(best, lang, data, min(1.0, best_score / 6), norm)
        reply.related = [{"id": a.id, "title": a.title[lang]} for s, a in scored[1:4] if s >= ANSWER_THRESHOLD and a.id != best.id][:2]
        return reply

    def search(self, query: str, language: str | None, limit: int = 8) -> list[dict]:
        text = clean_input(query)[:100]
        lang = detect_language(text, language)
        norm = normalize(text)
        results = []
        for score, article in self._scores(norm, norm.split()):
            if score < 1.0:
                break
            body = article.answer[lang]
            results.append({"id": article.id, "category": article.category, "title": article.title[lang],
                            "excerpt": body.split("\n")[0][:180], "score": round(score, 2)})
        return results[:limit]

    def article(self, article_id: str, language: str | None, data: PublicData | None = None) -> Reply | None:
        article = self.kb.articles.get(article_id)
        lang = language if language in LANGUAGES else "en"
        return self._answer(article, lang, data, 1.0) if article else None

    # ---------------------------------------------------------------- internals

    def _personal(self, token_set: set[str], lang: str, personal: PersonalData) -> Reply:
        """Signed-in citizen asking about their own records. Only bookings are answered in chat;
        family, Aadhaar and passbook details stay on the secured verification page."""
        if token_set & {normalize(w) for w in BOOKING_WORDS}:
            bookings = personal.upcoming_bookings()
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
        return Reply(kind="personal", language=lang, text=_SEE_VERIFICATION[lang], confidence=1.0,
                     links=[{"path": "/rural/verification", "label": _VERIFICATION_LABEL[lang]}])

    def _scores(self, norm: str, tokens: list[str]) -> list[tuple[float, Article]]:
        content = [t for t in tokens if t not in self._stop]
        if not content:
            return []
        latin = [t for t in content if t.isascii() and len(t) >= 5]
        scored = []
        for article in self.kb.articles.values():
            score = 0.0
            for kw, weight in self._keywords[article.id]:
                if kw == norm:
                    score += 2.0  # the whole question is this keyword ("ration card")
                if " " in kw:
                    if kw in norm:
                        score += 3.0 * weight
                elif kw in content:
                    score += 2.0 * weight
                elif len(kw) >= 3 and any(t.startswith(kw) or (len(t) >= 4 and kw.startswith(t)) for t in content):
                    score += 1.2 * weight  # inflections: documents/document, दस्तावेजों/दस्तावेज
                elif kw.isascii() and len(kw) >= 5 and latin and difflib.get_close_matches(kw, latin, n=1, cutoff=0.84):
                    score += 1.8 * weight  # typos: "eligiblity", "documnts"
            score += 0.5 * len(self._title_tokens[article.id] & set(content))
            if score > 0:
                scored.append((score, article))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored

    def _fixed(self, kind: str, lang: str) -> Reply:
        return Reply(kind=kind, language=lang, text=self.kb.responses[kind][lang],
                     suggestions=self.quick_suggestions(lang, limit=4), confidence=1.0)

    def _fallback(self, lang: str) -> Reply:
        return Reply(kind="fallback", language=lang, text=self.kb.responses["fallback"][lang],
                     suggestions=self.quick_suggestions(lang), confidence=0.0)

    def _answer(self, article: Article, lang: str, data: PublicData | None, confidence: float, norm: str = "") -> Reply:
        text = article.answer[lang]
        if article.dynamic and data is not None:
            extra = shops_text(data.shops(), norm, lang) if article.dynamic == "shops" else schemes_text(data.schemes(), lang)
            if extra:
                text = f"{text}\n\n{extra}"
        return Reply(
            kind="answer", language=lang, text=text, article_id=article.id, title=article.title[lang],
            links=[{"path": link.path, "label": link.label[lang]} for link in article.links],
            suggestions=self.quick_suggestions(lang, exclude=article.category, limit=4), confidence=round(confidence, 2),
        )


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
