# Google Play — what to upload and what to type

Everything here matches what the app really does (Google removes apps whose listing promises features that do not
exist). File to upload: `SmartRation-v1.0.4-playstore.aab` (built from `smart_ration_mobile`, signed with the upload
key `android/smart-ration-upload.jks`). Each new version needs a higher `version: x.y.z+N` in `pubspec.yaml`.

## 0. Before you start

- **Back up the upload key**: copy `smart_ration_mobile/android/smart-ration-upload.jks` and
  `smart_ration_mobile/android/key.properties` (it holds the key's passwords) to a private place you will not lose
  (e.g. an encrypted USB stick or your private Google Drive). Without them you cannot publish updates until Google
  resets the key, which takes days.
- **New personal developer accounts** must run a **closed test with at least 12 testers for 14 days in a row**
  before Google allows a public (production) release. Start the closed test the same day the account is ready.

## 1. Store listing

**App name** (30 max): `Smart Ration AI`

**Short description** (80 max):
`Book a time to collect your ration and show a QR token at the shop. Demo.`

**Full description:**

```text
Smart Ration AI helps people collect their monthly ration without waiting in long queues, and helps fair price
shops and officials keep distribution fair and transparent. This is a public demonstration that runs on sample
(synthetic) data.

FOR CITIZENS
• Book a 5-minute time slot at your fair price shop.
• Show your booking as a signed QR token at the shop; it stays available without internet.
• See your family's monthly entitlement and your collection history.
• File a complaint and follow its status.
• Ask the Ration Mitra assistant by typing or speaking, in English, Hindi or Marathi.
• Download a copy of your data, or close your account, from My account.

FOR SHOP OWNERS
• Scan a citizen's QR token with the camera to confirm a collection.
• See today's bookings and keep stock counts up to date.

FOR OFFICIALS
• Follow distribution, stock and complaints across shops, with alerts when stock may run short.

Demo accounts (sample data) are offered on the sign-in screen. Sign-in codes by SMS are not sent in this demo:
sign in with email and password.

This app is an independent demonstration project. It is not an official app of, and is not affiliated with,
any central or state government department.
```

**Graphics** (Play requires them): app icon 512×512 PNG; feature graphic 1024×500; at least 2 phone screenshots
(take them on your phone: sign-in with demo buttons, citizen home, booking QR, shop scanner).

**Category:** Tools (or Productivity). **Contact email:** dipeshchouhan9146@gmail.com

## 2. App content (Policy → App content)

| Question | Answer |
|---|---|
| Privacy policy URL | `https://smartration-api-prod.azurewebsites.net/privacy` |
| App access | "All or some functionality is restricted" → add instructions: *On the sign-in screen tap "Email & password", then tap "Government Official", "Shop Owner" or "Rural User": the demo email and password are filled in. Tap Sign in.* (the demo password is shown on that screen) |
| Ads | No ads |
| Content rating | Fill the questionnaire: no violence, no user-to-user chat, no gambling → rated for everyone |
| Target audience | 18 and over |
| News app | No |
| Government app | **No** (independent project; the disclaimer is in the description) |
| Financial features | None |
| Health | None |
| Data deletion: in-app | Yes: My account → Close my account |
| Data deletion: web link | `https://smartration-api-prod.azurewebsites.net/privacy` (section "Your rights": Settings → Close my account, or write to the contact email) |

## 3. Data safety form

Data is **encrypted in transit** (HTTPS): **Yes**. Users can **request deletion**: **Yes**. Data **shared** with third
parties: **No**. **Independent security review: No** (that answer is only for a review by an accredited lab).

| Data type | Collected | Optional? | Purpose |
|---|---|---|---|
| Name | Yes | Required | Account management, app functionality |
| Email address | Yes | Required | Account management |
| Phone number | Yes | Required | Account management, app functionality |
| User IDs (account, ration card) | Yes | Required | App functionality |
| App interactions / other user-generated content (bookings, complaints) | Yes | Optional | App functionality |
| Audio | **No** | | Speech is turned into text by the phone; the app does not store or send audio |
| Photos / camera | **No** | | The camera only reads QR codes live; no picture is kept |
| Location, contacts, files, payment info | **No** | | |

## 4. Steps in Play Console (in order)

1. play.google.com/console → create the developer account (personal, US$25, identity check: 1–2 days).
2. **Create app** → name `Smart Ration AI`, default language English (India), App, Free; accept the declarations.
3. **App content**: everything in section 2. **Store listing**: section 1. **Data safety**: section 3.
4. **Testing → Closed testing** → create a track → **Create release** → upload the `.aab` → accept Play App Signing
   (Google keeps the final signing key; the `.jks` above is your upload key) → release notes:
   `First release: booking, QR tokens, shop scanner, officer dashboards, Hindi and Marathi.` → **Review and roll out**.
5. Testers: add at least 12 Gmail addresses (an email list), share the opt-in link with them; each must accept and
   install from Play, and stay opted in for 14 days.
6. After 14 days: **Dashboard → Apply for production**, answer the questions, then **Production → Create release**
   with the same (or a newer) `.aab`. Google review usually takes 1–7 days.

**Updates later:** raise `version` in `pubspec.yaml` (e.g. `1.0.5+6`), build
`flutter build appbundle --release --dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://smartration-api-prod.azurewebsites.net --dart-define=DEMO_PASSWORD=<demo password>`,
then Production → Create release → upload. Phones with the Play version get the update automatically.

**Note:** an APK installed by hand (from WhatsApp or USB) is signed differently from the Play version; uninstall it
before installing from Play.
