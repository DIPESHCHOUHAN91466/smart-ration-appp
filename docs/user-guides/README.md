# User guides

How each kind of user works with Smart Ration (web app, English / हिंदी / मराठी — switch with the language
menu; the choice is remembered).

| Guide | For | Signs in as |
|---|---|---|
| [CITIZEN.md](CITIZEN.md) | ration-card holders: book a slot, show the QR, check verification and history; Public Help without an account | Rural user |
| [SHOP_OWNER.md](SHOP_OWNER.md) | fair-price shop operators: today's queue, QR / OTP verification, handing over rations, stock | Shop owner |
| [GOVERNMENT_OFFICIAL.md](GOVERNMENT_OFFICIAL.md) | district and state officials, administrators: statistics, shops, map, AI centre, audit, reports | Government official / Admin |

**This installation uses synthetic data.** Every person, ration card, Aadhaar reference (always masked,
`XXXX-XXXX-1234`) and shop is invented. OTP text messages are not really sent in the demo. Nothing you do
here affects a real citizen.

**Demo accounts** (only when the demo was set up with a password — `SEED_DEMO_PASSWORD`; the login page
lists them in demo builds): `rural@example.com` (citizen), `shop@example.com` (shop owner),
`officer@example.com` (official). New citizens can also register themselves; self-registration always
creates a citizen account, never a shop or official account.

**Getting help:** the Ration Mitra assistant (chat button, bottom right) answers questions about documents,
booking, QR codes and schemes from reviewed content. It never asks for, and refuses to handle, Aadhaar
numbers, OTPs or passwords.
