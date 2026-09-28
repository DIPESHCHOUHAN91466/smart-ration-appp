# src/services — every API call

**What:** one module per backend area (`rationService`, `qrService`, `inventoryService`,
`chatbotService`, …). **Why:** components never talk HTTP directly, so URLs, auth headers and error
handling live in one place.
**Belongs here:** request functions that return plain data. **Doesn't:** UI, state, business rules, the
HTTP client itself (that is `src/api/client.js`).
**Run/test:** used by pages and hooks; mocked in component tests (`vi.spyOn(chatbotService, "send")`).
**Connects:** each module calls `apiClient` / `unwrap` from `../api/client` → base URL from
`../config/env.js` (`VITE_API_BASE_URL`, the Python API `:8000/api/v1`; unset: localhost in dev, same-origin
`/api/v1` in production builds; a bare `/api` gets `/v1` added — rules in `api/baseUrl.js`). The client adds
the JWT, refreshes it once on a 401, sends you to `/login` if that fails, and turns errors into
`{message, status, errors}` (typed in `src/types/api.js`).
