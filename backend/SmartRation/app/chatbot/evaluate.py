"""Score the Public Help assistant against the evaluation set.

    .venv/Scripts/python -m app.chatbot.evaluate          (run from backend/SmartRation)

Prints accuracy per language for retrieval ("does the question reach the right article?") and
for the safety rules ("is a private/sensitive/health question handled as such?"), lists every
miss, and exits 1 if anything misses — so content changes (or a future LLM provider) can be
judged the same way.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from app.chatbot.engine import Assistant
from app.chatbot.knowledge_base import load

EVALUATION = Path(__file__).resolve().parents[4] / "ai" / "chatbot" / "evaluation" / "questions.json"


def evaluate(assistant: Assistant, cases: dict) -> tuple[dict[str, list[int]], list[str]]:
    score: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # label -> [passed, total]
    misses: list[str] = []
    for case in cases["answers"]:
        reply = assistant.reply(case["message"], case["language"])
        ok = reply.kind == "answer" and reply.article_id == case["expected_article"]
        label = f"answers/{case['language']}"
        score[label][0] += ok
        score[label][1] += 1
        if not ok:
            misses.append(f"{case['message']!r} [{case['language']}] -> {reply.kind}/{reply.article_id}, expected {case['expected_article']}")
    for case in cases["safety"]:
        reply = assistant.reply(case["message"], case["language"])
        ok = reply.kind == case["expected_kind"]
        label = f"safety/{case['language']}"
        score[label][0] += ok
        score[label][1] += 1
        if not ok:
            misses.append(f"{case['message']!r} [{case['language']}] -> {reply.kind}, expected {case['expected_kind']}")
    return score, misses


def main() -> int:
    cases = json.loads(EVALUATION.read_text(encoding="utf-8"))
    score, misses = evaluate(Assistant(load()), cases)
    for label in sorted(score):
        passed, total = score[label]
        print(f"{label:<14} {passed:>3}/{total:<3} {100 * passed / total:5.1f}%")
    for miss in misses:
        print("MISS", miss)
    print("EVALUATION PASSED" if not misses else f"EVALUATION FAILED ({len(misses)} misses)")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
