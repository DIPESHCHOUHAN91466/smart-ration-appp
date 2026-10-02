# Releasing Smart Ration AI (Android)

How to build a release of the app and what to check before it goes to Google Play.
**Nothing is uploaded to Google Play by any script here.** Publishing is always a manual,
deliberate step by the app owner.

## 1. One time: create your upload key

Google Play recognises your app by the key it is signed with. You create this key **once** and keep
it safe for as long as the app exists.

- **WHERE:** any folder **outside this project**, e.g. `D:\keys\` (create it first)
- **COMMAND (PowerShell):**

  ```powershell
  & "D:\dev\jdk-21\bin\keytool.exe" -genkeypair -v -keystore "D:\keys\smart-ration-upload.jks" -storetype PKCS12 -keyalg RSA -keysize 2048 -validity 10000 -alias upload
  ```

- **PURPOSE:** creates your private upload key. It asks for a password and your name/organisation.
- **EXPECTED:** `Storing D:\keys\smart-ration-upload.jks`

Then create the file `smart_ration_mobile/android/key.properties` (it is git-ignored, never commit it):

```properties
storeFile=D:/keys/smart-ration-upload.jks
storePassword=YOUR-KEYSTORE-PASSWORD
keyAlias=upload
keyPassword=YOUR-KEY-PASSWORD
```

**Keep safe:** back up the `.jks` file and both passwords somewhere other than this PC (for example an
encrypted USB drive and a password manager). Never email them or put them in the repository.
When you create the app in Play Console, keep **Play App Signing** turned on: Google then holds the
final signing key, and a lost upload key can be reset through Play support.

Without `key.properties`, a release build stops with *"Release builds need android/key.properties"*.
That is deliberate: it can never be signed with the debug key by mistake.

## 2. Build the release

Release builds only accept `APP_ENV=staging` or `APP_ENV=production` with an **https** server address.
Development settings (plain http to this PC, demo hints) are refused, both here and when the app starts.

1. **Raise the version** in `pubspec.yaml` before every upload: `version: 1.0.0+1` → `1.0.1+2`
   (the number after `+` must always go up).
2. **Check everything:**
   - WHERE: `smart_ration_mobile/`
   - COMMAND: `flutter analyze` then `flutter test`
   - EXPECTED: `No issues found!` and `All tests passed!` (203+ tests, including every screen in
     English, Hindi and Marathi on a small phone with large text)
3. **Build the bundle for Google Play:**
   - COMMAND: `flutter build appbundle --release --dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://YOUR-SERVER`
   - EXPECTED: `Built build\app\outputs\bundle\release\app-release.aab`
4. (Optional) **APKs for direct testing on phones:**
   - COMMAND: `flutter build apk --release --split-per-abi --dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://YOUR-SERVER`
   - EXPECTED: three APKs of about 22–29 MB. Most phones need `app-arm64-v8a-release.apk`.

Verified on 2026-10-02 with a throwaway test key: the release build is signed (APK Signature
Scheme v2), not debuggable, blocks plain http, excludes app data from backups, asks only for Internet,
Camera, Microphone and Network-state permissions, and runs correctly in English and Hindi after code
shrinking (R8).

## 3. Before the first release: the server

The app is only as ready as the backend it talks to (`backend/SmartRation`):

- [ ] Served over **https** with a valid certificate, at a public address.
- [ ] **Real data mode**, with the demo OTP switched off (`DEMO_OTP_ENABLED=false`; the backend
      refuses to start outside development with it on).
- [ ] A **real SMS gateway** (`SMS_PROVIDER=http`), so sign-in and counter OTP codes reach people's
      phones; the backend refuses the mock SMS provider with real data.
- [ ] `QR_SECRET` set and **never changed** afterwards (changing it makes every issued QR invalid).
- [ ] `LEGACY_API_URL` unset (the old C# API is no longer used).
- [ ] Database migrated to the latest version after a backup (`alembic upgrade head`; this app needs
      revision `0003_stock_movement_keys`, which protects stock deliveries and write-offs from being
      recorded twice).
- [ ] Regular database backups.
- [ ] If a generative AI provider is ever added to the help assistant, update `PRIVACY_POLICY.md`
      first: today questions never leave your server.

## 4. Test on real phones

Some things cannot be tested on the emulator. Before release, on at least one low-cost Android phone:

- [ ] Shop owner scans a citizen's QR **with the camera** (not just the typed code), in good and poor light.
- [ ] Ask the help assistant **by voice** in Hindi and in Marathi.
- [ ] Read-aloud in Hindi and Marathi (the phone may first download the voice).
- [ ] Airplane mode: the citizen's token QR still shows, and the shop accepts it.
- [ ] Sign out, and check the next person who signs in sees none of the previous person's data.

## 5. Google Play Console checklist

- [ ] **Privacy policy:** fill in every `[...]` in `PRIVACY_POLICY.md`, publish it as a web page, and
      enter its address in Play Console.
- [ ] **Data safety form** (answer from what the app does, and confirm with the backend operator):
  - Data collected: name, phone number, email (account); user IDs; ration and family records
    (other personal info). Used for app functionality and account management. Not shared for
    advertising. No data sold.
  - Help-chat questions are processed to answer them and not stored.
  - Audio: not collected by the app (the phone's speech service converts it to text).
  - Data is encrypted in transit (https). Explain how users can ask for deletion (contact email).
- [ ] **Permissions:** Camera (shop owners scan customers' QR tokens), Microphone (ask questions by
      voice, important for people who find typing hard).
- [ ] **Content rating** questionnaire; **target audience** adults (18+); category *Government*/*Tools*.
- [ ] **Store listing** in English, Hindi and Marathi: short and full description, 512×512 icon,
      1024×500 feature graphic, at least two phone screenshots.
- [ ] **Testing first:** start with an internal or closed test track. New personal developer accounts
      must run a closed test with a minimum number of testers for a minimum period before production;
      check the current rule in Play Console.
- [ ] **Publishing to production only after the owner's explicit confirmation.**

## 6. Known limitations of this version

- **No push notifications** when the app is closed; notifications appear in the in-app inbox.
  Push needs Google Firebase (a project, a config file, backend changes).
- The backend's own messages (refusal reasons, alert texts, notification texts) are in English; the
  app translates the ones it knows and labels the rest as English.
- The backend checks booking dates but not times of day, so the app hides slots that already started.
