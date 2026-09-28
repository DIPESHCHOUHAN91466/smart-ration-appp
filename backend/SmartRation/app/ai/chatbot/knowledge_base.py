"""Loads and validates the Public Help knowledge base (<repo>/ai/chatbot/knowledge/*.json).

The content is data, not code: reviewed in git, loaded once at startup, and validated so a
missing translation or a broken category reference fails fast (and in the test suite) instead
of showing a half-empty answer to a citizen.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

LANGUAGES = ("en", "hi", "mr")
# The knowledge lives outside the code, in <repo>/ai/chatbot/knowledge (content is reviewed
# separately from code). CHATBOT_KNOWLEDGE_DIR overrides it (e.g. in the Docker image).
KNOWLEDGE_DIR = Path(os.environ.get("CHATBOT_KNOWLEDGE_DIR") or Path(__file__).resolve().parents[5] / "ai" / "chatbot" / "knowledge")
ARTICLE_FILES = ("ration-help.json", "faq.json", "schemes.json")
RESPONSE_KEYS = ("welcome", "greeting", "thanks", "fallback", "private_data", "sensitive_input", "internal", "health")


class KnowledgeError(ValueError):
    pass


@dataclass(frozen=True)
class Link:
    path: str
    label: dict[str, str]


@dataclass(frozen=True)
class Article:
    id: str
    category: str
    keywords: tuple[str, ...]            # "~word" = weak keyword (generic nouns like "ration card"), half weight
    title: dict[str, str]
    answer: dict[str, str]
    dynamic: str | None = None
    links: tuple[Link, ...] = ()


@dataclass(frozen=True)
class Category:
    id: str
    icon: str
    primary: str
    quick: bool
    title: dict[str, str]
    description: dict[str, str]
    ask: dict[str, str]


@dataclass(frozen=True)
class KnowledgeBase:
    categories: tuple[Category, ...]
    articles: dict[str, Article]
    responses: dict[str, dict[str, str]]
    by_category: dict[str, list[Article]] = field(default_factory=dict)


def _texts(obj: dict, what: str) -> dict[str, str]:
    missing = [lang for lang in LANGUAGES if not str(obj.get(lang, "")).strip()]
    if missing:
        raise KnowledgeError(f"{what}: missing text for {missing}")
    return {lang: str(obj[lang]).strip() for lang in LANGUAGES}


def _read(directory: Path, name: str) -> dict:
    with open(directory / name, encoding="utf-8") as fh:
        return json.load(fh)


def load(directory: Path = KNOWLEDGE_DIR) -> KnowledgeBase:
    help_data = _read(directory, "public-help.json")

    categories = tuple(
        Category(id=c["id"], icon=c["icon"], primary=c["primary"], quick=bool(c.get("quick")),
                 title=_texts(c["title"], f"category {c['id']} title"),
                 description=_texts(c["description"], f"category {c['id']} description"),
                 ask=_texts(c["ask"], f"category {c['id']} ask"))
        for c in help_data["categories"]
    )
    responses = {key: _texts(help_data["responses"].get(key, {}), f"response {key}") for key in RESPONSE_KEYS}

    articles: dict[str, Article] = {}
    for name in ARTICLE_FILES:
        for a in _read(directory, name)["articles"]:
            if a["id"] in articles:
                raise KnowledgeError(f"duplicate article id {a['id']}")
            links = tuple(Link(path=link["path"], label=_texts(link["label"], f"{a['id']} link")) for link in a.get("links", []))
            if any(not link.path.startswith("/") or link.path.startswith("//") for link in links):
                raise KnowledgeError(f"{a['id']}: links must be in-app paths")
            if not a.get("keywords"):
                raise KnowledgeError(f"{a['id']}: needs keywords")
            articles[a["id"]] = Article(
                id=a["id"], category=a["category"], keywords=tuple(k.lower() for k in a["keywords"]),
                title=_texts(a["title"], f"{a['id']} title"), answer=_texts(a["answer"], f"{a['id']} answer"),
                dynamic=a.get("dynamic"), links=links,
            )

    category_ids = {c.id for c in categories}
    for c in categories:
        if c.primary not in articles:
            raise KnowledgeError(f"category {c.id}: primary article {c.primary} not found")
    for a in articles.values():
        if a.category not in category_ids:
            raise KnowledgeError(f"{a.id}: unknown category {a.category}")
        if a.dynamic not in (None, "shops", "schemes"):
            raise KnowledgeError(f"{a.id}: unknown dynamic source {a.dynamic}")

    by_category: dict[str, list[Article]] = {c.id: [] for c in categories}
    for a in articles.values():
        by_category[a.category].append(a)
    return KnowledgeBase(categories=categories, articles=articles, responses=responses, by_category=by_category)


@lru_cache
def get_knowledge_base() -> KnowledgeBase:
    return load()
