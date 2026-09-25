# ai/chatbot — knowledge and evaluation for the Smart Ration AI Assistant

**What:** the content the assistant answers from, and the test questions that keep it honest.
**Why:** the assistant must never invent government policy — it can only say what is written and
reviewed here. **Belongs here:** reviewed public information in English, Hindi and Marathi; evaluation
cases; prompt templates. **Doesn't:** code, personal data, anything unverified.

| Path | Content |
|---|---|
| `knowledge/public-help.json` | 12 help categories (quick buttons) + fixed replies (welcome, fallback, privacy, health, …) |
| `knowledge/ration-help.json` | how this app works: register, book a slot, token, QR, OTP, collection, login help |
| `knowledge/faq.json` | ration cards: what, types, applying, documents, eligibility, changes, lost card, rights, complaints, support |
| `knowledge/schemes.json` | NFSA, free foodgrain (PMGKAY), One Nation One Ration Card, this installation's demo schemes |
| `evaluation/questions.json` | 48 retrieval + 19 safety cases (en/hi/mr) |
| `prompts/system-prompt.md` | template for a future LLM provider (not used today) |

**Editing content:** keep every `title`/`answer` in `en`, `hi`, `mr`; lines starting `• ` or `1. `
become lists; links must be in-app paths (`/register`); general scheme facts stay hedged ("check your
state's portal"). Add real user questions to `evaluation/questions.json`, then run
`python -m app.chatbot.evaluate` (from `backend/SmartRation.Python`) — it must stay at 100%.
The app refuses to start if a translation is missing.

**Connects:** loaded by `backend/SmartRation.Python/app/chatbot/knowledge_base.py`.
Design: [../../docs/chatbot/CHATBOT_ARCHITECTURE.md](../../docs/chatbot/CHATBOT_ARCHITECTURE.md).
