# Smart Ration — End-to-End Azure & Google Play Store Deployment Blueprint

This master guide provides a step-by-step roadmap to deploy the **Smart Ration (Ration Mitra)** system onto **Microsoft Azure** (cloud infrastructure) and publish the **Flutter Android App** to the **Google Play Store**, enabling citizens, fair price shop owners, and government officials across India to access the service.

---

## Architecture Overview

```
 [Google Play Store]
        │
        ▼ (Download APK / AAB)
 [Citizen / FPS Android Devices] ────────┐
   (Flutter Mobile App)                  │ HTTPS / TLS
                                         ▼
                               [Azure Container Apps / App Service]
                               ├── React 18 Web Portal (Static Host)
                               └── FastAPI Backend API (:8000)
                                         │
                        ┌────────────────┴────────────────┐
                        │ Internal TLS                    │ Internal HTTP + API Key
                        ▼                                 ▼
             [Azure Database for MySQL]         [Azure Container App (AI)]
             Flexible Server (:3306)            Predictive Engine (:8001)
             smartration-ai.mysql.database...
```

---

## Phase 1: Azure MySQL Flexible Server Setup & Schema Migration

> **Your Server Details** *(from Azure Portal)*:
> - **Server Name**: `smartration-ai.mysql.database.azure.com`
> - **Resource Group**: `SmartRation-AI`
> - **Region**: `India South Central`
> - **Admin Login**: `airationmitrahsd2c`
> - **Engine Version**: MySQL 8.4 Flexible Server (B1ms)

### Step 1.1: Configure Networking & Firewall Rules
1. In Azure Portal, navigate to **smartration-ai** -> **Settings** -> **Networking**.
2. Check the box: **"Allow public access from any Azure service within Azure to this server"** (allows your Azure Web App / Container App to connect).
3. Under **Firewall rules**, click **+ Add current client IP address** so your local machine can run migrations, then click **Save**.

### Step 1.2: Initialize Database and Least-Privilege Users
Open the Azure Cloud Shell (already open in your browser) or local terminal with the SSL root certificate:

```bash
mysql -h smartration-ai.mysql.database.azure.com -u airationmitrahsd2c -p --ssl-ca=MysqlflexGlobalRootCA.crt.pem
```

Run the following SQL commands:

```sql
-- 1. Create database
CREATE DATABASE IF NOT EXISTS smartration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Create migrator account (used to apply schema changes & DDL)
CREATE USER IF NOT EXISTS 'smartration_migrator'@'%' IDENTIFIED BY 'STRONG_MIGRATOR_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON smartration.* TO 'smartration_migrator'@'%';

-- 3. Create application account (reads and writes rows; cannot DROP or ALTER tables)
CREATE USER IF NOT EXISTS 'smartration_app'@'%' IDENTIFIED BY 'STRONG_APP_PASSWORD_HERE';
GRANT SELECT, INSERT, UPDATE, DELETE ON smartration.* TO 'smartration_app'@'%';

-- 4. Create AI analytics account (strictly read-only)
CREATE USER IF NOT EXISTS 'smartration_ai'@'%' IDENTIFIED BY 'STRONG_AI_PASSWORD_HERE';
GRANT SELECT ON smartration.* TO 'smartration_ai'@'%';

FLUSH PRIVILEGES;
EXIT;
```

### Step 1.3: Run Database Migrations & Seed Reference Data
From your local project terminal (in `backend/SmartRation`), run Alembic against your Azure MySQL server:

```powershell
cd d:\Smart_Ration_HSD2C_Final\backend\SmartRation

# Set temporary environment variable for migration
$env:MIGRATION_DATABASE_URL="mysql+pymysql://smartration_migrator:STRONG_MIGRATOR_PASSWORD_HERE@smartration-ai.mysql.database.azure.com:3306/smartration?charset=utf8mb4&ssl_disabled=false"

# Apply all Alembic migrations (creates all 27 tables)
python scripts\setup_database.py

# Verify schema integrity against SQLAlchemy models
python scripts\verify_database.py
```

---

## Phase 2: Azure Cloud Deployment of Backend API & Web Application

The root Dockerfile (`backend/SmartRation/Dockerfile`) builds both the **React frontend** and **FastAPI backend** into a single container image.

### Step 2.1: Provision Azure Container Registry (ACR)
In Azure Cloud Shell or local Azure CLI (`az`):

```bash
# 1. Create Azure Container Registry
az acr create --resource-group SmartRation-AI --name smartrationcr --sku Basic --admin-enabled true

# 2. Log in to ACR
az acr login --name smartrationcr
```

### Step 2.2: Build and Push Docker Image
From the repository root:

```bash
# Build multi-stage image (frontend build + FastAPI backend)
docker build -f backend/SmartRation/Dockerfile -t smartrationcr.azurecr.io/smartration-api:latest .

# Push image to Azure Container Registry
docker push smartrationcr.azurecr.io/smartration-api:latest
```

### Step 2.3: Deploy to Azure App Service or Container Apps
Using **Azure App Service for Containers** (Linux):

```bash
# Create App Service Plan (B1 basic or Free F1)
az appservice plan create --name smartration-plan --resource-group SmartRation-AI --sku B1 --is-linux

# Create Web App using your container
az webapp create --resource-group SmartRation-AI --plan smartration-plan --name smartration-api \
  --deployment-container-image-name smartrationcr.azurecr.io/smartration-api:latest
```

### Step 2.4: Configure Production Environment Variables
Set application settings in Azure App Service:

```bash
az webapp config appsettings set --resource-group SmartRation-AI --name smartration-api --settings \
  ENVIRONMENT="production" \
  DATABASE_URL="mysql+pymysql://smartration_app:STRONG_APP_PASSWORD_HERE@smartration-ai.mysql.database.azure.com:3306/smartration?charset=utf8mb4" \
  JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  QR_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  MFA_ENCRYPTION_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  DATA_MODE="synthetic" \
  TRUSTED_PROXY_HOPS="1" \
  CORS_ORIGINS="https://smartration-api.azurewebsites.net"
```

### Step 2.5: Verify Live Web Application
Open your browser and navigate to:
- `https://smartration-api.azurewebsites.net` (React web app landing page)
- `https://smartration-api.azurewebsites.net/health` (Health probe reporting database status)
- `https://smartration-api.azurewebsites.net/ready` (Readiness check)

---

## Phase 3: AI Analytics Engine Microservice Deployment

### Step 3.1: Deploy AI Microservice Container
The `ai/` folder contains statistical demand forecasting, stockout alerts, and queue analytics.

```bash
# Build AI image
docker build -f ai/Dockerfile -t smartrationcr.azurecr.io/smartration-ai:latest ./ai

# Push to ACR
docker push smartrationcr.azurecr.io/smartration-ai:latest

# Deploy as secondary Azure App Service
az webapp create --resource-group SmartRation-AI --plan smartration-plan --name smartration-ai-service \
  --deployment-container-image-name smartrationcr.azurecr.io/smartration-ai:latest
```

### Step 3.2: Connect AI Service with Backend
1. In `smartration-ai-service`, set:
   - `SMARTRATION_AI_DB_URL="mysql+pymysql://smartration_ai:STRONG_AI_PASSWORD_HERE@smartration-ai.mysql.database.azure.com:3306/smartration?charset=utf8mb4"`
   - `SMARTRATION_AI_API_KEY="SHARED_SECRET_KEY_HERE"`
2. In main `smartration-api`, set:
   - `AI_SERVICE_URL="https://smartration-ai-service.azurewebsites.net"`
   - `AI_SERVICE_API_KEY="SHARED_SECRET_KEY_HERE"`

---

## Phase 4: Flutter Android Mobile App Production Build & Signing

### Step 4.1: Generate Private Release Upload Key
In PowerShell (store outside the repo, e.g. `C:\keys\`):

```powershell
New-Item -ItemType Directory -Force -Path "C:\keys"

& "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe" -genkeypair -v `
  -keystore "C:\keys\smart-ration-upload.jks" `
  -storetype PKCS12 -keyalg RSA -keysize 2048 -validity 10000 `
  -alias upload
```

> ⚠️ **Back up `smart-ration-upload.jks` and your passwords safely!**

### Step 4.2: Configure `key.properties`
Create `smart_ration_mobile/android/key.properties` (git-ignored):

```properties
storeFile=C:/keys/smart-ration-upload.jks
storePassword=YOUR_KEYSTORE_PASSWORD
keyAlias=upload
keyPassword=YOUR_KEY_PASSWORD
```

### Step 4.3: Version Code Increment
Open `smart_ration_mobile/pubspec.yaml` and verify:
```yaml
version: 1.0.0+1   # Bump (+2, +3...) for every subsequent release
```

### Step 4.4: Code Shrinking & Automated Verification
```powershell
cd d:\Smart_Ration_HSD2C_Final\smart_ration_mobile
flutter clean
flutter pub get
flutter analyze
flutter test
```

### Step 4.5: Compile Release Android App Bundle (.aab)
Compile with your live Azure backend endpoint:

```powershell
flutter build appbundle --release `
  --dart-define=APP_ENV=production `
  --dart-define=API_BASE_URL=https://smartration-api.azurewebsites.net
```

The output file is generated at:
`smart_ration_mobile/build/app/outputs/bundle/release/app-release.aab`

---

## Phase 5: Google Play Store Console Setup & Public Rollout

### Step 5.1: Create Google Play Developer Account
1. Visit [Google Play Console](https://play.google.com/console/signup) and sign up ($25 one-time registration fee).
2. Complete developer identity verification.

### Step 5.2: Create App Listing
1. Click **Create app**:
   - **App name**: Smart Ration AI (Ration Mitra)
   - **Default language**: English (United States / India)
   - **App or game**: App
   - **Free or paid**: Free
2. Enable **Play App Signing** (recommended by Google).

### Step 5.3: Store Presence & Graphics
Upload required visual assets:
- **App Icon**: 512 × 512 px PNG (32-bit with alpha)
- **Feature Graphic**: 1024 × 500 px PNG/JPEG
- **Phone Screenshots**: Minimum 4 screenshots (English, Hindi, and Marathi interfaces showing slot booking, QR token, camera scanning, and Ration Mitra assistant).
- **Short Description**: "Digital PDS appointment booking, signed QR tokens, and AI assistant."
- **Full Description**: Comprehensive description of the Public Distribution System benefits, fair price shop slot reservations, multilingual voice assistant, and transparent grievance redressal.

### Step 5.4: Compliance & Declarations
1. **Privacy Policy**: Host `smart_ration_mobile/PRIVACY_POLICY.md` on your web app (e.g., `https://smartration-api.azurewebsites.net/privacy-policy`) and enter the URL in Play Console.
2. **Data Safety Form**:
   - Data Collected: Name, Mobile number, Email, Ration card identifier.
   - Purpose: App functionality, Account management.
   - Security: Data is encrypted in transit over HTTPS/TLS; users can request data export and deletion.
   - Third-Party Sharing: None. No advertising or commercial tracking.
3. **App Access**: Provide demo credentials for Google reviewers:
   - Rural Citizen: `rural@example.com` / `demo123`
   - Shop Owner: `shop@example.com` / `demo123`

### Step 5.5: Testing & Production Rollout
1. **Internal Testing**: Upload `app-release.aab` to the Internal Testing track and test on your physical Android devices.
2. **Closed Testing**: Complete 14-day closed testing with 20 opt-in testers as required by Google Play policy.
3. **Production Track**: Submit the app for Google Play Review. Once approved, click **Start rollout to Production** — the app will be live and downloadable across India!
