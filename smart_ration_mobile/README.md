# Smart Ration Mobile App (Flutter / Android) 🌾📱

The official cross-platform mobile client for **Smart Ration (Ration Mitra / राशन मित्र)**, engineered with Flutter & Dart for rural accessibility, offline resilience, and secure distribution.

## Key Capabilities by Role

- 👨‍👩‍👧 **Citizen / Beneficiary**:
  - Sign in with mobile number + OTP or email + password.
  - View ration card details, family member roster, and monthly quota balance.
  - Book 5-minute Fair Price Shop (FPS) collection slots.
  - Generate and view **cryptographically signed HMAC-SHA256 QR tokens** (with offline caching so tokens display without internet).
  - Lodge grievances with reference tracking.
  - Multilingual voice AI assistant (**Ration Mitra**) supporting English, हिंदी (Hindi), and मराठी (Marathi) with text-to-speech read-aloud.
  - Exercise DPDP Act 2023 data rights ("Download My Data" and consent verification).
- 🏬 **Fair Price Shop (FPS) Operator**:
  - Real-time queue view and appointment timeline.
  - In-app high-speed camera QR code scanner.
  - Instant cryptographic token verification & eligibility checking.
  - SMS OTP fallback validation.
  - Idempotent stock distribution handover with digital receipts.
  - Stock deliveries and write-off ledger management.
- 🏛️ **Government Officials / Inspectors**:
  - Live inspection dashboard and district summaries.
  - Real-time inventory monitoring and AI anomaly alert reviews.

---

## Technical Stack & Architecture

- **Framework**: Flutter 3.24+ / Dart 3.5+
- **State Management**: Flutter Riverpod 2 / 3
- **Navigation & Deep Linking**: `go_router`
- **Networking**: `dio` with automatic JWT bearer token interceptor and refresh-token handling
- **Hardware Integrations**:
  - `mobile_scanner`: High-speed camera QR code barcode scanner
  - `speech_to_text`: Speech recognition in English, Hindi, and Marathi
  - `flutter_tts`: Native text-to-speech narration for low-literacy users
- **Security & Storage**: `flutter_secure_storage` (Android Keystore encrypted storage for tokens, refresh tokens, and offline passbook snapshots)
- **Localization**: Native Flutter `intl` (`app_en.arb`, `app_hi.arb`, `app_mr.arb`)
- **Code Shrinking & Protection**: Android R8 / ProGuard minification enabled for release builds

---

## Directory Structure

```
smart_ration_mobile/
├── android/                 # Android native project (Kotlin DSL, build.gradle.kts)
├── ios/                     # iOS native project
├── lib/
│   ├── app/                 # Environment config (`env.dart`), theme, router (`router.dart`)
│   ├── core/                # API client, secure token storage, network connectivity manager
│   ├── features/            # Modular feature slices:
│   │   ├── auth/            # Sign in, registration, OTP, MFA, password reset
│   │   ├── citizen/         # Ration card, family members, entitlements
│   │   ├── booking/         # Slot selection, token generation, signed QR viewer
│   │   ├── shop/            # Camera QR scanner, OTP verification, stock ledger
│   │   ├── official/        # Metrics, shop monitor, AI anomaly flags
│   │   ├── grievances/      # Complaint submission and status tracking
│   │   ├── help/            # Knowledge base and Ration Mitra voice chatbot
│   │   └── notifications/   # In-app alerts and collection receipts
│   └── l10n/                # Localization ARB bundles (en, hi, mr)
├── test/                    # Comprehensive unit & widget test suites
├── pubspec.yaml             # Dependencies and app metadata
├── PRIVACY_POLICY.md        # Google Play Store privacy disclosure
└── RELEASE.md               # Step-by-step Android App Bundle (AAB) release guide
```

---

## Getting Started

### Prerequisites

- [Flutter SDK](https://flutter.dev/docs/get-started/install) (3.24 or higher)
- [Android Studio](https://developer.android.com/studio) with Android SDK (API 34 or 35) & command-line tools
- Running backend (`backend/SmartRation`) on port 8000

### 1. Development Setup

```powershell
cd smart_ration_mobile
flutter pub get
```

### 2. Run on Android Emulator or Device

For Android Emulator (uses `10.0.2.2:8000` to connect to localhost backend):

```powershell
flutter run
```

To specify the backend address explicitly:

```powershell
flutter run --dart-define=APP_ENV=development --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### 3. Run Automated Tests

The test suite validates every feature across small screens, large fonts, and all 3 languages:

```powershell
flutter analyze
flutter test
```

---

## Production Release & Google Play Store Build

To compile a release-ready **Android App Bundle (`.aab`)** for the Google Play Store:

### 1. Keystore Configuration

Ensure `smart_ration_mobile/android/key.properties` exists (this file is git-ignored and points to your release signing key):

```properties
storeFile=C:/keys/smart-ration-upload.jks
storePassword=YOUR_SECURE_STORE_PASSWORD
keyAlias=upload
keyPassword=YOUR_SECURE_KEY_PASSWORD
```

### 2. Build the Android App Bundle (AAB)

Target your deployed Azure production backend:

```powershell
flutter build appbundle --release `
  --dart-define=APP_ENV=production `
  --dart-define=API_BASE_URL=https://smartration-api.azurewebsites.net
```

The resulting file is created at:
`build/app/outputs/bundle/release/app-release.aab`

For step-by-step Google Play Console onboarding, Data Safety questionnaire answers, and testing tracks, see [RELEASE.md](RELEASE.md).
