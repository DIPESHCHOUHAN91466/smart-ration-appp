# Proposed architecture — audit 2026-10-17

**Recommendation: keep the current architecture.** The audit found no structural reason to change the stack
(FastAPI + MySQL + React/Vite + Flutter on Azure App Service). Business rules already live once, on the backend,
and both clients call the same versioned `/api/v1`. The data invariants (capacity, no negative stock, single
collection, idempotent retries) are enforced with row locks and unique keys, and MySQL concurrency tests cover them.
A rewrite, microservices, a message broker, a cache or Kubernetes would add cost and risk without fixing anything
the audit found.

The proposal is therefore a set of targeted corrections to the current design.

```mermaid
flowchart LR
  W[Web app] --> API
  A[Android app] --> API
  subgraph Azure India South Central — pay-as-you-go
    API["App Service (prod)<br/>one start path: scripts/azure/startup.sh"]
    STG["App Service (staging)<br/>+ staging DB — optional, priced first"]
    DB[(MySQL Flexible prod<br/>rows-only runtime account<br/>migration account separate)]
    MON["Application Insights / availability test<br/>+ 5xx / restart alerts"]
  end
  API --> DB
  API -. telemetry .-> MON
  API -- "SMTP now · DLT SMS gateway before real users" --> MSG[Code delivery]
  API -. "optional: deploy ai/ or drop the DEGRADED signal" .-> AI[AI service]
```

| # | Change | Why (finding) | Kind |
|---|---|---|---|
| P1 | One deployment entry point: keep `scripts/azure/startup.sh` + `app.main:create_app --factory`; remove the untracked `main.py`/`startup.sh`/copies, unused `gunicorn` pin, and the inert `azure-deploy.yml` (or replace it with an OIDC zip-deploy workflow) | SEC-07, SEC-08 | cleanup, approval |
| P2 | Business timezone setting (`Asia/Kolkata`) used for "today", past-slot checks (date **and** start time) and the monthly entitlement window; storage stays UTC | DEF-03 | code + tests |
| P3 | Honest code delivery: SMTP on live; the mock provider outside development returns an explicit "not available" error instead of success | SEC-06 | code + config |
| P4 | Observability: register `Microsoft.Insights`, availability test on `/health`, alerts on 5xx and restarts. Let `/api/health` stop reporting `DEGRADED` for an AI service that is intentionally not configured | SEC-03, DEF-06 | config + small code |
| P5 | Least privilege on live: runtime = rows-only account, `MIGRATION_DATABASE_URL` = admin (code already supports it) | SEC-04 | config |
| P6 | Staging: a second App Service app + small MySQL database, deployed from the same package. Optional on cost; required before real data | readiness | cloud, cost |
| P7 | Retire the C# API and the Expo template from the repository after an approved removal (git history keeps them) | inventory | approval |
| P8 | Single documentation entry point: fold the 18 root-level Markdown files into `docs/` with an index; mark superseded ones as archived | doc drift | docs |

Not proposed (considered and rejected for now): LLM-based assistant (rule-based assistant and knowledge-base
chatbot meet the current need; an LLM needs an approved provider, privacy-policy update and evaluation set first),
Redis for rate limiting (single instance; needed only when scaling out), a separate frontend host (the API serves the
built site from the same origin, which keeps the cookie/CSRF model simple).
