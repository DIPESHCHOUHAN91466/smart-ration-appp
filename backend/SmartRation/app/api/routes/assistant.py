"""The AI assistant behind the app's AI button: POST /api/assistant/understand. See app/ai/assistant/service.py."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.assistant import service
from app.ai.chatbot.knowledge_base import LANGUAGES
from app.ai.chatbot.providers import get_provider
from app.ai.chatbot.text import MAX_MESSAGE_LENGTH, clean_input
from app.api.dependencies.auth import Actor, actor
from app.core.errors import ok
from app.core.validation import ValidationFailed
from app.database.connection import get_db
from app.security.rate_limit import rate_limit

log = logging.getLogger("smartration.assistant")
router = APIRouter(prefix="/api/assistant", tags=["assistant"])
signed_in = actor()
assistant_limit = Depends(rate_limit("assistant", lambda s: s.chatbot_rate_limit_per_minute))


class UnderstandRequest(BaseModel):
    text: str | None = Field(None, description=f"What the user said or typed, up to {MAX_MESSAGE_LENGTH} characters.")
    language: str | None = Field("en", description="en | hi | mr: the app's language (Devanagari text is detected)")
    screen: str | None = Field(None, description="The screen the user is on, e.g. 'complaint_form' or 'token'", max_length=40)


@router.post("/understand", summary="Turn what the user said into one checked action (open a screen, pre-fill a form, or answer)",
             dependencies=[assistant_limit])
async def understand(body: UnderstandRequest, request: Request, who: Actor = Depends(signed_in), db: Session = Depends(get_db)):
    text = clean_input(body.text or "")
    if not text:
        raise ValidationFailed(["Text: Please say or type what you need."])
    if len((body.text or "").strip()) > MAX_MESSAGE_LENGTH:
        raise ValidationFailed([f"Text: Please keep it under {MAX_MESSAGE_LENGTH} characters."])
    language = body.language if body.language in LANGUAGES else "en"
    started = time.perf_counter()
    chat = get_provider(request.app.state.settings.chatbot_provider)
    result = await run_in_threadpool(service.understand, db, who, chat, text, language, (body.screen or "")[:40] or None)
    # Outcome only, never the words (they may contain personal details).
    log.info("assistant", extra={"fields": {
        "intent": result["intent"], "action": result["action"], "language": result["language"], "role": who.role.name,
        "by": result["understoodBy"], "chars": len(text), "duration_ms": round((time.perf_counter() - started) * 1000, 1),
    }})
    return ok(result)
