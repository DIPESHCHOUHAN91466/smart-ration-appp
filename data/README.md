# data — synthetic data today, real data later

**What is this?** The data the system runs on that isn't user-generated: synthetic reference data now,
and the rules for ever using real data.

**Why does it exist?** To keep synthetic and real data strictly apart. The system is designed so
business logic never depends on synthetic data directly (it asks interfaces; `DATA_MODE` picks the
implementation), and so a real-data rollout is a deliberate, reviewed step — never an accident.

**What belongs here:**
- `synthetic/` — fabricated, clearly labelled demo data ([synthetic/README.md](synthetic/README.md)).
- `real/` — **documentation only**: what real data would require ([real/README.md](real/README.md)).

**What does NOT belong here:** real personal data (ever, in this repository), secrets, database dumps
(`database/mysql/backups`, git-ignored), generator code (`backend/*/scripts`).

**How do I run it?** `.\scripts\development\seed-demo-data.ps1` loads `synthetic/reference` into empty
tables (only when `DATA_MODE=synthetic`).

**How does it connect?** Python seed script → MySQL; the C# API seeds its own synthetic households on
first start; the AI service's history generator writes synthetic history. Everything generated is tagged
`DataSource = "SYNTHETIC_DEMO"`.

Architecture: [../docs/architecture/DATA_ARCHITECTURE.md](../docs/architecture/DATA_ARCHITECTURE.md).
