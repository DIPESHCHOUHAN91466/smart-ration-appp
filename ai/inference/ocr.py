"""Optional OCR for supporting documents (ration card / passbook photos).

OCR is NEVER identity verification. It only pre-fills fields that a human
operator must confirm; QR -> beneficiary -> verification stays the primary
workflow and does not depend on this module.

Pipeline: image -> preprocessing -> OCR engine -> redaction -> field extraction
          -> confidence -> requires_human_confirmation (always True)

Engines are pluggable. `TesseractEngine` is used only when both the
`pytesseract`/Pillow packages and the Tesseract binary are installed;
otherwise `UnavailableEngine` reports that clearly instead of returning fake
text. Any Aadhaar-like or mobile number is masked BEFORE anything leaves this
module, including the returned text.
"""

from __future__ import annotations

import base64
import binascii
import io
import os
import re
import shutil
from dataclasses import dataclass

from ai.errors import AIServiceError, InvalidInput

MAX_IMAGE_BYTES = 5 * 1024 * 1024
_MAGIC = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpeg"}

AADHAAR_RE = re.compile(r"(?<!\d)(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})(?!\d)")
MOBILE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?([6-9]\d{9})(?!\d)")
DOB_RE = re.compile(r"(?:DOB|D\.O\.B|Date of Birth|जन्म तिथि|जन्म तारीख)?\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4})", re.I)
NAME_RE = re.compile(r"(?:Name|नाम|नाव)\s*[:\-]\s*([A-Za-zऀ-ॿ][A-Za-zऀ-ॿ .]{1,60})", re.I)
CARD_RE = re.compile(r"(?:Ration\s*Card|RC|Card\s*No\.?|शिधापत्रिका|राशन कार्ड)\s*(?:No\.?|Number|क्रमांक)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-]{5,20})", re.I)
GENDER_RE = re.compile(r"\b(Male|Female|Transgender|पुरुष|महिला|स्त्री)\b", re.I)


class OcrEngine:
    name = "none"

    def available(self) -> bool:
        return False

    def extract_text(self, image: bytes) -> tuple[str, float]:
        raise NotImplementedError


class UnavailableEngine(OcrEngine):
    name = "unavailable"


class TesseractEngine(OcrEngine):
    """Tesseract via pytesseract. Languages: eng+hin+mar when installed."""

    name = "tesseract"

    def __init__(self) -> None:
        self._cmd = os.getenv("TESSERACT_CMD") or shutil.which("tesseract")

    def available(self) -> bool:
        if not self._cmd:
            return False
        try:
            import PIL  # noqa: F401
            import pytesseract  # noqa: F401
        except ImportError:
            return False
        return True

    def extract_text(self, image: bytes) -> tuple[str, float]:
        import pytesseract
        from PIL import Image, ImageOps

        pytesseract.pytesseract.tesseract_cmd = self._cmd
        img = Image.open(io.BytesIO(image))
        # Preprocessing: grayscale, contrast stretch, upscale small photos.
        img = ImageOps.autocontrast(ImageOps.grayscale(img))
        if img.width < 1000:
            factor = 1000 / img.width
            img = img.resize((int(img.width * factor), int(img.height * factor)))
        data = pytesseract.image_to_data(img, lang=os.getenv("OCR_LANGS", "eng"), output_type=pytesseract.Output.DICT)
        words = [(w, float(c)) for w, c in zip(data["text"], data["conf"], strict=True) if w.strip() and float(c) >= 0]
        text = " ".join(w for w, _ in words)
        confidence = sum(c for _, c in words) / len(words) / 100 if words else 0.0
        return text, round(confidence, 3)


def default_engine() -> OcrEngine:
    engine = TesseractEngine()
    return engine if engine.available() else UnavailableEngine()


def decode_image(image_base64: str) -> bytes:
    try:
        raw = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError):
        raise InvalidInput("Image must be base64-encoded.") from None
    if len(raw) > MAX_IMAGE_BYTES:
        raise InvalidInput("Image is larger than 5 MB.")
    if not any(raw.startswith(m) for m in _MAGIC):
        raise InvalidInput("Only PNG or JPEG images are accepted.")
    return raw


def mask_aadhaar(last4: str) -> str:
    return f"XXXX-XXXX-{last4}"


def redact(text: str) -> str:
    """Mask Aadhaar-like and mobile numbers in free text."""
    text = AADHAAR_RE.sub(lambda m: mask_aadhaar(m.group(3)), text)
    return MOBILE_RE.sub(lambda m: "******" + m.group(1)[-4:], text)


@dataclass
class Field:
    value: str
    confidence: float

    def as_dict(self) -> dict:
        return {"value": self.value, "confidence": self.confidence}


def extract_fields(text: str, engine_confidence: float = 1.0) -> dict:
    """Pull candidate fields out of OCR/typed text. Values are masked where
    sensitive. Confidence = engine confidence x how specific the pattern is."""
    fields: dict[str, Field] = {}

    def add(key, value, certainty):
        fields[key] = Field(value.strip(), round(engine_confidence * certainty, 3))

    if m := AADHAAR_RE.search(text):
        add("aadhaar_masked", mask_aadhaar(m.group(3)), 0.6)  # 12 digits could be another number
    if m := MOBILE_RE.search(AADHAAR_RE.sub(" ", text)):
        add("mobile_masked", "******" + m.group(1)[-4:], 0.8)
    if m := NAME_RE.search(text):
        add("name", m.group(1), 0.7)
    if m := DOB_RE.search(text):
        add("date_of_birth", m.group(1), 0.8)
    if m := CARD_RE.search(text):
        add("ration_card_number", m.group(1).upper(), 0.75)
    if m := GENDER_RE.search(text):
        add("gender", m.group(1), 0.9)
    return {k: v.as_dict() for k, v in fields.items()}


def result(text: str, engine_name: str, engine_confidence: float) -> dict:
    return {
        "engine": engine_name,
        "engine_confidence": engine_confidence,
        "text_redacted": redact(text),
        "fields": extract_fields(text, engine_confidence),
        # These flags are part of the contract: OCR output never verifies anyone.
        "requires_human_confirmation": True,
        "authoritative": False,
        "notice": "OCR output is a suggestion only. Confirm every field against the physical document; "
                  "identity is verified only through QR/OTP and the beneficiary record.",
    }


def run_ocr(engine: OcrEngine, image_base64: str) -> dict:
    if not engine.available():
        raise AIServiceError(
            "OCR_ENGINE_UNAVAILABLE",
            "No OCR engine is installed on the AI service. Install Tesseract (and pytesseract + Pillow) to enable image OCR.",
            503,
        )
    image = decode_image(image_base64)
    text, confidence = engine.extract_text(image)
    return result(text, engine.name, confidence)
