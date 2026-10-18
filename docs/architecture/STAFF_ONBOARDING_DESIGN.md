# Staff onboarding: apply, verify, approve (design approved and built 2026-10-18)

**Status:**
- Built: migration `0009_staff_applications` (it follows 0007, because the 0008 OTP-index draft is a separate
  decision), `app/services/staff_application_service.py`, `app/api/routes/staff.py`, the website's Settings card
  (citizens) and *Staff applications* page (Admins).
- Tests: `tests/api/test_staff_onboarding.py` (16), `mysql_suite/test_12_staff_onboarding.py` (3; two instances,
  mutation-checked), `frontend/tests/unit/staffOnboarding.test.jsx` (3).
- **Not built yet:**
  - requirement 6 (MFA required before an official's first page): it would lock out existing officials
    without MFA, so it is a separate owner decision;
  - the Android app screens (the website covers applying and reviewing).

**Today:**
- Self-registration always creates a citizen (`RuralUser`). The server ignores any role or shop in the request; this
  is tested and was probed live.
- Shop owners and officials exist only through seeding (`SEED_*`) or direct administration. There is no way for them
  to apply.

This design adds a safe application flow **without** ever letting a request grant privileges by itself. It needs one
new table (a migration), so it waits for the owner's approval.

## Requirements

1. Anyone signed in as a citizen may **apply** to become a shop owner of a named shop, or a government official of a
   named district or office, with supporting details (official ID or licence number, designation, office e-mail).
   Applying changes nothing about their access.
2. Only an **Admin** decides. **Approve** sets the role, and the shop for a shop owner, in one transaction; **Reject**
   keeps the role. Both need a written reason. An Admin cannot approve their own application.
3. One open application per person; at most one active owner per shop unless an Admin explicitly reassigns.
4. Every step is audited: who, when, from what, to what and why. **No identity-document images are stored**; staff
   verify documents outside the app and record only the reference they checked.
5. **Revocation:** an Admin can return a staff account to citizen. Any existing session ends at its next refresh,
   because sessions are short-lived JWTs, and the refresh token is revoked.
6. **Officials** additionally need two-factor sign-in (MFA already exists) before their first official page loads.

## Data (migration `0009_staff_applications`, additive)

| Column | Type | Notes |
|---|---|---|
| `Id` | int PK | |
| `UserId` | int FK → Users | the applicant |
| `RequestedRole` | int | 2 = ShopOwner or 3 = GovernmentOfficial only (enforced) |
| `RationShopId` | int FK → RationShops, null | required for ShopOwner |
| `Office` | varchar(200), null | district or office for officials |
| `Designation` | varchar(120) | |
| `ProofReference` | varchar(120) | the ID or licence number the reviewer checked (no image) |
| `Status` | int | Pending, Approved, Rejected, Withdrawn |
| `DecidedByUserId` | int, null | the Admin |
| `DecisionReason` | varchar(500), null | |
| `CreatedAt`, `DecidedAt` | datetime(6) | UTC |

**Indexes:**
- unique `(UserId)` where Status = Pending, enforced in code under a row lock on `Users`, since MySQL has no partial
  unique index;
- `(Status, CreatedAt)` for the review queue.

**Rollback:** drop the table (no existing data changes). Approved roles stay on `Users`, as today.

## API

| Method and path | Who | Effect |
|---|---|---|
| `POST /api/staff-applications` | citizen | create Pending; 409 if one is already open |
| `GET /api/staff-applications/mine` | citizen | own applications |
| `POST /api/staff-applications/{id}/withdraw` | the applicant | Pending → Withdrawn |
| `GET /api/admin/staff-applications?status=Pending` | Admin | the review queue (paged, as PERF-01) |
| `POST /api/admin/staff-applications/{id}/approve` | Admin, not the applicant | under `SELECT … FOR UPDATE` on the application and the user: set the role and shop; audit `STAFF_APPROVED`; revoke refresh tokens |
| `POST /api/admin/staff-applications/{id}/reject` | Admin | audit `STAFF_REJECTED` with the reason |
| `POST /api/admin/users/{id}/revoke-staff` | Admin | role → RuralUser, shop → null; audit; revoke refresh tokens |

Every route gets its explicit role guard and joins the deny-by-default list check in `test_route_access.py`.

## Website

- **Settings → "Work as a shop owner or official":** the form, plus the status of my application.
- **Admin → "Staff applications":** a queue with approve and reject, where the reason is mandatory.
- **Register page:** unchanged ("shop and government accounts are provisioned by administrators" becomes "… are
  approved by administrators after you apply from Settings").

## Tests (to write with the feature)

- A citizen applies, and nothing changes until approval: the staff APIs still answer 403.
- A non-Admin approves: 403. An Admin approves their own application: 403. Approve twice concurrently (two
  instances, MySQL): the role is set once and there is one audit row.
- Smuggling a role, shop or user id in the apply body is ignored. A shop owner of another shop applying for a shop
  that already has an owner: 409.
- Revocation ends staff access at the next refresh. Every decision writes an audit row without personal document data.

## Rollout

1. Owner approves the design and migration.
2. Build it behind the existing tests.
3. Run the migration on a disposable database (up, down, up).
4. Staging.
5. Production migration in a maintenance window, with a backup taken first.
