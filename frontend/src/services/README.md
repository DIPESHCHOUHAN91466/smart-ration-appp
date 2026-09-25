# src/services — every API call

**What:** one module per backend area (`rationService`, `qrService`, `inventoryService`,
`chatbotService`, …) plus `api.js`, the shared axios client. **Why:** components never talk HTTP
directly, so URLs, auth headers and error handling live in one place.
**Belongs here:** request functions that return plain data. **Doesn't:** UI, state, business rules.
**Run/test:** used by pages and hooks; mocked in component tests (`vi.spyOn(chatbotService, "send")`).
**Connects:** `api.js` → `VITE_API_BASE_URL` (the Python API, `:8000/api`). It adds the JWT, refreshes it
once on a 401, sends you to `/login` if that fails, and turns errors into `{message, status, errors}`.
