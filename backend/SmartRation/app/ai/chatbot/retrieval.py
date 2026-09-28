"""Knowledge-base retrieval: weighted keyword, title-word, inflection and typo matching.

Deterministic and explainable: an article's score is the sum of the matches listed in `scores`.
"""

from __future__ import annotations

import difflib

from app.ai.chatbot.knowledge_base import LANGUAGES, Article, KnowledgeBase
from app.ai.chatbot.text import STOPWORDS, normalize

ANSWER_THRESHOLD = 2.0


class Retriever:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        # (normalized keyword, weight): "~" marks generic nouns ("ration card", "shop") that appear in many
        # questions and shouldn't outweigh intent words ("apply", "documents", "less ration").
        self._keywords = {a.id: [(normalize(k.lstrip("~")), 0.5 if k.startswith("~") else 1.0) for k in a.keywords]
                          for a in kb.articles.values()}
        titles = {
            a.id: {t for lang in LANGUAGES for t in normalize(a.title[lang]).split() if t not in STOPWORDS and len(t) > 2}
            for a in kb.articles.values()
        }
        # Title words shared by many articles ("ration", "card", "shop") say nothing about intent.
        frequency: dict[str, int] = {}
        for tokens in titles.values():
            for t in tokens:
                frequency[t] = frequency.get(t, 0) + 1
        self._title_tokens = {aid: {t for t in tokens if frequency[t] <= 3} for aid, tokens in titles.items()}
        self._stop = {normalize(w) for w in STOPWORDS}

    def scores(self, norm: str, tokens: list[str]) -> list[tuple[float, Article]]:
        content = [t for t in tokens if t not in self._stop]
        if not content:
            return []
        latin = [t for t in content if t.isascii() and len(t) >= 5]
        scored = []
        for article in self.kb.articles.values():
            score = 0.0
            for kw, weight in self._keywords[article.id]:
                if kw == norm:
                    score += 2.0  # the whole question is this keyword ("ration card")
                if " " in kw:
                    if kw in norm:
                        score += 3.0 * weight
                elif kw in content:
                    score += 2.0 * weight
                elif len(kw) >= 3 and any(t.startswith(kw) or (len(t) >= 4 and kw.startswith(t)) for t in content):
                    score += 1.2 * weight  # inflections: documents/document, दस्तावेजों/दस्तावेज
                elif kw.isascii() and len(kw) >= 5 and latin and difflib.get_close_matches(kw, latin, n=1, cutoff=0.84):
                    score += 1.8 * weight  # typos: "eligiblity", "documnts"
            score += 0.5 * len(self._title_tokens[article.id] & set(content))
            if score > 0:
                scored.append((score, article))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored
