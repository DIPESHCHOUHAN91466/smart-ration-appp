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

Changing values: edit the JSON (keep the C# `DbInitializer` in sync — it seeds the same values), then
run the seed on an empty database or a fresh `smartration_test`.
