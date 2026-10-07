# Google Play Console — Store Listing & Compliance Kit

This document provides ready-to-copy metadata, descriptions, policy declarations, and Data Safety questionnaire answers required to publish **Smart Ration AI (Ration Mitra)** on the Google Play Store.

---

## 1. Store Listing Details

### App Title (Max 30 characters)
`Smart Ration AI - Ration Mitra`

### Short Description (Max 80 characters)
`Digital PDS appointment booking, signed QR tokens, and Ration Mitra AI assistant.`

### Full Description (Max 4,000 characters)

```text
Smart Ration AI (राशन मित्र) is a next-generation digital Public Distribution System (PDS) application designed to modernize grain distribution, eliminate crowded queues at Fair Price Shops (FPS), and empower citizens across India.

KEY CAPABILITIES FOR CITIZENS & BENEFICIARIES:
• 5-Minute Slot Reservation: Book a guaranteed collection time slot at your designated Fair Price Shop to avoid waiting in long lines.
• Cryptographically Signed QR Tokens: View your unique, tamper-proof QR appointment token. Tokens are securely cached on your device so you can display them even without an active internet connection.
• Quota & Family Transparency: Check your family roster, monthly grain entitlement balance, and past collection history in real time.
• Multilingual Ration Mitra AI Companion: Ask questions about government schemes, eligibility rules, and slot availability by speaking or typing in English, हिंदी (Hindi), or मराठी (Marathi).
• Grievance Redressal: Lodge complaints directly within the app and track official resolution milestones.
• Data Privacy (DPDP Act 2023): Exercise your right to digital privacy with instant "Download My Data" export and verifiable consent history.

FEATURES FOR FAIR PRICE SHOP (FPS) DEALERS:
• High-Speed Camera Scanner: Instant in-app QR code verification with zero delays.
• SMS OTP Fallback: Secure 6-digit OTP verification when a customer's phone screen is damaged.
• Automated Stock Ledger: Atomic, idempotent grain deduction preventing inventory mismatches.
• Real-Time Queue Management: View upcoming appointments for today at a glance.

FEATURES FOR GOVERNMENT OFFICIALS:
• Live Inspection Metrics: Real-time district-wide distribution progress.
• AI Stockout Alerts: Predictive analytics warning of impending grain shortages.
• Grievance Management: Review and resolve citizen complaints with instant citizen notifications.

LANGUAGE ACCESSIBILITY:
Available completely in English, Hindi (हिंदी), and Marathi (मराठी) with integrated speech recognition and text-to-speech read-aloud support.

DATA TRANSPARENCY NOTICE:
In demonstration mode, this application operates on synthetic demonstration data. Real-data modes connect exclusively with certified state PDS and UIDAI eKYC gateways.
```

---

## 2. Graphic Asset Requirements

| Asset | Dimensions | Format | Notes |
|---|---|---|---|
| **App Icon** | 512 × 512 px | PNG (32-bit color with alpha) | Emblem from `smart_ration_mobile/assets/icons/` |
| **Feature Graphic** | 1024 × 500 px | JPEG or PNG (no alpha) | Banner showing the Smart Ration emblem and slot booking phone mockup |
| **Phone Screenshots** | 1080 × 1920 px (or 16:9) | JPEG or PNG | Minimum 4 screenshots (Slot booking, QR token, FPS scanner, Ration Mitra voice chat) |

---

## 3. App Content & Policy Declarations

### A. Privacy Policy
- **Privacy Policy URL**: Host `smart_ration_mobile/PRIVACY_POLICY.md` on your web domain:
  `https://smartration-api.azurewebsites.net/privacy-policy`

### B. App Access (For Google Play Reviewers)
Provide test account credentials so Google's review team can test the app:
- **Username / Email**: `rural@example.com`
- **Password**: `demo123`
- **Role**: Citizen (Rural User)
- **Second Account**: `shop@example.com` / `demo123` (FPS Dealer)

### C. Government Apps Policy Declaration
- **Question**: Is your app developed by or on behalf of a government entity?
- **Answer**:
  - *If official state agency*: Select "Yes" and provide government authorization documentation.
  - *If civic tech / student / pilot project*: Select **"No"**, and include a prominent disclaimer: *"This application is a digital PDS utility developed for demonstration and public access. It is not officially affiliated with any central or state government ministry."*

### D. Target Audience & Content
- **Target Age Group**: Ages 18 and older.
- **Is this app designed for children?**: No.

### E. Financial Features Declaration
- **Answer**: "My app doesn't provide any financial features." (No payments, loans, or banking).

---

## 4. Data Safety Form Responses

When answering Google Play's **Data Safety questionnaire**, use these verified entries:

| Category | Data Type | Collected? | Shared? | Purpose | Ephemeral? |
|---|---|:---:|:---:|---|:---:|
| **Personal Info** | Name | Yes | No | App functionality, Account management | No |
| **Personal Info** | Email address | Yes | No | Account authentication | No |
| **Personal Info** | Phone number | Yes | No | Account authentication, SMS OTP | No |
| **Personal Info** | User IDs / Ration ID | Yes | No | App functionality | No |
| **Audio Files** | Voice recordings | No | No | Voice converted on-device to text; no audio saved | Yes |
| **Photos/Videos** | Camera photos | No | No | Camera used strictly for scanning QR codes live; no images saved | Yes |

### Security Practices:
- **Data Encrypted in Transit**: Yes (All network traffic enforced via HTTPS / TLS).
- **Data Deletion Mechanism**: Yes (Users can request account deletion, and citizens can download their data via DPDP Act export).
- **Independent Security Review**: Yes (Internal security and dependency audit completed).
