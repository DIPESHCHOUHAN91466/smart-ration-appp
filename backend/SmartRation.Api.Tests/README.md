# SmartRation.Api.Tests — C# Backend Test Suite

Unit and integration tests for the ASP.NET Core business API (`SmartRation.Api`). Built with **xUnit** against a real **SQLite in-memory** database (`TestFixtures/TestDbFactory.cs` — deliberately not the EF InMemory provider, so queries translate as in production); fakes such as `FakeCurrentUserService` instead of a mocking library.

## Overview

This suite verifies core business rules, security constraints, and operational integrity for the Smart Ration C# API.

| Area | Test File | Key Coverage |
|---|---|---|
| **AI Integration** | `AIServicesTests.cs`, `AiAlertServiceTests.cs` | HTTP client resilience, timeout handling, fallback when AI service is offline, alert parsing |
| **Admin Database** | `AdminDatabaseBrowserServiceTests.cs` | Read-only database table inspection, pagination, query isolation |
| **Beneficiaries** | `BeneficiaryProfileServiceTests.cs` | Profile lookup, family member linking, entitlement aggregation, masked Aadhaar |
| **Collection Security** | `CollectionSecurityTests.cs` | Prevention of double-dipping, role authorization, shop-tenant boundary enforcement |
| **Data Mode Guard** | `DataModeGuardTests.cs` | Refusal to boot in `DATA_MODE=real` without verified government connectors |
| **Entitlement Engine** | `EntitlementServiceTests.cs` | Monthly quota calculation (quota × members − already collected) across schemes (PHH, AAY) |
| **Inventory & Ledger** | `InventoryLedgerAndIdempotencyTests.cs` | Optimistic concurrency on stock updates, ledger audit trails, idempotent collection transactions |
| **OTP & Fallback** | `OtpDeliveryTests.cs`, `SyntheticOtpServiceTests.cs` | 6-digit OTP generation, SHA-256 hash storage, 5-minute expiration, 3-attempt lockout, synthetic SMS logging |
| **Security & Auth** | `PasswordHashesTests.cs` | Argon2id verification and legacy BCrypt upgrade compatibility |
| **QR Code Engine** | `QrServiceTests.cs`, `QrScanServiceTests.cs` | HMAC-SHA256 signature creation and tamper detection, payload validation, token lifecycle |
| **Collection Workflow** | `RationCollectionServiceTests.cs` | End-to-end collection execution, stock decrement, and notification event dispatch |

## Running the Tests

From the repository root:
```powershell
dotnet test SmartRation.sln -c Release
```

From this directory:
```powershell
dotnet test -c Release
```

To run a specific test class:
```powershell
dotnet test -c Release --filter "FullyQualifiedName~CollectionSecurityTests"
```
