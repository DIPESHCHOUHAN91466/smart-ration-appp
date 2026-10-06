# src/state — client state (Zustand) and toasts

**What:** small global stores. **Why:** state shared by distant components without prop drilling.
**Belongs here:** `authStore` (user, tokens, refresh), `preferencesStore`, `qrScannerStore` (open the
scanner from anywhere), `chatbotStore` (open the assistant with a question), `toast.js` (`useToast()`) and
`ToastProvider.jsx` (renders the notifications). **Doesn't:** server data caches or business logic.
**Run/test:** reset between tests in `frontend/tests/setup.js`.
**Connects:** read by components/hooks; `authStore` is used by `api/client.js` for the JWT.
Security note: `authStore` never persists a token. The refresh token is an HttpOnly cookie set by the API
(cookie mode, `X-Auth-Mode: cookie` from `api/client.js`); the access token is in memory only. See docs/security.
