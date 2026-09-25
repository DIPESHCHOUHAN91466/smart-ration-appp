# src/components — reusable UI

**What:** building blocks used by several pages. **Why:** one look and one behaviour everywhere.
**Belongs here:** presentational components and small UI logic (open/close, formatting).
**Doesn't:** API calls (use `src/services`), business rules (backend), page-specific layouts (`src/pages`).
**Run/test:** rendered by pages; tested in `frontend/tests/unit`.
**Connects:** pages import these; components get data through props, stores or hooks.

| Folder / file | Purpose |
|---|---|
| `chatbot/` | the floating Smart Ration AI Assistant ([chatbot/README.md](chatbot/README.md)) |
| `layout/` | public header/footer (`PublicLayout`), `LanguageSwitcher` |
| `qr/` | global QR scanner (camera, image, manual entry) |
| `verification/` | beneficiary verification panel, OTP modal, entitlement and family tables, receipt |
| `ai/` | analytics panel for the government AI centre |
| `BrandMark`, `EmptyState`, `PageHeader`, `StatusBadge`, `QRCodeCanvas`, `RationItemCard`, `ToggleSetting` | shared widgets |
