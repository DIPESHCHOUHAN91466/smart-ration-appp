"""Turning what the user said into a proposed action: the Understanding contract and the rule-based provider.

`RulesUnderstanding` needs no outside service: it recognises requests in English, Hindi and Marathi by keyword
(open a screen, file a complaint, ask when to collect ration, read this screen, change language) and extracts the
complaint's category and item. It does not guess: anything it does not recognise comes back as intent "ask" and is
answered by the verified help assistant. A future LLM provider returns the same `Understanding`, which is then
checked against the allowed actions exactly like this one (see actions.py and service.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.ai.chatbot.text import normalize

# intent: navigate | fill_form | collection_time | read_screen | explain_screen | change_language | ask
INTENTS = ("navigate", "fill_form", "collection_time", "read_screen", "explain_screen", "change_language", "ask")


@dataclass
class Understanding:
    intent: str
    target: str | None = None                 # screen id (navigate) or form id (fill_form) or language (change_language)
    fields: dict[str, str] = field(default_factory=dict)


class UnderstandingProvider(Protocol):
    name: str

    def understand(self, text: str, language: str, screen: str | None) -> Understanding: ...


def _words(*groups: str) -> tuple[str, ...]:
    return tuple(normalize(w) for g in groups for w in g.split("|"))


def _has(norm: str, words: tuple[str, ...]) -> bool:
    """Latin words must match whole words; Devanagari stems may match inside a word (गेहूं, गहू, कमी)."""
    padded = f" {norm} "
    return any((f" {w} " in padded) if w.isascii() else (w in norm) for w in words)


SHOW = _words("show|open|see|display|go to|take me", "दिखाओ|दिखाइए|दिखाएं|दिखाएँ|खोलो|खोलिए|खोलें|ले चलो",
              "दाखवा|दाखव|उघडा|उघड|बघायचे|पाहायचे")
COMPLAINT = _words("complaint|complain|grievance|report a problem|report problem",
                   "शिकायत|कंप्लेंट", "तक्रार")
MY_COMPLAINTS = _words("my complaints|complaint status|status of my complaint",
                       "शिकायत का स्टेटस|शिकायत की स्थिति|मेरी शिकायतें", "तक्रारीची स्थिती|माझ्या तक्रारी")
WHEN = _words("when|what time|which day", "कब|कितने बजे|किस दिन", "कधी|केव्हा|किती वाजता")
RATION_OR_TOKEN = _words("ration|token|slot|collect|collection", "राशन|टोकन|स्लॉट", "रेशन|टोकन|धान्य")
TELL = _words("tell|tell me|what is", "बताओ|बताइए|बताएं|बताएँ", "सांगा|सांग")
GO = _words("go|visit|come", "जाना|जाऊं|जाऊँ|आना", "जायचे|जाऊ|यायचे")
READ = _words("read|read out|read aloud|speak this", "पढ़ो|पढ़कर|पढ़ें|सुनाओ|सुनाइए|बोलकर", "वाचा|वाचून|ऐकवा|वाचून दाखवा")
EXPLAIN = _words("explain|what does this mean", "समझाओ|समझाइए|मतलब", "समजावून|समजावा|अर्थ")
LANGUAGE = _words("language|speak in|switch to", "भाषा", "भाषा")
LANGUAGE_NAMES = {"mr": _words("marathi|मराठी"), "hi": _words("hindi|हिंदी|हिन्दी"),
                  "en": _words("english|अंग्रेजी|अंग्रेज़ी|इंग्रजी|इंग्लिश")}

SCREEN_WORDS: list[tuple[str, tuple[str, ...]]] = [
    ("my_complaints", MY_COMPLAINTS),
    ("my_tokens", _words("token|tokens|qr|qr code", "टोकन|क्यूआर", "टोकन")),
    ("book", _words("book|booking|book a slot", "बुक|बुकिंग", "बुक|बुकिंग")),
    ("family", _words("family|members", "परिवार|सदस्य", "कुटुंब|सदस्य")),
    ("ration_card", _words("ration card|card", "राशन कार्ड|कार्ड", "रेशन कार्ड|कार्ड")),
    ("eligibility", _words("eligibility|entitlement|how much ration", "पात्रता|कितना राशन|हकदार", "पात्रता|किती रेशन")),
    ("notifications", _words("notification|notifications|messages", "सूचना|सूचनाएं|संदेश", "सूचना|संदेश")),
    ("queue", _words("queue|waiting list", "कतार|लाइन", "रांग")),
    ("stock", _words("stock|inventory", "स्टॉक|भंडार", "साठा|स्टॉक")),
    ("scan", _words("scan|scanner", "स्कैन", "स्कॅन")),
    ("alerts", _words("alert|alerts", "अलर्ट|चेतावनी", "सूचना")),
    ("shops", _words("shops|all shops", "दुकानें|सभी दुकान", "दुकाने")),
    ("help", _words("help", "मदद|सहायता", "मदत")),
    ("home", _words("home|main screen", "होम|मुख्य", "मुख्य पान|होम")),
]

# Complaint category: checked in this order (the more specific first); LessRation is the common case.
CATEGORY_WORDS: list[tuple[str, tuple[str, ...]]] = [
    ("Overcharged", _words("overcharge|overcharged|extra money|more money|bribe|asked for money",
                           "ज्यादा पैसे|अधिक पैसे|पैसे मांगे|पैसे लिए|रिश्वत", "जास्त पैसे|पैसे मागितले|लाच")),
    ("PoorQuality", _words("quality|spoiled|rotten|bad grain|insects|stones",
                           "खराब|सड़ा|सडा|घटिया|कीड़े|कीडे|कंकड़", "निकृष्ट|सडलेले|किडे|खडे|खराब")),
    ("ShopClosed", _words("closed|shut", "बंद", "बंद")),
    ("StaffBehaviour", _words("rude|misbehave|misbehaved|abused|shouted",
                              "बदतमीज|गाली|बुरा व्यवहार|डांटा", "उद्धट|अपमान|शिवीगाळ|ओरडले")),
    ("VerificationProblem", _words("otp|aadhaar|aadhar|verification|fingerprint|biometric",
                                   "ओटीपी|आधार|सत्यापन|अंगूठा", "ओटीपी|आधार|पडताळणी|अंगठा")),
    ("LessRation", _words("less|short|not given|did not get|didn't get|not received|missing|reduced",
                          "कम|नहीं मिला|नहीं दिया|पूरा नहीं|नही मिला", "कमी|मिळाले नाही|मिळाला नाही|दिले नाही")),
    ("TokenProblem", _words("token|qr|slot|booking", "टोकन|क्यूआर|स्लॉट|बुकिंग", "टोकन|स्लॉट|बुकिंग")),
]
ITEM_WORDS: list[tuple[str, tuple[str, ...]]] = [
    ("Wheat", _words("wheat|gehu|gehun|atta", "गेहूं|गेहूँ|गेंहू|आटा", "गहू")),
    ("Rice", _words("rice|chawal", "चावल", "तांदूळ|तांदुळ")),
    ("Sugar", _words("sugar|cheeni", "चीनी|शक्कर", "साखर")),
    ("Pulses", _words("pulses|dal|daal|lentils", "दाल", "डाळ")),
    ("EdibleOil", _words("oil|edible oil", "तेल", "तेल")),
    ("Salt", _words("salt|namak", "नमक", "मीठ")),
]


def _first(norm: str, table: list[tuple[str, tuple[str, ...]]]) -> str | None:
    return next((name for name, words in table if _has(norm, words)), None)


class RulesUnderstanding:
    name = "rules"

    def understand(self, text: str, language: str, screen: str | None) -> Understanding:
        norm = normalize(text)
        category, item = _first(norm, CATEGORY_WORDS), _first(norm, ITEM_WORDS)

        if _has(norm, LANGUAGE):
            chosen = next((code for code, words in LANGUAGE_NAMES.items() if _has(norm, words)), None)
            if chosen:
                return Understanding("change_language", chosen)
        if _has(norm, MY_COMPLAINTS):
            return Understanding("navigate", "my_complaints")
        on_complaint_form = screen == "complaint_form"
        # A complaint: said outright, or a ration problem described while the complaint form is open.
        if _has(norm, COMPLAINT) or (on_complaint_form and (category or item)):
            fields: dict[str, str] = {}
            if category:
                fields["category"] = category
            if item:
                fields["rationType"] = item
                fields.setdefault("category", "LessRation")
            if category or item:
                fields["description"] = text.strip()   # the user's own words, for them to review
            return Understanding("fill_form", "grievance", fields)
        if _has(norm, READ):
            return Understanding("read_screen")
        if _has(norm, EXPLAIN):
            return Understanding("explain_screen")
        if _has(norm, WHEN) and (_has(norm, RATION_OR_TOKEN) or _has(norm, GO)):
            return Understanding("collection_time")
        if _has(norm, TELL) and _has(norm, RATION_OR_TOKEN):
            return Understanding("collection_time")
        target = _first(norm, SCREEN_WORDS)
        if target and (_has(norm, SHOW) or len(norm.split()) <= 3):
            return Understanding("navigate", target)
        return Understanding("ask")
