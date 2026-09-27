# MySQL testing with 100 people — step-by-step guide

This project doesn't use **MySQLi** (that's PHP's MySQL extension, and there is no PHP here).
It talks to MySQL through **PyMySQL + SQLAlchemy** (Python backend) and EF Core (the C# API
being retired). Everything a MySQLi test plan checks has a direct equivalent here:

| MySQLi idea | In this project |
|---|---|
| `mysqli_prepare` + `bind_param` (prepared statements) | SQLAlchemy/PyMySQL bound parameters: `select(User).where(User.Email == value)`, `text("... = :e")`, `cursor.execute("... = %s", (value,))` |
| `mysqli_report(MYSQLI_REPORT_ERROR \| MYSQLI_REPORT_STRICT)` | the driver always raises exceptions (`IntegrityError`, `OperationalError`, …) with MySQL's error number in `exc.orig.args[0]` |
| `mysqli_set_charset('utf8mb4')` | `?charset=utf8mb4` in `DATABASE_URL` |
| persistent connections (`p:host`) | SQLAlchemy connection pool (10 + 10 overflow, pre-ping, recycle 30 min) |
| `mysqli_begin_transaction` / `commit` / `rollback` | one `Session` transaction per request; rollback on any error |
| `mysqli_multi_query` | disabled: the driver refuses stacked statements |

The suite lives in `backend/SmartRation/tests/mysql_suite/` (123 tests).

---

## Step 1 — Create a separate test database (once)

The tests create, change and delete data and send SQL-injection strings on purpose, so they run
only against a database whose name ends in `_test`. They refuse to run against `smartration`.

Open **PowerShell** and log in to MySQL as root. MySQL asks for the root password; type it there:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

At the `mysql>` prompt, run these three lines:

```sql
CREATE DATABASE smartration_test CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
GRANT ALL PRIVILEGES ON smartration_test.* TO 'smartration_app'@'localhost';
EXIT;
```

This gives the app's existing account access to the new, empty database only. It changes nothing in `smartration`.

## Step 2 — Tell the tests where the test database is

In PowerShell, from the Python backend folder, use the **same password as in your `.env`** but the
database name `smartration_test`:

```powershell
cd backend\SmartRation        # from the repository root, wherever it is on your machine
$env:TEST_DATABASE_URL = "mysql+pymysql://smartration_app:<password>@localhost:3306/smartration_test?charset=utf8mb4"
```

This lasts only while that PowerShell window is open. Don't put it in a committed file.

## Step 3 — Run the tests

```powershell
.venv\Scripts\python -m pytest tests\mysql_suite -v
```

The first run builds all 25 tables in `smartration_test` with the real Alembic migration and seeds
synthetic reference data (shops, items, schemes, slots). The full run takes about 1–3 minutes.

Run a single area:

```powershell
.venv\Scripts\python -m pytest tests\mysql_suite\test_03_security.py -v
```

## Step 4 — Read the results

- Every line should end in `PASSED`. A `FAILED` line prints the expected value, what actually
  came back, and the MySQL error number.
- At the end, a **"MySQL performance"** section lists the timings measured on your machine: single
  vs. batch inserts, reads, pooled vs. new connections, and memory.
- `SKIPPED ... TEST_DATABASE_URL not set` means Step 2 didn't take effect in this window.

---

## Sample data (`sample_data.py`)

100 people, each `{full_name, email, mobile, password}`:

- email `prefix.NNN@example.test` (reserved test domain), unique mobile `7XXXXXXXXX`, password `Synthetic-Pass-NNN!`;
- names that stress encoding and escaping:
  - `राहुल पाटील` (Devanagari)
  - `Zoë Ångström-Müller`
  - `Sunita 🌾 Shinde` (4-byte emoji)
  - `Priya D'Souza`
  - `Anil "Bapu" Jadhav`
  - a name with a backslash
  - a name with `;` and `--`
  - a name with `%` and `_`
  - tab and newline characters
  - `O'Brien; DROP TABLE Users; --`
  - the length limits: 2 characters, 150 ASCII characters, and 150 Devanagari characters (450 bytes)
- 16 SQL-injection payloads:
  - `' OR '1'='1`
  - `'; DROP TABLE Users; --`
  - `UNION SELECT`
  - `SLEEP(5)` and `BENCHMARK()`
  - hex-encoded and look-alike-apostrophe variants

All data is fabricated. There are no real people and no Aadhaar numbers.

## Test cases and expected outcomes

### 1. Configuration checklist — `test_01_configuration.py`
| Check | Expected |
|---|---|
| Server version | MySQL 8.x |
| Connection charset (client/connection/results) | `utf8mb4`, collation `utf8mb4_*` |
| Every table | InnoDB, utf8mb4 |
| `sql_mode` | contains `STRICT_TRANS_TABLES` (too-long values raise an error instead of being truncated) |
| Isolation / autocommit | `REPEATABLE-READ` / 0 (explicit transactions) |
| Deadlock detection / lock wait timeout | on / 1–120 s |
| Pool | QueuePool, pre-ping on, recycle 1800 s < `wait_timeout`, size + overflow ≤ half of `max_connections` |
| Connection reuse | two sequential queries use the same `CONNECTION_ID()` |
| Account | not root; no global privileges beyond `USAGE` |
| Multi-statements | `SELECT 1; SELECT 2` is rejected |

### 2. Functional CRUD — `test_02_functional_crud.py`
| Test | Expected |
|---|---|
| Create 100 → read each → update all → delete 50 | 100 rows; every field identical; 100 renamed, 50 inactive; 50 left, deleted ones gone |
| Register 100 via `POST /api/auth/register`, log in 10 | 100 × 200, 100 users + 100 beneficiaries; right password 200, wrong password 401 |
| Empty / blank name, 1-char name, 151-char name, bad email, 201-char email, bad phone, short password | 400 with the exact validation message; **0 rows written** |
| Exact maxima (150-char Devanagari name, 200-char email, 20-digit mobile, 100-char password) | 200; stored lengths 150/200/20 |
| Duplicate email (also different case) / duplicate mobile | 409; still 1 user |
| DB-level: duplicate email, 256-char email, NULL name | MySQL errors 1062, 1406 (no truncation), 1048 |
| Empty string name | stored as `''`, not NULL |

### 3. Security — `test_03_security.py`
| Test | Expected |
|---|---|
| Login with each payload as email/password (48 attempts) | 400/401, no token, < 3 s each (SLEEP never runs); 2 users, no Admin, table intact |
| Register with a payload as the name | stored **literally**, character for character |
| ORM lookup / `LIKE` with each payload | 0 rows |
| Raw PyMySQL cursor with `%s` placeholder | 0 rows |
| Compiled SQL | contains the `%s` placeholder, never the value |
| Demo: the same payload pasted into SQL text | returns **all** users (why placeholders matter); with a placeholder: 0 |
| Password storage | `$argon2id$…`, never the plain password |
| Wrong password vs. unknown email | same status and message (no account discovery) |

### 4. Performance — `test_04_performance.py` (numbers printed at the end)
| Test | Expected |
|---|---|
| 100 inserts one-by-one vs. one batch | batch faster; ≥ 200 round trips vs. ≤ 10 |
| 100 reads one-by-one vs. one `IN (...)` | single query faster; `EXPLAIN` uses `IX_Users_Email` |
| Update / delete 100 in one statement | 100 rows affected each |
| 100 queries: new connection each vs. pool | pool faster (typically 5–50×) |
| Load 100 users as objects | peak Python memory < 10 MB |

### 5. Concurrency — `test_05_concurrency.py`
| Test | Expected |
|---|---|
| 100 increments from 20 threads with `FOR UPDATE` | final value exactly 100 (no lost updates) |
| 30 threads booking a slot with capacity 2 | exactly 2 succeed, 28 refused, count 2 |
| 20 threads inserting the same email | 1 row; 19 × error 1062 |
| 100 different people registering at once (10 threads) | 100 users, 100 unique beneficiary and family codes, no errors |
| Same person registering 10 times at once | 1 success, 9 × 409, no half-created records |
| Two transactions locking rows in opposite order | MySQL detects the deadlock (1213) immediately and rolls one back; with retry, both commit exactly once |
| 40 threads on a 20-connection pool | all succeed (extras wait); all connections returned |

### 6. Error handling — `test_06_error_handling.py`
| Test | Expected |
|---|---|
| Wrong DB password | error 1045 in < 6 s; the password isn't in the message |
| Unreachable server | fails in < 6 s (no hanging) |
| API with the database down | `/health` and `/ready` 503; login 500 `INTERNAL_ERROR`; no password, "mysql" or error numbers in responses |
| Table missing mid-request | clean 500 envelope, no SQL or table name, `X-Request-ID` present, user insert rolled back; works again once fixed |
| Registration with no active shop | 400 with a clear message; the user row doesn't survive |
| Duplicate inside one transaction | whole transaction rolled back (0 rows) |
| Connection killed (`KILL`) | error 2013/2006; next request gets a fresh working connection |
| Row locked by someone else | error 1205 after the 1 s timeout, not a hang |
| Logs during register/login | contain events, never passwords, tokens, query-string secrets or the JWT key |

### 7. Data integrity — `test_07_data_integrity.py`
| Test | Expected |
|---|---|
| 100 records round trip | every name identical and same length; emoji stored as `F09F8CBE`; 150 Devanagari chars = 450 bytes |
| Fingerprint (SHA-256 of all rows) | unchanged after reads; restored exactly after update + revert |
| Decimals | `0.1 + 0.2` stored as exactly `0.3`; 30 decimal places kept |
| Datetimes | microseconds kept |
| Foreign keys | missing parent → 1452; deleting a shop that still has families → 1451 and the shop survives |
| CASCADE / SET NULL | deleting a user removes their beneficiary and tokens; deleting a shop sets `Users.RationShopId` to NULL |
| After 100 registrations | 0 orphans in 4 relationship checks; Aadhaar values all `XXXX-XXXX-####`, mobiles `******####`; 100 unique codes |

---

## Configuration checklist (tick after a green run)

- [ ] `DATABASE_URL` ends with `?charset=utf8mb4`
- [ ] Server `sql_mode` includes `STRICT_TRANS_TABLES`
- [ ] All tables InnoDB + utf8mb4
- [ ] App uses the `smartration_app` account, never root; no global privileges
- [ ] Every query uses placeholders; no SQL built with f-strings or `+` from user input
- [ ] Errors raise exceptions; API responses never contain SQL, table names or credentials
- [ ] Connection pool: pre-ping on, `pool_recycle` (1800) < `wait_timeout`, `connect_timeout` 5 s
- [ ] Transactions: one per request; rollback on error; `FOR UPDATE` where counters/stock change
- [ ] Deadlocks (1213) retried by code that locks several rows
- [ ] Logs are JSON with request ids and no secrets
- [ ] `tests/mysql_suite`: 123 passed

## Clean up (optional)

The suite empties its own tables at the start of each test and leaves `smartration_test` in place
for the next run. To remove it completely, as root:

```sql
DROP DATABASE smartration_test;
```
