"""Public Help and the Public Help chatbot — no login required.

  GET  /api/public-help/categories        sections of the help page, with their articles
  GET  /api/public-help/articles/{id}     one article (plus live public data where relevant)
  GET  /api/public-help/search?q=         search the help content
  GET  /api/chatbot/welcome               the assistant's greeting and quick buttons
  POST /api/chatbot/message               ask the assistant

Privacy: these routes never read personal data, ignore any Authorization header, and never log
message text (only the outcome, language and length). Rate-limited per client IP.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.chatbot.engine import MAX_MESSAGE_LENGTH, Reply
from app.chatbot.knowledge_base import LANGUAGES, get_knowledge_base
from app.chatbot.providers import get_provider
from app.core.errors import NotFound, ok
from app.core.rate_limit import rate_limit
from app.core.validation import ValidationFailed
from app.db.database import get_db
from app.services.public_help_service import DatabasePublicData

log = logging.getLogger("smartration.chatbot")
router = APIRouter(tags=["public help"])

chat_limit = Depends(rate_limit("chatbot", lambda s: s.chatbot_rate_limit_per_minute))
help_limit = Depends(rate_limit("public-help", lambda s: s.public_help_rate_limit_per_minute))
Language = Query("en", description="en | hi | mr (anything else falls back to en)", max_length=5)


class ChatRequest(BaseModel):
    message: str | None = Field(None, description=f"The question, up to {MAX_MESSAGE_LENGTH} characters.")
    language: str | None = Field("en", description="en | hi | mr — the interface language; Devanagari messages are detected")
    topic: str | None = Field(None, description="A quick-button category id instead of a message (e.g. 'documents')")
    articleId: str | None = Field(None, description="Open a specific article (e.g. from 'related')")


def _lang(value: str | None) -> str:
    return value if value in LANGUAGES else "en"


def _reply_dto(reply: Reply) -> dict:
    d = asdict(reply)
    return {
        "kind": d["kind"], "language": d["language"], "text": d["text"], "articleId": d["article_id"],
        "title": d["title"], "links": d["links"], "suggestions": d["suggestions"], "related": d["related"],
        "requiresLogin": d["requires_login"], "confidence": d["confidence"],
    }


@router.get("/api/public-help/categories", summary="Public Help sections and their articles", dependencies=[help_limit])
def categories(language: str = Language):
    lang, kb = _lang(language), get_knowledge_base()
    return ok([
        {"id": c.id, "icon": c.icon, "title": c.title[lang], "description": c.description[lang], "ask": c.ask[lang],
         "primaryArticle": c.primary,
         "quick": c.quick, "articles": [{"id": a.id, "title": a.title[lang]} for a in kb.by_category[c.id]]}
        for c in kb.categories
    ])


@router.get("/api/public-help/articles/{article_id}", summary="One Public Help article", dependencies=[help_limit])
async def article(article_id: str, language: str = Language, db: Session = Depends(get_db)):
    provider = get_provider("knowledge")
    reply = await run_in_threadpool(provider.reply, None, _lang(language), DatabasePublicData(db), None, article_id[:64])
    if reply.kind != "answer":
        raise NotFound("Help article not found.")
    return ok(_reply_dto(reply))


@router.get("/api/public-help/search", summary="Search Public Help", dependencies=[help_limit])
def search(q: str = Query(..., min_length=1, max_length=100), language: str = Language):
    provider = get_provider("knowledge")
    return ok(provider.assistant.search(q, _lang(language)))  # type: ignore[attr-defined]


@router.get("/api/chatbot/welcome", summary="Assistant greeting and quick buttons", dependencies=[help_limit])
def welcome(request: Request, language: str = Language):
    provider = get_provider(request.app.state.settings.chatbot_provider)
    return ok(_reply_dto(provider.welcome(_lang(language))))


@router.post("/api/chatbot/message", summary="Ask the Public Help assistant", dependencies=[chat_limit],
             responses={400: {"description": "Empty or too-long message"}, 429: {"description": "Rate limited"}})
async def message(body: ChatRequest, request: Request, db: Session = Depends(get_db)):
    text = (body.message or "").strip()
    if not text and not body.topic and not body.articleId:
        raise ValidationFailed(["Message: Please type a question."])
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValidationFailed([f"Message: Please keep your question under {MAX_MESSAGE_LENGTH} characters."])

    started = time.perf_counter()
    provider = get_provider(request.app.state.settings.chatbot_provider)
    reply = await run_in_threadpool(provider.reply, text, _lang(body.language), DatabasePublicData(db),
                                    (body.topic or "")[:40] or None, (body.articleId or "")[:64] or None)
    # Outcome only — never the message itself (it may contain personal data despite our warnings).
    log.info("chatbot reply", extra={"fields": {
        "kind": reply.kind, "article": reply.article_id, "language": reply.language, "chars": len(text),
        "via": "topic" if body.topic else "article" if body.articleId else "message",
        "confidence": reply.confidence, "duration_ms": round((time.perf_counter() - started) * 1000, 1),
    }})
    return ok(_reply_dto(reply))
