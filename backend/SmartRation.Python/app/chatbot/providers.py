"""Chat providers. Selected by the CHATBOT_PROVIDER setting.

* "knowledge" (default): the retrieval assistant in engine.py — answers only from reviewed
  articles and public database facts. No external calls, no API key.

Adding a generative model later: implement `ChatProvider.reply` so it (1) runs the same safety
checks first (reuse `Assistant.reply` for anything that isn't kind="answer"/"fallback"),
(2) grounds the model on the articles returned by `Assistant.search`, and (3) never passes user
records to the model. Read the key from CHATBOT_API_KEY; never log prompts or completions.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.chatbot.engine import Assistant, PublicData, Reply
from app.chatbot.knowledge_base import get_knowledge_base


class ChatProvider(Protocol):
    name: str

    def reply(self, message: str | None, language: str | None, data: PublicData | None,
              topic: str | None = None, article_id: str | None = None) -> Reply: ...

    def welcome(self, language: str) -> Reply: ...


class KnowledgeBaseProvider:
    name = "knowledge"

    def __init__(self) -> None:
        self.assistant = Assistant(get_knowledge_base())

    def reply(self, message, language, data, topic=None, article_id=None) -> Reply:
        return self.assistant.reply(message, language, data, topic=topic, article_id=article_id)

    def welcome(self, language: str) -> Reply:
        return self.assistant.welcome(language)


class UnsupportedProvider(RuntimeError):
    pass


@lru_cache
def get_provider(name: str) -> ChatProvider:
    if name in ("", "knowledge"):
        return KnowledgeBaseProvider()
    raise UnsupportedProvider(
        f"CHATBOT_PROVIDER={name!r} is not available. Supported: 'knowledge'. "
        "See app/chatbot/providers.py for how to add a generative provider."
    )
