# src/store — client state (Zustand)

**What:** small global stores. **Why:** state shared by distant components without prop drilling.
**Belongs here:** `authStore` (user, tokens, refresh), `preferencesStore`, `qrScannerStore` (open the
scanner from anywhere), `chatbotStore` (open the assistant with a question). **Doesn't:** server data
caches or business logic. **Run/test:** reset between tests in `frontend/tests/setup.js`.
**Connects:** read by components/hooks; `authStore` is used by `services/api.js` for the JWT.
Security note: `authStore` persists tokens in `localStorage` — moving the refresh token to an HttpOnly
cookie is an open item (docs/security).
