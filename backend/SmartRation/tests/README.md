# SmartRation/tests — Python Test Suites

Comprehensive unit, contract, and scale test suites for the Python FastAPI Gateway, Chatbot Engine, Data Providers, and Database Migrations.

## Overview

| Test Module | Coverage Area |
|---|---|
| `test_auth.py` | Registration, login, token refresh, password hashing with Argon2id, automatic upgrade of legacy BCrypt hashes, JWT expiry, invalid credentials |
| `test_chatbot_engine.py` | Intent parsing, sensitive data redaction (Aadhaar, OTP, passwords), knowledge retrieval, language fallback (EN/HI/MR), health guidance rules |
| `test_public_help_api.py` | Knowledge base endpoints, article search, category browsing, topic resolution |
| `test_synthetic_data.py` | Deterministic generation of 1000+ realistic Indian citizen profiles, household structures, ration card schemes, and token bookings |
| `test_proxy.py` | Reverse proxy forwarding to C# API (:5188), header propagation (client IP, correlation ID, JWT), error handling |
| `test_health_and_errors.py` | Liveness (`/health/live`), readiness (`/ready`), database connectivity probes, standard error envelope (`{success, message, errors}`) |
| `test_data_mode.py` | Rejection of `DATA_MODE=real` without verified government gateway integrations |
| `test_schema_compat.py` & `test_schema_snapshot.py` | Verification that SQLAlchemy models remain 100% aligned with Alembic migrations and MySQL schema |
| `test_api_contract.py` | Verification that exported OpenAPI definitions in `api/openapi/` do not drift from the live Python endpoints |
| `contract/` | Parity checks comparing Python gateway responses against direct C# API responses |
| `mysql_suite/` | End-to-end database integration suite (1000 records, optimistic concurrency, transactions, CRUD) |

## Running Python Tests

From `backend/SmartRation`:
```powershell
.venv\Scripts\pytest
```

To run only unit tests (excluding live database requirements):
```powershell
.venv\Scripts\pytest -m "not mysql"
```

To run the contract comparison tests (requires both servers running):
```powershell
.venv\Scripts\python tests\contract\compare_proxy.py
```
