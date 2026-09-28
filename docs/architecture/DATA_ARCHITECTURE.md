# Data architecture — synthetic today, real later

## The rule

**Business logic never talks to a synthetic generator directly.** It asks an interface; configuration
(`DATA_MODE`) decides which implementation answers.

```
            registration / verification / seeding code
                              │ (interfaces only)
          ┌───────────────────┴────────────────────┐
  DATA_MODE=synthetic (default)            DATA_MODE=real
  Synthetic* providers                     Real* providers
  fabricated, labelled records             BLOCKED — REQUIRES EXTERNAL INTEGRATION
                                           (app refuses to start)
```

| Concern | Interface | Synthetic implementation (today) | Real implementation |
|---|---|---|---|
| New citizen's household, beneficiary, verifications (Python) | `DataProvider` (`app/services/data_provider.py`) | `SyntheticDataProvider` | `RealDataProvider` — refuses |
| Aadhaar verification (C#) | `IAadhaarVerificationService` | `SyntheticAadhaarVerificationService` | not implemented — startup refused |
| Passbook / ration-card registry (C#) | `IPassbookVerificationService` | `SyntheticPassbookVerificationService` | not implemented — startup refused |
| OTP (C#) | `IOtpService`, `ISmsProvider` | `SyntheticOtpService`, `MockSmsProvider` | `HttpSmsProvider` exists (gateway config required); refused outside Development if mocks are on |
| Reference data (items, shops, schemes) | JSON in `database/seeds/synthetic/` | seeded into empty tables | from the state department — not available |

## Configuration

| Setting | Values | Effect |
|---|---|---|
| `DATA_MODE` (both backends; C# also reads `DataMode`) | `synthetic` (default) / `real` | chooses providers; `real` stops startup today |
| `Demo:UseSyntheticAadhaar`, `Demo:UseSyntheticPassbook` (C#) | `true` | `false` without a real provider stops startup (they used to be ignored) |
| `SYNTHETIC_DATA_DIR` (Python) | path | where the reference JSON is read from |

## How synthetic records are marked

- Every generated household, member, beneficiary and verification row: `DataSource = "SYNTHETIC_DEMO"`.
- Codes are visibly fake: `FAM-DEMO-0001`, `BEN-DEMO-0001`, `AAD-DEMO-000001`, `PB-DEMO-0001`;
  history households `BEN-HIST-*` with `@history.synthetic.invalid` emails (cannot log in).
- Aadhaar is only ever a masked reference `XXXX-XXXX-1234` that belongs to nobody.
- Bulk test citizens (`app/synthetic`, `scripts/generate_test_data.py`): `SYN-RC-<seed>-000001` ration cards,
  `90BBxxxxxx` mobiles, `@example.com` emails; see [database/seeds/README.md](../../database/seeds/README.md).
  The `Users` table has no flag column; synthetic users are identified by these reserved ranges/domains and
  by `DataSource` on their beneficiary rows.
- Reference JSON carries `"_meta": {"isSynthetic": true}`; the seeder refuses files without it.
- The UI footer and the status page say "Demonstration system / synthetic".

## Moving to real data (checklist)

1. **Separate database** — never load real personal data into this demo database.
2. **Authorised integrations** — state PDS / ration-card registry API; UIDAI-authorised eKYC through a
   licensed AUA/KUA; a DLT-registered SMS gateway. Implement `Real*` providers behind the interfaces above.
3. **Legal and privacy** — consent capture, purpose limitation and retention under the Digital Personal
   Data Protection Act, 2023; Aadhaar Act restrictions on storing/using Aadhaar numbers.
4. **Security review** — penetration test, key rotation (JWT key is in old git history), HttpOnly
   refresh cookie, audit log retention, backups and restore rehearsal.
5. **Data migration plan** — how real households map to `Families`/`Beneficiaries`; no synthetic rows.
6. Only then change the startup guard to allow `DATA_MODE=real` with the real providers configured.

Details and owners: [../../database/seeds/REAL_DATA.md](../../database/seeds/REAL_DATA.md).
