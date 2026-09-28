"""Request model of the Public Help chatbot endpoint (POST /api/public-help/chat).

FastAPI parses the body with it and publishes it in OpenAPI; field limits (message length,
languages) are enforced in the route and the chatbot engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ai.chatbot.text import MAX_MESSAGE_LENGTH


class ChatRequest(BaseModel):
    message: str | None = Field(None, description=f"The question, up to {MAX_MESSAGE_LENGTH} characters.")
    language: str | None = Field("en", description="en | hi | mr — the interface language; Devanagari messages are detected")
    topic: str | None = Field(None, description="A quick-button category id instead of a message (e.g. 'documents')")
    articleId: str | None = Field(None, description="Open a specific article (e.g. from 'related')")
