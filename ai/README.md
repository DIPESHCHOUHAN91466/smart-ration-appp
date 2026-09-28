# ai — AI assets (content, evaluation, prompts)

**What is this?** The *non-code* side of Smart Ration's AI: the chatbot's knowledge base, its
evaluation set, and prompt templates for a future language model.

**Why does it exist?** AI behaviour is decided as much by content and evaluation as by code. Keeping
them here lets content be reviewed and improved (by non-programmers too) without touching the engine,
and every change is measured against the same evaluation set.

**What belongs here:** `chatbot/knowledge/*.json` (reviewed answers in en/hi/mr),
`chatbot/evaluation/questions.json` (questions with the expected answer or safety behaviour),
`chatbot/prompts/` (templates for a future LLM provider). **What does NOT:** code — the chatbot engine
is in `backend/SmartRation/app/ai/chatbot`, the analytics service in `backend/SmartRation.AI`;
personal data of any kind.

**How do I run it?**
```
cd backend\SmartRation
.venv\Scripts\python -m app.ai.chatbot.evaluate     # score the assistant on the evaluation set
.venv\Scripts\python -m pytest tests\unit\test_chatbot_engine.py
```

**How does it connect?** The Python API loads `chatbot/knowledge` at startup (path overridable with
`CHATBOT_KNOWLEDGE_DIR`; the Docker image copies it in). Tests and the evaluator read
`chatbot/evaluation`.

No trained model files exist (`models/`, `embeddings/` would hold them): the analytics use statistical
methods and the chatbot uses keyword retrieval. Architecture:
[../docs/architecture/AI_ARCHITECTURE.md](../docs/architecture/AI_ARCHITECTURE.md).
