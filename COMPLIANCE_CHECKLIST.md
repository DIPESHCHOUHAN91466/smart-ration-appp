# Compliance Checklist — Government of India readiness

Status of Smart Ration HSD2C against the Guidelines for Indian Government Websites (GIGW 3.0), WCAG 2.1 AA, the
Digital Personal Data Protection Act 2023 (DPDP), data localisation and a CERT-In empanelled security audit.
Branch `audit-and-deploy`, 2026-10-02. ✅ done · 🟡 partly / draft · ❌ missing · 👤 needs the owner or an outside body.

## 1. GIGW basics

| Requirement | Status | Notes |
|---|---|---|
| Bilingual content (English + Hindi) | ✅ | English, Hindi and Marathi on the website, the app, the AI assistant and the chatbot; backend error texts are English (the apps translate the ones they show). |
| Privacy Policy, Terms of Use (incl. copyright, hyperlinking, disclaimer) | 🟡 | `/privacy`, `/terms` in en/hi/mr (8ff3d8b). Operator details are `[PLACEHOLDERS]`; legal review and official translation needed 👤. |
| Accessibility Statement | 🟡 | `/accessibility` (8ff3d8b); fill in contact and the manual-audit findings 👤. |
| Contact / Help / FAQ | ✅ | Contact section (`/#contact`, linked in the footer), Public Help + chatbot (`/help`). Replace demo helpline/office details with the real ones 👤. |
| Feedback mechanism | ✅ | Complaints with reference numbers (web and app); accessibility feedback via the statement. |
| Footer: owning department, "last updated" | 🟡 | Policy pages show "Last updated"; add the owning ministry/department name and a site-wide last-updated date 👤. |
| Content policies: CMAP, Content Review, Archival | ❌ 👤 | Organisational documents required by GIGW; templates are not part of the code. |
| Sitemap page, site search | ❌ | Not built (small, can be added). |
| Link to the National Portal (india.gov.in) | ❌ | Add once the operator confirms placement. |
| `.gov.in` / `.nic.in` domain, State Emblem use per the Emblem Act | 👤 | Via NIC; the HSD2C branding must be reviewed against government identity rules. |
| STQC GIGW compliance certification | 👤 | After the items above. |

## 2. Accessibility (WCAG 2.1 Level AA)

| Check | Status | Evidence |
|---|---|---|
| Automated WCAG 2.1 A/AA scan (axe-core) | ✅ | 0 violations on 25 pages (7 public + all scanned signed-in pages, 3 roles); was 66 (18297d9). Runs in `tests/e2e/accessibility.spec.js`. |
| Keyboard use, skip link | ✅ | "Skip to main content" first on every page; browser tests drive the forms by keyboard-accessible roles. |
| Screen-reader names and announcements | ✅ | Labels on every control found by the scan; errors and toasts announced (bc5b645). |
| Colour contrast ≥ 4.5:1 | ✅ | Muted text, table headers, green/red text fixed (18297d9). |
| Text resize, high contrast, reduced motion | ✅ | Settings page (signed in); app supports large text (tested on a small phone at 130%). |
| Android app accessibility | ✅ | Semantics labels, live regions, large touch targets, every screen tested in 3 languages at large text. |
| **Manual audit** (NVDA/JAWS/TalkBack, keyboard-only walk-through, zoom 200%) | ❌ 👤 | Automated tools find roughly a third of WCAG issues; a manual audit is required before certification. |
| Known limitation: the shop map | 🟡 | Visual only; the same data is on the Shops list (stated in the Accessibility Statement). |

## 3. Multilingual support

| Item | Status |
|---|---|
| English + Hindi (+ Marathi) everywhere a person reads text | ✅ |
| Structure for more Indian languages | ✅ Web: add a block in `frontend/src/i18n/translations.js` + `publicStrings.js` and the policy texts in `pages/legal/legalContent.js` (tests fail if a key is missing). App: add `lib/l10n/app_<code>.arb` (test enforces completeness). Chatbot: add the language to `ai/chatbot/knowledge/*.json` (evaluation must stay at 100%). |
| Speech in each language | 🟡 Uses the phone's speech services; Marathi read-aloud needs the voice pack on the device. |

## 4. DPDP Act 2023

| Requirement | Status | Notes |
|---|---|---|
| Notice (privacy policy) in the person's language | 🟡 | Drafted (en/hi/mr); needs the operator's details and legal review 👤. |
| Informed consent before processing; proof of consent | ✅ | Website registration requires consent; `CONSENT_GIVEN` audit row with time (7687a7d). |
| Purpose limitation, data minimisation | ✅ | Aadhaar never collected or shown in full; masked mobiles for shops; no analytics/advertising/trackers; chat and assistant text never stored. |
| Rights: access, correction, erasure, grievance, nomination | 🟡 | Stated in the policy with a Grievance Officer contact; **no in-app erasure/export request** yet (handled by email). Recommended: a "request my data / delete my account" flow 👤 decide. |
| Grievance Officer named and reachable | ❌ 👤 | Placeholder in the policy. |
| Retention periods and deletion | ❌ 👤 | Placeholder; needs the department's record-retention rules, then a scheduled clean-up job. |
| Personal data breach process (notify the Board and affected people) | ❌ 👤 | Organisational process; logs and audit trail support investigation. |
| Security safeguards | ✅ | See SECURITY_REPORT.md. |
| Children's data | ✅ | Only as family members on a ration card; adult accounts only. |
| Significant Data Fiduciary obligations (DPIA, audits, DPO) | 👤 | If notified as one (likely for a state PDS service). |

## 5. Data stored in India

| Option | Data in India? | Use |
|---|---|---|
| **Render + Aiven (current blueprint)** | **No** for Render (no Indian region; nearest Singapore). Aiven offers Indian regions on paid plans. | **Synthetic-data demo/staging only.** |
| NIC MeghRaj (GI Cloud) | Yes | Preferred for central/state government. |
| MeitY-empanelled commercial clouds: AWS (Mumbai, Hyderabad), Microsoft Azure (Central India – Pune, South India – Chennai, West India – Mumbai), Google Cloud (Mumbai, Delhi), and Indian providers (e.g. CtrlS, Yotta, ESDS, Sify) | Yes, when the Indian regions are used | Production. **Check the current MeitY empanelment list and the empanelled service type before procurement** 👤. |

The application is cloud-agnostic (one Docker image + managed MySQL 8 + environment variables), so it moves to any
of these without code changes (DEPLOYMENT_GUIDE.md).

## 6. CERT-In empanelled security audit — what the auditor will check, and where we stand

| Area the auditor tests | Ready? | Where |
|---|---|---|
| OWASP Top 10 (web) and API Security Top 10: access control, injection, auth, sessions | ✅ | SECURITY_REPORT.md |
| OWASP Mobile Top 10 / MASVS for the Android app: storage, network, code, permissions | 🟡 | Encrypted storage, HTTPS-only release, backups off, no secrets in the app; certificate pinning and root detection not implemented. |
| TLS configuration and certificates | 👤 | On the host (A grade on SSL Labs expected); HSTS is sent. |
| Security headers, CSP, cookies | ✅ | CSP, HSTS, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy. |
| Brute force, rate limiting, account lockout | ✅ | Per-IP limits + per-account lockout (4a83231). |
| File uploads | ✅ | Type, size and file signature checked (9d67270). |
| Error handling (no stack traces), logging without personal data | ✅ | Live check verifies no internals in errors. |
| Outdated components | ✅ | pip-audit / npm audit clean; CI repeats on every push. |
| Secrets management | 🟡 | S1 in SECURITY_REPORT.md: rotate the local development secrets 👤. |
| Server hardening, patching, backups, DR | 👤 | Hosting-dependent; backup scripts exist (`scripts/database/backup.ps1`, `deployment/scripts/backup-mysql.sh`). |

**To give the auditor:** a staging URL with synthetic data, one test account per role, the API description
(`docs/api/openapi/python-api.openapi.json`), PROJECT_OVERVIEW.md, SECURITY_REPORT.md, this checklist, and the
Android release APK. The audit ends with a "safe to host" certificate valid for a limited period; re-audit after
major changes.
