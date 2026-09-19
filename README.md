# Smart Ration HSD2C Blue Dashboard — Final Frontend

A production-style React/Vite frontend prototype for the Smart Ration HSD2C distribution workflow.

## Included

- Three role-based login experiences: Rural User, Ration Shop Owner, Government Official
- Blue modern responsive dashboard
- Clickable cards with hierarchical navigation and Back breadcrumbs
- Rural token generation
- 5-minute time slots
- Rice/Tandul, Wheat/Gahu, Sugar/Sakhar selection
- Token confirmation and QR generation
- QR display/print flow
- Shop queue and collection management
- QR verification UI with manual fallback
- Inventory dashboard
- Government analytics
- Shop management
- Beneficiary management
- Complaints/feedback
- Policy configuration
- Audit trail
- Reports UI
- Responsive mobile layout
- Mock data layer
- Loading/empty/error-style states
- Animated hover/click/QR scanning UI

## Demo accounts

- Rural: `rural@example.com` / `demo123`
- Shop: `shop@example.com` / `demo123`
- Government: `officer@example.com` / `demo123`

## Run on Windows PowerShell

Open PowerShell in this folder:

```powershell
npm install
npm run dev
```

Then open:

```text
http://localhost:5173/
```

Keep the terminal running while using the website.

## Production build

```powershell
npm run build
npm run preview
```

## Important production note

This package is a complete frontend prototype with a mock data layer. For a real government deployment, connect the existing screens to a secured backend API and PostgreSQL database. Do not put Aadhaar, biometric templates, passwords, or other sensitive personal information inside QR payloads. Use HTTPS, secure authentication, RBAC, audit logging, rate limiting, server-side QR validation and approved identity-verification providers.

## Suggested backend API contract

```text
POST /api/auth/login
POST /api/tokens
GET  /api/tokens/:id
POST /api/qr/generate
POST /api/qr/verify
POST /api/collections/:id/complete
GET  /api/shop/queue
GET  /api/inventory
GET  /api/government/analytics
GET  /api/government/audit
GET  /api/reports
```
