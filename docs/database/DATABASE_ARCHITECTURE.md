# Database

MySQL 8, database `smartration`, charset utf8mb4, InnoDB. The application connects with a
least-privilege account (`smartration_app`: DML + DDL on `smartration` only; no global
privileges such as PROCESS or CREATE DATABASE). The Python models in
`backend/SmartRation/app/models/` match the tables column for column; any drift
fails `tests/test_schema_compat.py` and `scripts/verify_database.py`.

On Windows, MySQL runs with `lower_case_table_names=1`, so tables are stored lowercase
(`users`) even though they're declared PascalCase (`Users`); the tooling handles both.

## Ownership and migrations

**Alembic owns the schema.** Revision `0001_initial` creates the 25 tables exactly as EF Core did,
including EF's constraint names (`FK_<Table>_<Principal>_<Column>`, `IX_<Table>_<Columns>`).
The existing database was adopted with `alembic stamp 0001_initial` after verifying zero drift,
which only added the `alembic_version` table. EF's `__EFMigrationsHistory` table is left alone
(the C# API still reads it on startup and finds nothing to apply). **Do not add EF Core migrations.**

New schema changes:

```
cd backend\SmartRation
# 1. edit app/models/
.venv\Scripts\alembic revision --autogenerate -m "short description"
# 2. review the generated file: reversible downgrade, no data loss, batch-safe for big tables
# 3. back up (BACKUP_RESTORE.md), then:
.venv\Scripts\python scripts\setup_database.py        # applies pending revisions, then verifies
```

Rules for revisions: every `upgrade` has a working `downgrade`; destructive steps (dropping a
column/table with data) need a data-preserving plan and explicit approval; the initial revision's
downgrade is refused unless `RESET_DATABASE=true` and `CONFIRM_RESET=SMART_RATION_RESET`.

## Scripts (`backend/SmartRation/scripts`)

| Script | What it does | Destructive? |
|---|---|---|
| `setup_database.py [--seed]` | empty DB → create; EF-created DB with zero drift → stamp; Alembic DB → upgrade; partial/unknown schema → refuse. Then verifies. | no |
| `verify_database.py` | read-only: connectivity, DB name, MySQL 8, tables, columns, types, nullability, defaults, FKs, indexes, uniques, migration version, reference data. Prints `DATABASE VERIFICATION PASSED/FAILED`, exit 0/1 | no |
| `seed_database.py` | synthetic reference data (items, 10 shops, 2 schemes + entitlements, inventory, 3 days of slots) into **empty tables only**; users only if `SEED_DEMO_PASSWORD` / `SEED_ADMIN_EMAIL`+`SEED_ADMIN_PASSWORD` are set | no |
| `reset_database.py` | drop everything, recreate, seed, verify. Requires `RESET_DATABASE=true`, `CONFIRM_RESET=SMART_RATION_RESET`, a non-production environment, typing the DB name, and takes a backup first | **yes** (dev only) |

All seed data is fabricated. There is no real Aadhaar, passbook or personal data anywhere;
Aadhaar values are masked synthetic references (`XXXX-XXXX-####`).

## Tables (25)

| Table | Cols | Foreign keys (on delete) | Unique |
|---|---|---|---|
| AIAlerts | 20 | — | — |
| AIInsights | 9 | — | — |
| AadhaarVerifications | 8 | BeneficiaryId→Beneficiaries (CASCADE) | BeneficiaryId |
| AuditLogs | 10 | — | — |
| Beneficiaries | 16 | FamilyId→Families (RESTRICT), UserId→Users (CASCADE) | BeneficiaryCode, UserId |
| Families | 6 | RationShopId→RationShops (RESTRICT), RationSchemeId→RationSchemes (RESTRICT) | FamilyCode |
| FamilyMembers | 7 | FamilyId→Families (CASCADE) | — |
| Inventory | 7 | RationShopId→RationShops (CASCADE) | RationShopId+RationType |
| InventoryMovements | 10 | RationShopId→RationShops (RESTRICT) | — |
| MobileVerifications | 6 | BeneficiaryId→Beneficiaries (CASCADE) | BeneficiaryId |
| Notifications | 7 | UserId→Users (CASCADE) | — |
| OtpVerifications | 10 | BeneficiaryId→Beneficiaries (CASCADE) | — |
| PassbookVerifications | 7 | BeneficiaryId→Beneficiaries (CASCADE) | BeneficiaryId |
| RationCollectionItems | 4 | RationCollectionId→RationCollections (CASCADE) | — |
| RationCollections | 9 | BeneficiaryId→Beneficiaries, TokenId→Tokens, RationShopId→RationShops (all RESTRICT) | IdempotencyKey, CollectionCode, TokenId |
| RationItems | 7 | — | RationType |
| RationSchemes | 5 | — | SchemeCode |
| RationShops | 12 | — | ShopCode |
| RefreshTokens | 7 | UserId→Users (CASCADE) | TokenHash |
| SchemeEntitlementItems | 4 | RationSchemeId→RationSchemes (CASCADE) | RationSchemeId+RationType |
| TimeSlots | 7 | RationShopId→RationShops (CASCADE) | — |
| TokenItems | 4 | TokenId→Tokens (CASCADE) | — |
| Tokens | 9 | TimeSlotId→TimeSlots, RationShopId→RationShops, UserId→Users (all RESTRICT) | TokenNumber |
| Users | 9 | RationShopId→RationShops (SET NULL) | Email, MobileNumber |
| VerificationAuditLogs | 13 | — | — |

Totals: 24 foreign keys, 37 indexes (18 unique). Enums are stored as integers with the C# values
(`app/models/enums.py`); decimals are `decimal(65,30)`; datetimes are `datetime(6)` naive UTC.

### Mapping to the target entities in the migration brief

| Brief entity | Here |
|---|---|
| users / roles | `Users.Role` (1 RuralUser, 2 ShopOwner, 3 GovernmentOfficial, 4 Admin) |
| citizens / households | `Beneficiaries`, `Families`, `FamilyMembers` |
| ration cards | no table; the passbook (`PassbookVerifications`) plays this role |
| qr credentials | `Tokens.QRCodeValue` (HMAC-signed `SRQR-…` references) |
| ration transactions | `RationCollections` + `RationCollectionItems` (idempotency key, one per token) |
| stock | `Inventory` + ledger `InventoryMovements` |
| otp requests | `OtpVerifications` (hashed codes) |
| audit | `AuditLogs`, `VerificationAuditLogs` |
| payments, system settings | not present — future work |

### Known schema follow-ups (to do as reviewed Alembic revisions, not now)

- Some deletes CASCADE where RESTRICT would protect history (e.g. `Beneficiaries.UserId`,
  `Notifications`, `TimeSlots`). Tighten once the matching Python services own those deletes.
- `LONGTEXT` is used for short strings EF didn't bound (names, units); bounded `VARCHAR`s would
  allow indexing. Change only with a data-length check first.
