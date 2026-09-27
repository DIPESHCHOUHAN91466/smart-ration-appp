# Architecture diagrams

Ten diagrams of the system as it is built (checked against the code on 2026-09-26). They are
[Mermaid](https://mermaid.js.org/) text, so GitHub and VS Code (with a Mermaid preview extension)
render them, and a change to the system is a reviewable change to this file.

1. [System architecture](#1-system-architecture)
2. [Frontend architecture](#2-frontend-architecture)
3. [Backend architecture](#3-backend-architecture)
4. [API flow](#4-api-flow)
5. [Database relationships](#5-database-relationships)
6. [AI flow](#6-ai-flow)
7. [Authentication flow](#7-authentication-flow)
8. [QR verification flow](#8-qr-verification-flow)
9. [Deployment architecture](#9-deployment-architecture)
10. [CI/CD pipeline](#10-cicd-pipeline)

## 1. System architecture

The browser only ever talks to the Python gateway. The gateway answers sign-in, public help and the
chatbot itself and forwards every other `/api/*` call to the C# business API. Both backends use the same
MySQL database and the same JWT signing key.

```mermaid
flowchart LR
    B["Browser<br/>React SPA (Vite)"]
    subgraph PY["Python gateway :8000 (FastAPI)"]
        V["/api/v1 alias"]
        A["Auth: register, login,<br/>refresh, logout"]
        H["Public help + chatbot<br/>(no login, no private data)"]
        W["Website files<br/>(production build)"]
        P["Proxy: every other /api/*"]
    end
    CS["C# business API :5188<br/>(ASP.NET Core 8)"]
    AI["AI service :8001<br/>(FastAPI, optional)"]
    DB[("MySQL 8<br/>smartration")]
    KB["Knowledge base<br/>ai/chatbot/knowledge/*.json"]

    B -- "HTTPS, JWT" --> V
    V --> A & H & P
    B -. "GET /" .-> W
    A -- "users, refresh tokens" --> DB
    H --> KB
    P -- "same path, same JWT" --> CS
    CS -- "EF Core" --> DB
    CS -- "X-Api-Key" --> AI
    AI -- "read-only account" --> DB
```

## 2. Frontend architecture

```mermaid
flowchart TB
    M["main.jsx"] --> APP["App.jsx: routes"]
    APP --> PUB["Public pages<br/>landing, help, login, register,<br/>public profile badge"]
    APP --> PR["ProtectedRoute(roles)"]
    PR --> DL["DashboardLayout<br/>sidebar, search, notifications"]
    DL --> RU["Rural pages<br/>book, token, history, verification"]
    DL --> SH["Shop pages<br/>queue, scanner, inventory"]
    DL --> GV["Government pages<br/>dashboard, map, audit, AI centre"]
    DL --> SS["Shared pages<br/>settings + my profile, beneficiary 360"]
    APP --> CB["ChatbotWidget"]

    RU & SH & GV & SS & PUB & CB --> SV["services/*.js<br/>one module per API area"]
    SV --> AX["api.js (axios)<br/>adds JWT, refreshes on 401,<br/>unwraps the envelope"]
    AX --> BASE["apiBase.js<br/>VITE_API_BASE_URL → /api/v1"]

    subgraph ST["State"]
        AS["authStore (zustand, persisted)"]
        PS["preferencesStore"]
        CS["chatbotStore"]
        I18["i18n: en / hi / mr"]
    end
    AX <--> AS
    DL --> PS
    CB --> CS
    PUB & DL --> I18
```

## 3. Backend architecture

Controllers only translate HTTP; rules live in services; only services touch the database.

```mermaid
flowchart TB
    subgraph CSH["C# API (backend/SmartRation.Api)"]
        MW["Middleware: exception → envelope,<br/>JWT bearer, role policies, rate limiter"]
        CT["Controllers (25)<br/>thin: parse, call, wrap"]
        SVC["Services<br/>booking, entitlement, QR, OTP, verification,<br/>collection, inventory ledger, search, catalog, AI"]
        ACC["BeneficiaryAccess<br/>one access rule"]
        MAP["Mapping extensions<br/>entity → DTO"]
        EF["SmartRationDbContext<br/>(EF Core, Pomelo MySQL)"]
        MW --> CT --> SVC
        SVC --> ACC
        SVC --> MAP
        SVC --> EF
    end
    subgraph PYG["Python gateway (backend/SmartRation/app)"]
        PMW["Middleware: /api/v1 alias, request id,<br/>size limit, security headers, CORS"]
        API["api/: auth, health, public_help,<br/>legacy_proxy (last)"]
        PSV["services/: auth_service"]
        CHAT["chatbot/: intents, retrieval, responses"]
        SA["db/: SQLAlchemy models,<br/>Alembic migrations (schema owner)"]
        PMW --> API --> PSV --> SA
        API --> CHAT
    end
    EF --> DB[("MySQL")]
    SA --> DB
    API -- "8 small httpx pools" --> MW
```

## 4. API flow

One authenticated call from the browser, for example `GET /api/v1/ration/items?shopId=3`.

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (api.js)
    participant G as Python gateway
    participant C as C# API
    participant D as MySQL
    B->>G: GET /api/v1/ration/items?shopId=3<br/>Authorization: Bearer JWT
    G->>G: rewrite /api/v1 → /api, add X-Request-ID,<br/>check body size
    alt route is Python's own (auth, public help, chatbot)
        G->>D: query
        G-->>B: {success, message, data, errors}
    else any other /api/* route
        G->>C: same method, path, query, body, JWT<br/>+ X-Forwarded-For, X-Request-ID
        C->>C: validate JWT (key, issuer, audience, expiry),<br/>check role, rate limit
        C->>D: EF Core queries (service layer)
        D-->>C: rows
        C-->>G: envelope + status
        G-->>B: same body and status, X-Served-By: legacy-dotnet
    end
    Note over G,C: C# down → 502 LEGACY_API_UNAVAILABLE, slow → 504 LEGACY_API_TIMEOUT
```

## 5. Database relationships

The core tables (25 in total; Alembic revision `0001_initial` owns the schema). `Users` holds every role;
a citizen's `Beneficiaries` row links them to a `Families` row, which belongs to one shop and one scheme.

```mermaid
erDiagram
    Users ||--o| Beneficiaries : "is (citizen)"
    Users }o--o| RationShops : "works at (shop owner)"
    Users ||--o{ RefreshTokens : has
    Users ||--o{ Notifications : receives
    Users ||--o{ Tokens : books
    RationShops ||--o{ Families : serves
    RationSchemes ||--o{ Families : "entitles"
    RationSchemes ||--o{ SchemeEntitlementItems : "quota per member"
    Families ||--o{ FamilyMembers : has
    Families ||--o{ Beneficiaries : has
    Beneficiaries ||--o| AadhaarVerifications : "masked reference only"
    Beneficiaries ||--o| PassbookVerifications : has
    Beneficiaries ||--o| MobileVerifications : has
    Beneficiaries ||--o{ OtpVerifications : "hashed codes"
    RationShops ||--o{ TimeSlots : "5-minute slots"
    TimeSlots ||--o{ Tokens : "booked in"
    RationShops ||--o{ Tokens : at
    Tokens ||--o{ TokenItems : requests
    Tokens ||--o| RationCollections : "completed by"
    Beneficiaries ||--o{ RationCollections : receives
    RationCollections ||--o{ RationCollectionItems : issues
    RationShops ||--o{ Inventory : stocks
    RationShops ||--o{ InventoryMovements : "ledger"
    RationShops ||--o{ VerificationAuditLogs : "scans at"
    RationShops ||--o{ AIAlerts : about
```

## 6. AI flow

Two separate AI parts. The public chatbot answers from a reviewed knowledge base and never sees private data.
The analytics come from the optional AI service; when it is down the C# API answers with its own simpler
calculations, so the dashboards keep working.

```mermaid
flowchart LR
    subgraph PUBLIC["Public help (no login)"]
        U1["Visitor"] --> CW["ChatbotWidget"]
        CW -- "/api/v1/chatbot/message" --> ENG["chatbot engine:<br/>intents → retrieval → response"]
        ENG --> KB["knowledge base (en/hi/mr)"]
        ENG -. "Aadhaar-like number,<br/>private question" .-> REF["refuses + points to login"]
    end
    subgraph ANALYTICS["Distribution analytics (signed-in staff)"]
        U2["Shop owner / official"] -- "/api/v1/ai/analytics/*" --> C["C# AIController<br/>(shop owner scoped to own shop)"]
        C -- "X-Api-Key" --> AIS["AI service /v1/forecast, inventory,<br/>queue, risk, shops, alerts"]
        AIS -- "read-only" --> DB[("MySQL")]
        C -. "AI service unavailable" .-> FB["built-in C# forecast,<br/>inventory risk, queue prediction"]
        C --> AL["AiAlertService → AIAlerts table"]
    end
```

## 7. Authentication flow

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant G as Python gateway (/api/v1/auth)
    participant D as MySQL
    participant C as C# API
    B->>G: POST /auth/login {email, password}
    Note over G: rate limit 10/min per address
    G->>D: find user by email
    G->>G: verify argon2id hash<br/>(older bcrypt hashes still accepted and upgraded)
    G->>D: store SHA-256 hash of a new refresh token
    G-->>B: accessToken (JWT HS256, 15 min) + refreshToken + user
    B->>C: any business call via the gateway, Bearer accessToken
    C->>C: same key, issuer, audience → role from the token
    B->>G: POST /auth/refresh {refreshToken} (on 401)
    G->>D: token hash valid and not revoked? revoke it, store a new one
    G-->>B: new pair (rotation: a reused refresh token is refused)
    B->>G: POST /auth/logout {refreshToken}
    G->>D: mark revoked
```

## 8. QR verification flow

```mermaid
sequenceDiagram
    autonumber
    actor R as Citizen
    actor S as Shop owner
    participant C as C# API
    participant D as MySQL
    R->>C: book a 5-minute slot (POST /ration/bookings)
    C->>D: token + items, slot capacity checked (concurrency-safe)
    R->>C: open My token (GET /qr/payload/{id})
    C-->>R: payload signed with HMAC-SHA256 (Qr secret), shown as QR
    S->>C: scan (POST /qr/scan or GET /verification/qr/{ref})
    C->>C: signature valid? token for this shop, today, not used?
    C->>D: Aadhaar / passbook / mobile status, family entitlement left
    C->>D: VerificationAuditLog (reference only, never the raw payload)
    C-->>S: summary: ALLOWED or COLLECTION_BLOCKED + reason
    opt QR not available
        S->>C: OTP to the registered mobile (6/min limit), then verify
    end
    S->>C: POST /ration/collection/confirm + Idempotency-Key
    C->>D: one transaction: stock out (inventory ledger),<br/>collection + items, token → Completed
    C-->>S: receipt (a retried request returns the same receipt)
```

## 9. Deployment architecture

Render Blueprint (`render.yaml`, guide: [RENDER.md](../deployment/RENDER.md)). Synthetic-data demo; the AI
service is not deployed there (the dashboards use the C# fallback).

```mermaid
flowchart LR
    U["Users (HTTPS)"] --> W
    subgraph RENDER["Render (free plan, Docker)"]
        W["smart-ration-hsd2c<br/>Python gateway + built website<br/>health: /health/live"]
        CORE["smart-ration-hsd2c-core<br/>C# API, non-root image<br/>health: /api/health"]
        W -- "HTTPS (public host name;<br/>free plan has no private network)" --> CORE
    end
    subgraph AIVEN["Aiven (free MySQL 8)"]
        M[("smartration<br/>TLS, CA certificate")]
    end
    W -- "DATABASE_URL + MYSQL_SSL_CA" --> M
    CORE -- "DATABASE_URL + MYSQL_SSL_CA" --> M
    GH["GitHub main"] -- "push → build + deploy" --> RENDER
    SEC["Render-generated secrets:<br/>JWT_SECRET_KEY, Qr__Secret"] -.-> W & CORE
```

First start on an empty database: the C# API creates the schema and seeds synthetic data; the Python
service waits for it (`WAIT_FOR_LEGACY_API`), then verifies and adopts the schema (`RUN_DB_SETUP`).
Local alternative: `docker compose` / the four processes started by `sr.ps1 run`.

## 10. CI/CD pipeline

`.github/workflows/ci.yml`, on every push to `main` or `feature/**` and every pull request. Jobs run in
parallel; `docker` waits for `python`.

```mermaid
flowchart LR
    T["push / pull request"] --> PYJ & AIJ & CSJ & FEJ & SECJ
    PYJ["python<br/>ruff, mypy, schema on MySQL 8,<br/>setup idempotent, tests, MySQL suite,<br/>chatbot evaluation"]
    AIJ["ai<br/>AI service tests"]
    CSJ["csharp<br/>dotnet build + test (Release)"]
    FEJ["frontend<br/>ESLint, Vitest, build"]
    SECJ["security<br/>pip-audit ×2, npm audit (prod),<br/>dotnet vulnerable packages"]
    PYJ --> DK["docker<br/>build both images; no secrets/env files;<br/>container serves the website;<br/>C# image runs as non-root"]
    T -. "push to main (independently of CI)" .-> RD["Render builds and deploys"]
```

**Gap:** Render deploys every push to `main` whether or not CI passed (`render.yaml` sets no deploy
trigger). Setting the services to deploy only after checks pass (Render's "after CI checks pass" auto-deploy
option) closes it. NOT DONE: it can only be verified on a connected Render account.

Not in CI: the Playwright end-to-end tests and the HTTP load test, because they need the whole stack
running (`sr.ps1 e2e`, `sr.ps1 load`).
