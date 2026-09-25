"""Safety and intent rules, checked before any knowledge-base search (in this order):

  1. sensitive input (Aadhaar-like numbers, OTPs, passwords)  -> "sensitive_input"
  2. system/security internals or other people's data          -> "internal"
  3. the user's OWN records ("my token", "my family")          -> "own_records"
  4. health questions                                           -> "health"
  5. greetings / thanks                                         -> "greeting" / "thanks"
  None = an ordinary question: search the knowledge base.
Pure functions of the text: no data access, no side effects.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from app.chatbot.text import normalize

_AADHAAR_LIKE = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
_OTP_WITH_CODE = re.compile(r"(otp|ओटीपी|one time password)\D{0,20}\d{4,8}|\d{4,8}\D{0,20}(otp|ओटीपी)", re.IGNORECASE)
_PASSWORD_VALUE = re.compile(r"(password|passcode|पासवर्ड)\s*(is|was|:|=|है|आहे)\s*\S+", re.IGNORECASE)

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

_OWN = {normalize(w) for w in OWN_WORDS}
_RECORDS = {normalize(w) for w in OWN_RECORDS}
_BOOKING = {normalize(w) for w in BOOKING_WORDS}
_HOW = {normalize(w) for w in HOW_WORDS}
_HEALTH = {normalize(w) for w in HEALTH_WORDS}
_GREETINGS = {normalize(w) for w in GREETINGS}
_THANKS = {normalize(w) for w in THANKS}


def classify(text: str, norm: str, tokens: list[str], has_article_match: Callable[[], bool]) -> str | None:
    """The intent of a cleaned message (`text`), its normalised form and tokens. `has_article_match`
    is only called for short greetings ("hi, ration card?" is a question, not a greeting)."""
    token_set = set(tokens)
    if _AADHAAR_LIKE.search(text) or _OTP_WITH_CODE.search(text) or _PASSWORD_VALUE.search(text):
        return "sensitive_input"
    if any(phrase in norm for phrase in INTERNAL_PHRASES):
        return "internal"
    if token_set & _OWN and token_set & _RECORDS and not token_set & _HOW:
        return "own_records"
    if token_set & _HEALTH or any(w in norm for w in _HEALTH if " " in w):
        return "health"
    if len(tokens) <= 4 and (norm in _GREETINGS or tokens[0] in _GREETINGS or " ".join(tokens[:2]) in _GREETINGS) \
            and not has_article_match():
        return "greeting"
    if any(t in norm for t in _THANKS) and len(tokens) <= 5:
        return "thanks"
    return None


def is_about_bookings(tokens: set[str]) -> bool:
    return bool(tokens & _BOOKING)
