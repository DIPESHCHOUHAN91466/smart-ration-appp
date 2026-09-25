# Frontend architecture

React 18 + Vite 6, JavaScript (not TypeScript — the existing app is JS; converting is possible later
file by file). UI only: no business rules and no direct `fetch`/`axios` calls in components.

```
frontend/src/
├── App.jsx            routes + route guards; mounts the chatbot once
├── main.jsx           entry
├── pages/             one folder per area: landing/, public-help/, rural/ (citizen), shop/,
│                      government/ (officials + admin), shared/, status/ (dev only), Login, Register, NotFound
├── layouts/           DashboardLayout (sidebar, header, language, QR scanner host)
├── components/        reusable UI: chatbot/, layout/ (public header/footer), qr/, verification/, ai/, common widgets
├── services/          ALL API calls — api.js (axios client: base URL, JWT, refresh on 401, error normalising)
│                      + one module per area (rationService, qrService, chatbotService, …)
├── store/             Zustand: auth (tokens, user), preferences, QR scanner, chatbot open state
├── hooks/             useChatbot, useQrScanner, useOnlineStatus
├── i18n/              translations.js (+ publicStrings.js): en / hi / mr, useTranslation()
├── context/           ToastContext
├── routes/            ProtectedRoute, roleHome
├── qr/                QR payload contract
└── assets/            logos, chatbot SVGs
tests/unit/            Vitest + Testing Library
```

**Folder names** follow the existing app (e.g. `pages/rural` is the citizen area, `pages/shop` the
ration-shop area). They were kept on purpose (2026-09-25) rather than renamed to a template layout —
renaming would touch most files for no functional gain.

## Data flow

Component → `services/<area>Service.js` → `api.js` (adds `Authorization`, retries once after refreshing
the token on 401) → Python API `:8000` → (proxy) C# API. Errors come back normalised
(`{message, status, errors}`) and are shown as friendly messages/toasts, never raw exceptions.

## Routing and access

Public: `/`, `/help`, `/login`, `/register`, `/profile/:ref`. Protected by role: `/rural/*` (citizen),
`/shop/*` (shop owner), `/gov/*` (official + admin). `/status` only in development builds.
Route guards are convenience only — the backend enforces every permission.

## Internationalisation

`useTranslation()` → `t("key")` over one dictionary (`translations.js`, with the public-page/chatbot
strings in `publicStrings.js`). English is the fallback. Tests fail if a key is missing in hi or mr.
Known gap: 41 older dashboard components still have English text inline.

## Performance

Route-level lazy loading for the QR scanner, map, landing, help and status pages. Main bundle ≈ 520 KB
(above Vite's 500 KB advisory) — next step: lazy-load the chatbot window and split translations.
