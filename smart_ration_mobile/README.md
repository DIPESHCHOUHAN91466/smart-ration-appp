# Smart Ration AI — Powered by HSD2C (Android app)

The Flutter Android app for the Smart Ration system. It is a client of the existing backend in
`backend/SmartRation` (FastAPI + MySQL) and never talks to the database directly.

- **Citizens:** sign in with mobile + code, ration card, family, eligibility, book a 5-minute slot,
  token with a signed QR (also shown without internet), notifications.
- **Shop owners:** today's counts, scan a customer's QR (or verify by mobile code), check every
  rule, hand over and get a receipt, today's queue, stock deliveries and write-offs.
- **Government officials / admins:** totals across shops, last 30 days, shops and their stock, alerts.
- **Everyone:** the help assistant "Ration Mitra" by typing or voice, answers read aloud;
  English, हिंदी and मराठी throughout.

## Run it (development)

1. Start the backend on this PC (port 8000), see `backend/SmartRation/README.md`.
2. Start the Android emulator, then in this folder:

   ```powershell
   flutter run
   ```

   Development builds talk to `http://10.0.2.2:8000` (this PC as seen from the emulator) and show
   demo hints. Demo accounts are listed in the project's main README.

## Check it

```powershell
flutter analyze
flutter test
```

The tests use a fake backend, a fake camera, a fake microphone and a fake speaker. They include every
main screen in all three languages on a small phone with large text.

## Release

See [RELEASE.md](RELEASE.md) (upload key, release build, Play Store checklist) and
[PRIVACY_POLICY.md](PRIVACY_POLICY.md) (to be completed and published before release).

## Where things are

| Folder | What |
| --- | --- |
| `lib/app/` | settings (`env.dart`), theme, screen addresses and sign-in rules |
| `lib/core/` | the backend client, saved sign-in, offline copies, online/offline status |
| `lib/features/` | one folder per area: auth, citizen, booking, shop, official, help, notifications |
| `lib/l10n/` | all sentences in English (`app_en.arb`), Hindi and Marathi |
| `test/` | automated tests and the fake backend they use |
