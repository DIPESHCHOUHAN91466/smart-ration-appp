# frontend/e2e — End-to-End Browser Tests (Playwright)

Automated end-to-end browser tests verifying user-facing journeys, accessibility, language localization, and API interactions in real Chromium/WebKit/Firefox instances.

## Overview

These tests exercise the full client-server stack without mocking the API.

| Spec File | Coverage |
|---|---|
| `smoke.spec.js` | Landing page layout and Ration Mitra branding, multi-language switching (English, Hindi, Marathi) with persistence across page reloads, Public Help knowledge base topic expansion, live chatbot Q&A with Aadhaar leak detection & refusal, authentication route guards (redirecting unauthenticated users to `/login`), status dashboard verification, and 404 handling |
| `mobile.spec.js` | Mobile viewport compatibility (iPhone/Android dimensions), mobile navigation toggling, responsive modal dialogues, and responsive touch controls |

## Prerequisites

The full application stack should be running:
- Frontend on `http://localhost:5173`
- Python API Gateway on `http://127.0.0.1:8000`
- C# Business API on `http://localhost:5188`

## Running E2E Tests

From the `frontend` directory:
```bash
npm run test:e2e
```

To run with interactive UI mode:
```bash
npx playwright test --ui
```

To run on a specific browser:
```bash
npx playwright test --project=chromium
```

From the repository root using the developer CLI:
```powershell
.\sr.ps1 e2e
```
