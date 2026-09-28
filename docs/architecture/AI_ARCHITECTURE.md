# AI architecture

Two AI features, both explainable and neither able to invent facts or see data it shouldn't.

## 1. Public Help assistant (chatbot)

```
UI (ChatbotWidget) → POST /api/chatbot/message → ChatProvider (CHATBOT_PROVIDER=knowledge)
   → safety checks (sensitive input · internals/other people · own records · health · greeting)
   → intent/knowledge retrieval over ai/chatbot/knowledge/*.json (en/hi/mr)
   → + live public data (shops, scheme quotas) or the signed-in citizen's own bookings
   → safe response (plain text, in-app links only)
```

| Asset | Where |
|---|---|
| Knowledge (25 reviewed articles, 12 categories, fixed replies) | `ai/chatbot/knowledge/` |
| Evaluation set (48 retrieval + 19 safety cases; 100% today) | `ai/chatbot/evaluation/questions.json` |
| Prompt template for a future LLM provider (unused today) | `ai/chatbot/prompts/` |
| Code (engine, providers, evaluation runner) | `backend/SmartRation/app/ai/chatbot/` |

Provider abstraction (the brief's `IChatbotProvider`): `ChatProvider` in
`app/ai/chatbot/providers.py`. Implemented: **`KnowledgeBaseProvider`** (rules + retrieval). A
`LLMChatbotProvider` can be added without touching the frontend or the safety rules — see
[../chatbot/CHATBOT_ARCHITECTURE.md](../chatbot/CHATBOT_ARCHITECTURE.md#adding-an-llm-future).
Status of a generative provider: **BLOCKED — REQUIRES EXTERNAL INTEGRATION** (no provider or key).

## 2. Distribution analytics (AI service)

`ai` computes, from the distribution history (read-only):
demand forecasts (method chosen by rolling-origin backtest; no number below 14 days of data),
stock-out risk, queue prediction, anomaly alerts (low stock, forecast risk, demand spikes, unusual
consumption, inventory anomalies) persisted in `AIAlerts`, and optional OCR that pre-fills forms for
human confirmation (never identity verification). Statistical methods only — no trained ML model:
`ai/models/` holds the forecasting formulas (not weight files), `ai/training/` picks one per shop and item
by backtest, `ai/evaluation/` measures accuracy (`python -m ai.evaluation.report`, with `MODEL_VERSION`),
`ai/inference/` runs them. Every forecast carries `model_version`; `/health` reports `forecast_model`.

## Principles

- **No invented policy.** Answers come only from reviewed content; otherwise "I'm not able to verify
  that information. Please check the official government source or contact support."
- **Privacy.** Public chat never reads personal data; a signed-in citizen gets only their own booking.
- **Evaluation before change.** `python -m app.ai.chatbot.evaluate` must stay at 100% for content or
  provider changes.
- **Honest labels.** Forecasts carry data sufficiency and confidence; alerts are review prompts, not proof.
