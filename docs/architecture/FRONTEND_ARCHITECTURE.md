# Frontend architecture

React 18 + Vite 6, JavaScript (not TypeScript — the existing app is JS; converting is possible later
file by file). UI only: no business rules and no direct `fetch`/`axios` calls in components.

```
frontend/src/
├── App.jsx            routes + route guards; mounts the chatbot once
├── main.jsx           entry
├── config/env.js      every build-time setting in one place (API base URL, demo mode, status page)
├── api/               the HTTP layer: client.js (axios: base URL, JWT, refresh on 401, error normalising,
│                      envelope unwrapping), baseUrl.js (API URL rules, /api/v1)
├── services/          one module per API area (rationService, qrService, chatbotService, …) — plain data in/out
├── state/             Zustand stores: auth (tokens, user), preferences, QR scanner, chatbot open state;
│                      toast.js (useToast) + ToastProvider.jsx
├── features/          logic of one feature, no UI: qr/ (payload contract, input validation),
│                      auth/ (ProtectedRoute, role → home page), chatbot/ (reply text → paragraphs and lists)
├── pages/             one folder per area: landing/, public-help/, rural/ (citizen), shop/,
│                      government/ (officials + admin), shared/, status/ (dev only), Login, Register, NotFound
├── layouts/           DashboardLayout (sidebar, header, language, QR scanner host), PublicLayout (header/footer)
├── components/        reusable UI: chatbot/, qr/, verification/, ai/, LanguageSwitcher, common widgets
├── hooks/             useChatbot, useQrScanner, useOnlineStatus
├── i18n/              translations.js (+ publicStrings.js): en / hi / mr, useTranslation()
├── utils/format.js    dates and times in the user's language (UTC-safe), ration item labels and units
├── types/api.js       JSDoc types of the API contract (envelope, errors, user, auth response)
├── styles/global.css  design tokens and global styles
└── assets/            logos
tests/unit/            Vitest + Testing Library
```

The layout follows the project's target architecture (2026-09-28): UI (`pages`, `layouts`, `components`),
state (`state`), HTTP (`api`) and domain calls (`services`), feature logic (`features`), configuration
(`config`) are separate, so a page never builds a URL, reads `import.meta.env` or formats a date itself.
Area names inside `pages/` follow the existing app (`rural` = citizen, `shop` = ration shop).

## Data flow

Component → `services/<area>Service.js` → `api/client.js` (adds `Authorization`, retries once after refreshing
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
