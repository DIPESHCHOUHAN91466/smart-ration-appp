# frontend/tests — component tests (Vitest + Testing Library)

**What:** automated tests that render components in a simulated browser (jsdom). **Why:** catch UI
regressions (chatbot behaviour, safety, translations) before a person does.
**Belongs here:** `unit/*.test.jsx` (components, hooks, formatting), `setup.js` (resets stores and
storage). `integration/` and `e2e/` (Playwright) are planned — none exist yet.
**Doesn't:** backend or database tests (those live with each backend).
**Run:** `npm test` (in `frontend`). **Connects:** API modules are mocked with `vi.spyOn`, so no server is needed.

Current: `chatbot.test.jsx` (18), `publicPages.test.jsx` (9), `messageText.test.jsx` (4),
`i18n.test.js` (3), `statusPage.test.jsx` (2).
