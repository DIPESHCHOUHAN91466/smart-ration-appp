"""The Public Help assistant: safety checks first, then retrieval over the knowledge base.

Deterministic and explainable: every answer is a reviewed article (plus live public data such
as the shop list), never generated text. That keeps it honest about what it knows and makes it
impossible for it to reveal data it was never given. A generative model can be added later
behind `ChatProvider` (app/chatbot/providers.py), grounded on the same articles.

Pipeline for each message (one module per step):
  text.py       clean the input, normalise it, detect the language
  intents.py    safety and intent rules (sensitive input, internals, own records, health, greetings)
  retrieval.py  knowledge-base search -> best article, or a helpful fallback
  responses.py  the Reply model and answer text (live shop/scheme lists, signed-in booking lines)
  engine.py     this file: orchestrates the steps; data arrives only through the Protocols below
"""

from __future__ import annotations

from typing import Protocol

from app.chatbot.intents import classify, is_about_bookings
from app.chatbot.knowledge_base import LANGUAGES, Article, KnowledgeBase
from app.chatbot.responses import Reply, bookings_reply, schemes_text, shops_text, verification_reply
from app.chatbot.retrieval import ANSWER_THRESHOLD, Retriever
from app.chatbot.text import clean_input, detect_language, normalize


class PublicData(Protocol):
    """Public, non-personal facts the assistant may include (read from the database)."""

    def shops(self) -> list[dict]: ...  # {name, address, village, taluka, district}

    def schemes(self) -> list[dict]: ...  # {code, name, items: [{name, vernacular, unit, quota}]}


class PersonalData(Protocol):
    """The signed-in citizen's OWN records, available only with a valid access token."""

    def upcoming_bookings(self) -> list[dict]: ...  # {id, token, date, start, end, shop, status}


class Assistant:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.retriever = Retriever(kb)

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

        intent = classify(text, norm, tokens, lambda: bool(self.retriever.scores(norm, tokens)))
        if intent == "own_records":
            if personal is not None:
                return self._personal(set(tokens), lang, personal)
            reply = self._fixed("private_data", lang)
            reply.requires_login = True
            reply.links = [{"path": "/login", "label": {"en": "Log in securely", "hi": "सुरक्षित लॉग इन करें", "mr": "सुरक्षित लॉग इन करा"}[lang]}]
            return reply
        if intent is not None:
            return self._fixed(intent, lang)

        scored = self.retriever.scores(norm, tokens)
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
        for score, article in self.retriever.scores(norm, norm.split()):
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
        if is_about_bookings(token_set):
            return bookings_reply(personal.upcoming_bookings(), lang)
        return verification_reply(lang)

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
