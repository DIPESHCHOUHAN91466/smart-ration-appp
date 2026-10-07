# Baseline test report

Date: 2026-10-07 · Windows 11, 7.4 GB RAM · branch `audit-and-deploy`.
Baseline taken at `da87cc9`; two defects found by it were fixed in `92d6d1f` and everything was re-run.
Nothing is skipped silently: every skip is listed with its reason.

## Results

| Suite | Command (from) | Result | Notes |
|---|---|---|---|
| Backend unit + API + **MySQL integration** | `pytest` (backend/SmartRation) with `TEST_DATABASE_URL` → `smartration_test` | **687 passed, 5 skipped** | Skipped: the database-permission tests, which need MySQL root and run only in CI (`TEST_MYSQL_ROOT_URL`) |
| Backend lint / types | `ruff check app tests` · `mypy app` | clean · clean (108 files) | |
| Regression (cross-component contracts, deploy config) | `pytest tests/regression` (repo root) | **34 passed** | |
| Website unit | `npx vitest run` (frontend) | **117 passed** (18 files) | 112 at baseline + 5 new for the session fix |
| Website lint | `npx eslint src tests` | clean | |
| Website build | `npx vite build` | OK in ~10 s; main bundle 453 kB (136 kB gzip) | |
| Android | `flutter analyze` · `flutter test` (smart_ration_mobile) | clean · **361 passed** | Run at `da87cc9`; app code unchanged since |
| Android build | `flutter build apk --debug` (JDK 21) | OK | Release `.aab` not built: needs the owner's upload key |
| Browser e2e (Playwright, Edge) | `npx playwright test` (tests/e2e) against the running stack | **27 passed, 1 skipped** | Skipped: staff two-factor test needs a dedicated staff account (`E2E_STAFF_EMAIL/PASSWORD`) |
| Dependency audit | `npm audit` (frontend) · `pip-audit -r requirements.txt` | 0 · 0 known vulnerabilities | |
| Docker image | `docker build` | **not run** | Docker Desktop engine not running on this PC; CI job `docker` builds it and runs a first-boot smoke test |
| Live smoke (deployed site) | `pytest tests/smoke` | **not run** | Nothing is deployed (see DEPLOYMENT_AUDIT.md) |

## Defects found by the baseline and fixed (`92d6d1f`)

1. **Website: every page load failed its API calls once (401) and repeated them.** Since the session moved to an
   HttpOnly cookie, the access token lives in memory only; after a reload each call went out without a token, got
   401, refreshed and was sent again (parallel calls often refreshed twice). The e2e citizen journey recorded 28
   failed calls. Fix: the API client gets one token from the cookie *before* the first call; calls made meanwhile
   wait for that refresh. Verified: 5 new unit tests, and the three e2e role journeys pass (they fail on any 4xx API answer).
2. **e2e suite could not pass as configured.** Spec files ran in parallel while sharing the demo accounts (a
   password-change test signs the account out everywhere) and the API's sign-in limit (10 a minute per address).
   Fix: `workers: 1`; the README now says the API for an e2e run is started with `AUTH_RATE_LIMIT_PER_MINUTE=60`
   and the AI service. Production keeps the limit of 10.

## Environment notes

- The status-page e2e test expects every *configured* service to be healthy; locally `AI_SERVICE_URL` is set, so the
  AI service (:8001) must run. In production it is not configured and reported as disabled, not unhealthy.
- An Android emulator and a person using it at the same time made a live device check unreliable (2026-10-07);
  it was stopped. Phone testing is still open.
