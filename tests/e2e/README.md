# tests/e2e — End-to-End Browser Tests (Playwright)

Automated end-to-end browser tests verifying user-facing journeys, accessibility, language localization, and API interactions in the Microsoft Edge installed on Windows (Playwright `channel: "msedge"`, no browser download).

## Overview

These tests exercise the full client-server stack without mocking the API.

| Spec File | Coverage |
|---|---|
| `smoke.spec.js` | Landing page layout and Ration Mitra branding, multi-language switching (English, Hindi, Marathi) with persistence across page reloads, Public Help knowledge base topic expansion, live chatbot Q&A with Aadhaar leak detection & refusal, authentication route guards (redirecting unauthenticated users to `/login`), status dashboard verification, and 404 handling |
| `mobile.spec.js` | Phone viewport (Pixel 7): no sideways scrolling, the mobile menu opens, the chatbot opens as a full-width bottom sheet |

## Prerequisites

The full application stack should be running:
- Frontend on `http://localhost:5173`
- Python API on `http://127.0.0.1:8000`, started for the test run with a higher sign-in limit:
  `AUTH_RATE_LIMIT_PER_MINUTE=60` (in the API's environment, not committed). Every test signs in or registers from the
  same address, and the default limit (10 a minute per address) would answer some of them `429 Too Many Requests`.
  Never raise it on a deployed server.
- AI analytics service on `http://127.0.0.1:8001` (the status-page test expects every configured service to be healthy)
- `E2E_DEMO_PASSWORD` set to the demo accounts' password (the signed-in journeys are skipped without it)

The tests run one at a time (`workers: 1` in `playwright.config.js`): they share the demo accounts, and a password
change signs an account out everywhere, so spec files running in parallel would break each other.

## Running E2E Tests

This folder is a small Node project of its own (`package.json`, `playwright.config.js`), so the browser tests of
the whole system don't live inside one app. From `tests/e2e`:
```bash
npm install        # first time only (setup.ps1 does it too)
npm test
```
(`npm run test:e2e` in `frontend/` forwards here.)

To run with interactive UI mode:
```bash
npx playwright test --ui
```

To run only one project (`desktop` or `mobile`):
```bash
npx playwright test --project=desktop
```

To use Playwright's own Chromium instead of Edge: `npx playwright install chromium`, then set `E2E_BROWSER=chromium`.

Nothing in these tests signs in or types a password; they cover public pages, the chatbot, the login form's presence and the protected-route redirect.

From the repository root using the developer CLI:
```powershell
.\sr.ps1 e2e
```
