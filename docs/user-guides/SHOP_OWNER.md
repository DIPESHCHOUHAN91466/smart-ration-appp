# Shop owner guide

For the operator of a fair-price shop. Your account is linked to one shop; you only ever see that shop's
bookings, stock and beneficiaries.

## Dashboard

Today's bookings, collections so far and stock at a glance.

## Today's Queue

Everyone booked for today in slot order, with the token status (confirmed, collected, cancelled). Use it to
see who is next and who has already collected.

## Hand over rations — QR Verification

1. **Scan** the citizen's QR code with the camera (allow camera access when the browser asks), or type the
   reference printed under the QR (`SRQR-…`) if the camera can't read it.
2. The server checks the QR's signature and the booking. You see one of:
   - **Verified** — the beneficiary, family members, this month's entitlement, previous collections and an
     audit timeline; mobile number masked, Aadhaar shown only as `XXXX-XXXX-1234`.
   - A clear refusal: invalid or tampered QR, expired, cancelled booking, **already collected**, booked at
     another shop, or not eligible. Do not hand over rations on a refusal.
3. **No QR or it won't scan?** Use **Mobile OTP Verification**: a one-time code goes to the citizen's
   registered number (in the synthetic demo no SMS is really sent). Wrong codes are limited and every attempt
   is logged.
4. **Confirm Ration Collection.** Stock moves from available to distributed in the same step and a receipt
   is shown. Confirming twice is safe: the second attempt is recognised and nothing is issued twice.

Every scan, OTP attempt and collection is recorded in the audit log with your account.

## Inventory

Each commodity's **available** quantity, what has been allocated, and the **minimum threshold** that
triggers a low-stock warning. You can correct the available quantity and threshold after a physical count;
every change is written to the stock ledger.

## Notifications and Settings

Stock and system notices; language and your profile.
