# Government official guide

For district / state officials and administrators. Officials see every shop; nothing on these pages changes
a citizen's entitlement — they are for oversight.

| Page | What it shows |
|---|---|
| **Dashboard** | today's collections, bookings, shops and alerts across the area |
| **Statistics** | bookings and completed collections over a date range, per shop, with efficiency (completed ÷ booked) |
| **Bookings** | all bookings with status, shop and slot |
| **Shops** | every fair-price shop and its performance |
| **Beneficiaries** | registered citizen accounts with their contact details (Aadhaar is never stored in full, only `XXXX-XXXX-1234`) |
| **Inventory** | stock per shop and commodity, low-stock items |
| **Smart Ration Map** | shops on a map with their stock and activity |
| **AI Intelligence Center** | forecasts of demand for the next days per shop and item, stock-out risk, queue predictions, beneficiary risk scores and alerts — each with its basis (days of data, confidence, model version) and in your language |
| **Synthetic Data** | the synthetic beneficiary dataset with search, district / verification filters and paging (development and demo tooling; generating data is a command-line tool, `.\sr.ps1 synthetic`) |
| **Database Viewer** | read-only, paged view of selected tables (beneficiaries, family members, tokens, collections, inventory, AI insights, audit logs); no password or token hashes are exposed and nothing can be edited |
| **Audit Log** | who did what and when: sign-ins, failed sign-ins (e-mail masked), scans, OTP attempts, collections |
| **Reports** | report summaries (daily collections and others); file export is marked where it is not implemented yet |

## Reading the AI Intelligence Center

- A forecast appears only with **at least 14 days of history**; otherwise the page says there is not enough
  data instead of guessing.
- **Confidence** (LOW / MEDIUM / HIGH) comes from how much history there is and how well the method predicted
  the past (backtest error). Treat LOW as a rough indication.
- **Alerts and risk scores are prompts to review, never proof of wrongdoing.** Check the underlying bookings
  and audit entries before acting on one.
- If the AI service is not running, the page says "unavailable"; bookings and collections are not affected.

## Data mode

This installation runs on **synthetic data** (`DATA_MODE=synthetic`). Using real citizens' data requires the
integrations and legal steps in `deployment/production/CHECKLIST.md`; until then the system refuses to start
in real-data mode.
