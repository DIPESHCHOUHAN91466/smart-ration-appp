# Documentation

**What is this?** Every human-readable explanation of Smart Ration HSD2C. **Why?** So anyone can
understand, run, change and explain the system without reading all the code. **Belongs here:**
architecture, guides, decisions, status. **Doesn't:** code, secrets, generated output.

| Start here | |
|---|---|
| [../README.md](../README.md) | what it is, how it works, how to run/test/deploy (one page) |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) · [../DEVELOPMENT.md](../DEVELOPMENT.md) · [../TESTING.md](../TESTING.md) · [../DEPLOYMENT.md](../DEPLOYMENT.md) | one-page overviews of each topic |
| [user-guides/](user-guides/README.md) | how citizens, shop owners and officials use the app |
| [development/LOCAL_SETUP.md](development/LOCAL_SETUP.md) | from a fresh clone to a running app |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | what works, what's partial, what's blocked (PASS / PARTIAL / FAIL / NOT TESTED) |
| [PROJECT_AUDIT.md](PROJECT_AUDIT.md) | the latest full audit |

| Folder | Documents |
|---|---|
| `architecture/` | [SYSTEM](architecture/SYSTEM_ARCHITECTURE.md) · [FRONTEND](architecture/FRONTEND_ARCHITECTURE.md) · [BACKEND](architecture/BACKEND_ARCHITECTURE.md) · [PYTHON](architecture/PYTHON_ARCHITECTURE.md) · [AI](architecture/AI_ARCHITECTURE.md) · [DATA (synthetic → real)](architecture/DATA_ARCHITECTURE.md) |
| `api/` | [API.md](api/API.md) — conventions and every endpoint; `openapi/` — generated contracts ([README](api/README.md)) |
| `database/` | [DATABASE_ARCHITECTURE](database/DATABASE_ARCHITECTURE.md) · [BACKUP_RESTORE](database/BACKUP_RESTORE.md) · [DB_TESTING (100-record plan)](database/DB_TESTING.md) |
| `chatbot/` | [CHATBOT_ARCHITECTURE](chatbot/CHATBOT_ARCHITECTURE.md) |
| `security/` | [SECURITY_ARCHITECTURE](security/SECURITY_ARCHITECTURE.md) (policy: [../SECURITY.md](../SECURITY.md)) |
| `testing/` | [TESTING](testing/TESTING.md) · [LOAD_TESTING](testing/LOAD_TESTING.md) |
| `deployment/` | [DEPLOYMENT](deployment/DEPLOYMENT.md) · [RENDER](deployment/RENDER.md) · [NATIVE_DEPENDENCIES](deployment/NATIVE_DEPENDENCIES.md) (environments and checklists: [../deployment/](../deployment/README.md)) |
| `development/` | [LOCAL_SETUP](development/LOCAL_SETUP.md) · [TROUBLESHOOTING](development/TROUBLESHOOTING.md) |
| `user-guides/` | [CITIZEN](user-guides/CITIZEN.md) · [SHOP_OWNER](user-guides/SHOP_OWNER.md) · [GOVERNMENT_OFFICIAL](user-guides/GOVERNMENT_OFFICIAL.md) |
| `migration/` | [MIGRATION_GUIDE](migration/MIGRATION_GUIDE.md) · [MIGRATION_AUDIT](migration/MIGRATION_AUDIT.md) (C# → Python history) |
| `archive/` | superseded documents, kept for history |
