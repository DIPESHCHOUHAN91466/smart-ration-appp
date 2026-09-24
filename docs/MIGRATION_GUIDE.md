# C# → Python migration guide

Status per area: [backend/SmartRation.Python/MIGRATION.md](../backend/SmartRation.Python/MIGRATION.md).
Initial audit: [MIGRATION_AUDIT.md](../MIGRATION_AUDIT.md).

## How an area is migrated

Each step moves one area (e.g. "bookings + tokens") and must leave the system fully working:

1. **Read the C# controller, service and DTOs** for the area, including validation messages,
   status codes, error codes and the exact JSON shape.
2. **Port** into `app/api/<area>.py` (router), `app/services/<area>_service.py` (logic, one transaction),
   `app/schemas/<area>.py`. Use `get_current_user` / `require_roles` for the same roles as `[Authorize]`.
3. **Register the router** in `app/main.py` *before* the fallback proxy. From then on Python serves it.
4. **Unit tests** (`tests/test_<area>.py`) on SQLite: success paths, validation, authorisation,
   conflicts, and transaction rollback for anything that writes.
5. **Contract check** against the live C# API: add the area's requests to `tests/contract/`; the same
   request must give the same status and JSON (ids/timestamps normalised).
6. **Run everything**: `pytest`, `ruff check .`, `mypy`, `scripts/verify_database.py`, both contract
   scripts, C# tests. Record results in MIGRATION.md; commit.
7. Only when the step is green, move to the next area.

Rules: never change the database schema inside a port step (schema changes are separate Alembic
revisions); keep route paths, bodies and messages identical; new routes from the brief are added as
**aliases** next to the existing ones, never replacing them; money-like quantities stay `Decimal`.

## Order

| Step | Area | Notes |
|---|---|---|
| 3 | users, ration items, slots | alias `/api/users/me` |
| 4 | bookings + tokens | slot capacity (2), booking limits |
| 5 | QR | same `Qr:Secret`, reference format `SRQR-{id}-{sig16}`; existing codes must keep verifying |
| 6 | verification + OTP + SMS | hashed OTPs, attempt limits |
| 7 | collection | one transaction, row locks, idempotency key, entitlement check |
| 8 | inventory + ledger | every change writes an `InventoryMovements` row |
| 9 | notifications | |
| 10 | beneficiaries, families, public, search, audit | masked identifiers only |
| 11 | government/admin, map, synthetic data, admin DB viewer | admin actions audited |
| 12 | AI + AI alerts + OCR | merge `SmartRation.AI`; no OpenCV/PyTorch/YOLO |
| 13 | `/api/health` | |
| 14 | frontend → :8000 | one env var (`VITE_API_BASE_URL`) |
| 15 | retire C# | move to `legacy_archive/`, remove proxy, remove EF history table |

## Rollback

- **Per route:** remove the router from `app/main.py`; the proxy sends the route back to C#.
- **Whole backend:** point the frontend back at `http://localhost:5188/api` (it still is today).
- **Passwords:** users who logged in through Python now have Argon2id hashes. The C# API on this
  branch verifies both BCrypt and Argon2id (`PasswordHashes.cs`), so rolling back to *this branch's*
  C# is safe. Rolling back to the pre-migration checkpoint `3148b9d` is not: that build can't read
  Argon2id hashes (those users would need a password reset).
- **Database:** revert the latest Alembic revision with `alembic downgrade -1` (after a backup), or
  restore a backup ([BACKUP_RESTORE.md](BACKUP_RESTORE.md)). Adoption of the existing database
  (`stamp 0001_initial`) is undone by dropping the `alembic_version` table; no other table changed.
