# mobile — Smart Ration Mobile Companion App (React Native & Expo)

> **Status (verified 2026-09-25): not implemented yet.** This folder is the unmodified Expo starter template
> (`src/app/index.tsx` and `explore.tsx` tabs). It does not call the API, scan QR codes or store tokens.
> Everything under *Overview* and *Tech Stack* below is the **planned** design, not current behaviour.

Cross-platform mobile application for citizens and Fair Price Shop owners built with **React Native 0.86**, **Expo SDK 57**, **Expo Router**, and **Zustand**.

## Overview

The mobile client brings Smart Ration capabilities directly to smartphones and handheld POS terminals used in rural distribution centres:

- **Citizen Mobile Pass**: View ration card entitlement, book 5-minute distribution slots, and present digitally signed QR tokens even in low-connectivity areas using offline SQLite token caching.
- **Shop Operator Scanner**: Use the device camera (`expo-camera`) to scan beneficiary QR tokens, verify HMAC signatures, or trigger SMS OTP fallback.
- **Offline Resilience**: Local SQLite database (`expo-sqlite`) caches valid slots and token signatures so distribution is never stalled by network outages.
- **Secure Storage**: Cryptographic keys and auth tokens are stored using device hardware security via `expo-secure-store`.

## Tech Stack

| Technology | Purpose |
|---|---|
| **Expo SDK 57** & **React Native 0.86** | Cross-platform runtime targeting Android & iOS |
| **Expo Router** | File-based routing (`src/app`) |
| **Expo Camera** | High-speed QR token scanning at Fair Price Shops |
| **Expo SQLite** | Local offline token and entitlement storage |
| **Expo SecureStore** | Encrypted token and key storage |
| **Zustand** | Lightweight client state management |
| **Axios** | Communication with the Python API Gateway (:8000) |

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Expo Go app on your physical device (Android / iOS) or Android Studio emulator / Xcode simulator

### Installation

```bash
cd mobile
npm install
```

### Running the App

```bash
# Start the Expo development server (scans QR in Expo Go)
npm start

# Run directly on Android emulator
npm run android

# Run directly on iOS simulator (macOS required)
npm run ios

# Run in web browser mode
npm run web
```

## Directory Structure

```
mobile/
├── assets/          # App icons, splash screens, and illustrations
├── scripts/         # Utility scripts (reset-project)
├── src/
│   ├── app/         # Expo Router screen definitions (_layout.tsx, index.tsx, explore.tsx)
│   ├── components/  # Themed UI components, animated icons, badges
│   ├── constants/   # Color themes, dimensions, spacing
│   └── hooks/       # Custom React hooks (color scheme, responsive layout)
├── app.json         # Expo project configuration and native permissions
└── tsconfig.json    # TypeScript compiler configuration
```

## Backend Connection

By default, the mobile app communicates with the Python API Gateway:
- Physical device: Point to your workstation's LAN IP (e.g. `http://192.168.1.X:8000/api`)
- Android Emulator: Point to `http://10.0.2.2:8000/api`
- iOS Simulator: Point to `http://localhost:8000/api`
