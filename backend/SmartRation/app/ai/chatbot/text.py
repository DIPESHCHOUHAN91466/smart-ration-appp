"""Chat input handling: clean-up, normalisation (incl. Devanagari spelling variants) and language detection."""

from __future__ import annotations

import re
import unicodedata

from app.ai.chatbot.knowledge_base import LANGUAGES

MAX_MESSAGE_LENGTH = 500

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

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
