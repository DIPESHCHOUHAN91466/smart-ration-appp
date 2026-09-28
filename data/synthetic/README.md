# data/synthetic — fabricated demo data

**What:** reference data for a demonstration installation. **Every value is invented.** No real
person, household, Aadhaar number, ration card or shop is represented.

| File | Records | Used by |
|---|---|---|
| `reference/ration_items.json` | 6 items (rice, wheat, sugar, pulses, oil, salt) with local names and units | seed script |
| `reference/shops.json` | 10 demo ration shops around Nagpur (names, codes, coordinates) | seed script |
| `reference/schemes.json` | `DEMO-NFSA`, `DEMO-AAY` with per-member monthly quotas | seed script, chatbot (quotas answer) |
| `reference/inventory_rules.json` | minimum stock, stock tiers, slot capacity (2) and 5-minute slots | seed script |

Each file has `"_meta": {"isSynthetic": true, "dataSource": "SYNTHETIC_DEMO"}`; the seed script refuses
a file without it and refuses to run unless `DATA_MODE=synthetic`. It inserts only into **empty**
tables, so re-running never changes existing data.

Generated at runtime (not stored here): demo households and beneficiaries (C# `DbInitializer` and the
Python `SyntheticDataProvider` on registration: codes `FAM-DEMO-*`, `BEN-DEMO-*`, masked Aadhaar
references `XXXX-XXXX-####`), and optional distribution history (`backend/SmartRation.AI/scripts/generate_history.py`:
`BEN-HIST-*`, `@history.synthetic.invalid`). All rows carry `DataSource = "SYNTHETIC_DEMO"`.

## Bulk synthetic citizens: the central generator

`backend/SmartRation/app/synthetic` is the one place bulk citizen data comes from (tests and
the command below use it). Same `--seed` → identical records; everything is validated before insert.

```
cd backend\SmartRation
.venv\Scripts\python scripts\generate_test_data.py --users 1000 --seed 2026            # generate + validate only
.venv\Scripts\python scripts\generate_test_data.py --users 1000 --json people.json     # write JSON
.venv\Scripts\python scripts\generate_test_data.py --users 1000 --insert               # into smartration_test only
```

| Field | Format (seed 2026, person 1) |
|---|---|
| mobile | `9047000001` — block `90BB`, `BB = seed % 99 + 1`; block `00` is reserved for the demo accounts (`9000000001`, `…051`, `…052`) and the C# seeder's beneficiaries (`9000000002–050`) |
| email | `user0001.s2026@example.com` (RFC 2606 reserved domain) |
| ration card (`Families.FamilyCode`) | `SYN-RC-2026-000001` |
| beneficiary / Aadhaar reference / passbook | `SYN-BEN-…`, `SYN-AAD-…`, `SYN-PB-…` |
| Aadhaar | masked only, `XXXX-XXXX-1234` — no full number exists anywhere |
| names | English and Devanagari (Marathi/Hindi), families of 1–6 |

`--insert --bookings` also gives each citizen one Confirmed token in the earliest free upcoming time slot at
their shop (slot capacity respected, token number `SR-<year>-<id>`, items = the scheme's entitled ration
types; the QR value is signed by the C# API on first request). Citizens whose shop has no free slot are
reported as `Unbooked`.
`--collections SHARE` (e.g. `0.5`) adds past collections — the "transaction" history — for that share of the
citizens, following the C# collection rules: a Completed token in a **past** slot, a `RationCollection` with
its items, stock moved from available to allocated with a *Distributed* ledger entry per item, and never
below zero (citizens whose shop lacks stock are reported as `NotCollected`). Past slots exist in databases
seeded since 2026-09-25 (the seeder now creates −5…+2 days, like the C# seeder).
Verified at scale on MySQL: 100 000 citizens (343 085 family members) inserted in 83 s; 1 000 citizens'
collections with stock and ledger checked exactly (`tests/integration/mysql_suite/test_08_scale.py`).
`--insert` refuses any database whose name doesn't end in `_test`, refuses unless `DATA_MODE=synthetic`,
and runs in one transaction. Accounts can't log in unless `SYNTHETIC_USER_PASSWORD` is set.
The MySQL suite's `sample_data.py` is different on purpose: 100 *adversarial* records (emoji, 150-character
names, injection-looking text) for encoding and security tests.

Changing values: edit the JSON (keep the C# `DbInitializer` in sync — it seeds the same values), then
run the seed on an empty database or a fresh `smartration_test`.
