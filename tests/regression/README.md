# tests/regression — bugs that must never come back

**What:** (1) `test_cross_component_contracts.py` — the values C#, Python and JavaScript must agree on
(integer enums stored in shared columns, the QR envelope and scan statuses, roles, ration types, the
status numbers hard-coded in `database/queries`), read straight from each source file; (2) the register
below: every bug fixed in this project and the test that pins it, wherever that test lives.

**Why here:** each app's own tests can only see that app. A renumbered C# enum or a renamed QR status
passes every suite on its own and breaks production at the seam.

**Run** (repository root, Python backend's virtualenv; no database or running services needed):
```
backend\SmartRation\.venv\Scripts\python -m pytest tests/regression
```
It is also part of the root `pytest` run and of `scripts\testing\run-tests.ps1`.

## Register of fixed bugs

Add a row with every bug fix; the test must fail on the old code (checked for the rows marked ✓).

| Date | Bug | Test that pins it |
|---|---|---|
| 2026-09-28 | C# seeder counted cancelled demo tokens in `TimeSlots.BookedCount` (12 slots showed places taken by nobody; found by `database/queries/07_slot_count_drift.sql`) ✓ | `backend/SmartRation.Api.Tests/DbInitializerTests.cs` `Cancelled_seed_tokens_do_not_hold_a_slot_place` |
| 2026-09-28 | Timestamps from the C# API have no `Z`; My Token and Notifications showed them as local time (5 h 30 min early in India) | `frontend/tests/unit/format.test.js` "treats zone-less API timestamps as UTC" |
| 2026-09-28 | `reset_database.py` still pointed at the old backup script path after the folder restructure | `backend/SmartRation/tests/integration/test_db_scripts.py` `test_every_path_the_scripts_depend_on_exists` |
| 2026-09-28 | Backup-script test inherited `DB_NAME` from `tests/integration/mysql`'s `.env` (failed only in the full run) | `backend/SmartRation/tests/integration/test_backup_script.py` (isolated environment) |
| 2026-09-26 | Two gateway throughput bottlenecks under 100–1,000 users (commit 8f35e82) | `backend/SmartRation/tests/api/test_proxy.py` `test_requests_take_turns_across_the_connection_pools`, `test_pool_settings_create_that_many_clients` |
| 2026-09-25 | Concurrent registrations deadlocked on the empty-string unique codes (MySQL 1213) | `backend/SmartRation/tests/integration/mysql_suite/test_05_concurrency.py` `test_100_concurrent_registrations`, `test_same_person_registering_twice_at_once` |
| 2026-09-25 | Synthetic tests depended on `SEED_DEMO_PASSWORD` being unset (CI) | `backend/SmartRation/tests/integration/test_synthetic_data.py` (`sqlite_db` fixture clears it) |
| seam | C#, gateway and AI service disagree on an enum value, QR field, scan status, role or ration type ✓ | `tests/regression/test_cross_component_contracts.py` |
