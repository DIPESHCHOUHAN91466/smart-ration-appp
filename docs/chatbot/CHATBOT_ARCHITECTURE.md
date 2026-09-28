# Ration Mitra AI Assistant (Public Help chatbot)

A floating assistant (bottom-right on every page except the full-screen QR scanner) that answers
public questions about ration cards, eligibility, documents, tokens and slots, QR/OTP verification,
collection, rights and support — in English, हिंदी and मराठी, without login.

## What it is — and isn't

It is a **retrieval assistant**: every answer is a reviewed article from the knowledge base, plus
live *public* facts from the database (active shops, scheme quotas). It does not generate text and
calls no external AI service, so it cannot invent facts or reveal data it was never given.
It is branded "AI Assistant" as the product name; the design leaves room for a generative model
later (see *Adding an LLM*), but none is used today.

## Architecture

```
ChatbotWidget (React) ─► POST /api/chatbot/message ─► providers.get_provider(CHATBOT_PROVIDER)
                         GET  /api/chatbot/welcome       └─ KnowledgeBaseProvider ─► engine.Assistant
Public Help page ──────► GET  /api/public-help/*              ├─ safety checks (order below)
                                                              ├─ search over knowledge/*.json
                                                              └─ PublicData (shops, schemes; cached 5 min)
```

| Where | What |
|---|---|
| `ai/chatbot/knowledge/public-help.json` | help categories (quick buttons) + fixed replies (welcome, fallback, privacy, health…) |
| `…/knowledge/ration-help.json` | how this app works (register, book, token, QR, OTP, collection, login help) |
| `…/knowledge/faq.json` | ration cards: what, types, applying, documents, eligibility, changes, lost card, rights, complaints, support |
| `…/knowledge/schemes.json` | NFSA, free foodgrain (PMGKAY), One Nation One Ration Card, this installation's demo schemes |
| `app/ai/chatbot/knowledge_base.py` | loads + validates (every text in en/hi/mr, valid categories, in-app links only) at startup |
| `app/ai/chatbot/text.py` | input clean-up, normalisation (Devanagari variants), language detection |
| `app/ai/chatbot/intents.py` | safety and intent rules, in order: sensitive input, internals, own records, health, greeting, thanks |
| `app/ai/chatbot/retrieval.py` | knowledge-base scoring (keywords, title words, inflections, typos) |
| `app/ai/chatbot/responses.py` | the `Reply` model and all text assembled in code (bookings, shop and scheme lists) |
| `app/ai/chatbot/engine.py` | orchestration only (`Assistant`); data arrives through the `PublicData` / `PersonalData` protocols, never directly from the database |
| `app/ai/chatbot/providers.py` | `ChatProvider` interface; `CHATBOT_PROVIDER=knowledge` |
| `app/api/routes/public_help.py` | the five public routes |
| `frontend/src/components/chatbot/` | widget, window, header, message, input, suggestions, avatar, CSS |
| `frontend/src/hooks/useChatbot.js` | conversation state (sessionStorage) |
| `frontend/src/assets/ration-mitra-emblem.png` | the emblem cropped from the supplied logo (`ration-mitra-logo.webp`); chatbot avatar + launcher (Logo 2), header (Logo 1), favicon |

## Safety rules (checked before any search)

1. **Sensitive input** — an Aadhaar-like 12-digit number, an OTP with digits, or "password is …" →
   a warning not to share them; the message isn't processed further.
2. **Internals / other people's data** — "system prompt", "ignore previous instructions", "API key",
   "SQL", "show all users", "aadhaar of …" → a polite refusal.
3. **The user's own records** — "my token / booking / family / Aadhaar / OTP…" (without a how-to
   word) → "please log in securely" with a login button. The public chat never reads personal data,
   and it ignores any `Authorization` header.
4. **Health** — general guidance (PHC, ASHA, Anganwadi/ICDS, balanced diet), never diagnosis;
   emergency numbers 112 / 108.
5. Greetings and thanks.

Then the search picks the best article, or answers with a fallback and the quick buttons.

**Logging:** each reply logs its kind, article id, language, message length, confidence and duration
— never the message text. **Rate limits:** 30 messages/minute and 120 help requests/minute per client
IP (`CHATBOT_RATE_LIMIT_PER_MINUTE`, `PUBLIC_HELP_RATE_LIMIT_PER_MINUTE`). **Output:** plain text; the
frontend renders paragraphs and lists as React text nodes (no HTML) and only in-app links.

## Search

Normalisation (lower-case, punctuation removed, Devanagari nukta/chandrabindu variants unified) →
keyword scoring: phrase match 3, word match 2, inflection prefix 1.2, English typo (difflib) 1.8,
distinctive title words 0.5; `~keyword` marks generic nouns ("ration card", "shop") at half weight.
Threshold 2.0. The interface language decides the reply language; Devanagari messages are detected as
Hindi or Marathi from marker words.

## Editing content

1. Edit the JSON in `app/ai/chatbot/knowledge/` — every `title` / `answer` needs `en`, `hi` and `mr`.
   Lines starting with `• ` or `1. ` become lists. Links must be in-app paths (`/register`).
2. Add keywords users would actually type, in all three languages and romanised Hindi.
3. Add the question to `QUESTIONS` in `tests/unit/test_chatbot_engine.py` and run the tests — they fail if
   a translation is missing or a question lands on the wrong article.
4. Facts about the app must match the code (booking rules, OTP limits); general scheme facts stay
   hedged ("in many states", "check your state's portal") and should be reviewed before a public launch.

## Adding an LLM (future)

Implement `ChatProvider` in `providers.py`: run `Assistant.reply` first and return it unless it is
`answer`/`fallback` (keeps every safety rule), ground the model on `Assistant.search` results, never
send user records, read `CHATBOT_API_KEY` from the environment, and never log prompts or completions.
Unknown `CHATBOT_PROVIDER` values stop the app at startup.

## Tests

- Backend: `tests/unit/test_chatbot_engine.py` (66: 32 real questions in 3 languages, safety rules, language
  detection, knowledge integrity) and `tests/api/test_public_help_api.py` (16: routes, validation, privacy,
  no message text in logs, rate limit, XSS input, startup check).
- Frontend: `tests/unit/chatbot.test.jsx` (17: open/close, quick actions, typed messages, failure + retry,
  rate limit, markup safety, private-data reply, related topics, Esc + focus, expand, clear, search,
  open from any page, hidden on the scanner), `messageText.test.jsx`, `i18n.test.js`, `publicPages.test.jsx`.
- Mobile layout: verified in the browser at 375×812 (bottom sheet, touch-size controls); not unit-tested
  (jsdom has no layout).
