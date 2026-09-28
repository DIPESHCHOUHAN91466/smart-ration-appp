# src/pages — screens

**What:** one component per screen, grouped by who uses it. **Why:** a URL maps to one page, so you can
find the code for any screen quickly.
**Belongs here:** page layout, wiring components to services and stores. **Doesn't:** reusable widgets
(`src/components`), raw API calls (`src/services`), business rules (backend).
**Run/test:** routed in `src/App.jsx`. **Connects:** pages call `src/services/*` and read `src/state/*`.

| Folder | Who | Routes |
|---|---|---|
| `landing/` | public | `/` |
| `public-help/` | public | `/help` |
| `Login.jsx`, `Register.jsx`, `PublicProfile.jsx`, `NotFound.jsx` | public | `/login`, `/register`, `/profile/:ref`, unknown URLs |
| `rural/` | citizen (RuralUser) | `/rural/*` — dashboard, book ration, my token, history, verification |
| `shop/` | ration-shop owner | `/shop/*` — dashboard, queue, QR scanner, inventory |
| `government/` | official + admin | `/gov/*` — dashboard, users, shops, bookings, inventory, statistics, reports, audit, map, AI centre, synthetic data, database viewer |
| `shared/` | signed-in users | notifications, beneficiary profile, settings |
| `status/` | developers | `/status` (development builds only) |

Folder names are the original ones (`rural` = citizen, `shop` = ration shop) and were kept on purpose.
