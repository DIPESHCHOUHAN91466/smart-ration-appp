"""The assistant's one entry point: what the user said -> one checked action for the phone.

Order (safety first, nothing guessed):
  1. Aadhaar numbers, OTPs or passwords in the text -> the help assistant's refusal; nothing else runs.
  2. An understanding provider proposes an intent (rules today; an LLM later, same contract).
  3. The proposal is accepted only if the action is allowed for the caller's role (actions.py); form fields are
     kept only if they fit the form's schema. Anything else is answered by the verified help assistant.
  4. Answers about the user's own collection come from their real bookings (by user id from the token).
The assistant never writes data: forms are only pre-filled; the user reviews and submits them through the
normal API. The user's words are never logged.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.assistant.actions import FORMS, LANGUAGES, form_allowed, screen_allowed
from app.ai.assistant.understanding import RulesUnderstanding, Understanding, UnderstandingProvider
from app.ai.chatbot.intents import contains_sensitive
from app.ai.chatbot.providers import ChatProvider
from app.ai.chatbot.responses import bookings_reply, reply_dto
from app.ai.chatbot.text import detect_language
from app.api.dependencies.auth import Actor
from app.database.enums import UserRole
from app.services.public_help_service import DatabasePublicData, UserBookings

RULES = RulesUnderstanding()


def understand(db: Session, actor: Actor, chat: ChatProvider, text: str, language: str, screen: str | None,
               provider: UnderstandingProvider = RULES) -> dict:
    lang = detect_language(text, language)
    personal = UserBookings(db, actor.user_id) if actor.role == UserRole.RuralUser else None

    def answer(intent: str, reply=None) -> dict:
        reply = reply or chat.reply(text, lang, DatabasePublicData(db), personal=personal)
        return {"action": "answer", "intent": intent, "language": lang, "understoodBy": provider.name, "reply": reply_dto(reply)}

    if contains_sensitive(text):
        return answer("sensitive")

    u: Understanding = provider.understand(text, lang, screen)
    base = {"intent": u.intent, "language": lang, "understoodBy": provider.name}

    if u.intent == "navigate" and screen_allowed(u.target, actor.role):
        return {**base, "action": "navigate", "target": u.target}
    if u.intent == "fill_form" and form_allowed(u.target, actor.role):
        fields, missing = FORMS[u.target].draft(u.fields)
        return {**base, "action": "fill_form", "form": u.target, "fields": fields, "missing": missing}
    if u.intent == "change_language" and u.target in LANGUAGES:
        return {**base, "action": "change_language", "target": u.target}
    if u.intent in ("read_screen", "explain_screen"):
        return {**base, "action": u.intent}
    if u.intent == "collection_time" and personal is not None:
        return answer("collection_time", bookings_reply(personal.upcoming_bookings(), lang))
    # Not recognised, or not allowed for this role: the verified help assistant answers (or says it can't).
    return answer("ask")
