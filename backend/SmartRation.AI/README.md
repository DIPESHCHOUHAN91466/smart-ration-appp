# SmartRation.AI — AI / analytics service (Python, FastAPI)

**What is this?** A read-only analytics service: demand forecasts, stock-out risk, queue prediction,
anomaly alerts, and optional OCR, in English/Hindi/Marathi.

**Why does it exist?** Statistical analysis is easier and better tested in Python; keeping it separate
means the core ration system keeps working if analytics is down (AI panels then say "unavailable").

**What belongs here:** analytics algorithms (`smartration_ai/forecasting.py`, `inventory.py`, `risk.py`,
`queue.py`, `alerts.py`), read-only data access (`repository.py`), OCR (`ocr.py`), the synthetic history
generator (`scripts/generate_history.py`, development only), tests. **What does NOT:** writing business
data (the DB account is SELECT-only), the chatbot (Python API), UI.

**How do I run it?**
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env      # SMARTRATION_AI_DB_URL (read-only account), SMARTRATION_AI_API_KEY
.venv\Scripts\python -m uvicorn smartration_ai.main:create_app --factory --host 127.0.0.1 --port 8001
.venv\Scripts\python -m pytest       # 46 tests
```
Docs at http://127.0.0.1:8001/docs.

**How does it connect?** The C# API calls it over HTTP with a shared API key
(`AiService:ApiKey` = `SMARTRATION_AI_API_KEY`); the Python API's `/health` reports whether it is up.
It reads MySQL with the read-only `smartration_ai` account.

Forecasts refuse to produce a number with under 14 days of history and always report data sufficiency
and confidence; alerts are review prompts, never proof of wrongdoing; OCR never replaces verification.
Architecture: [../../docs/architecture/AI_ARCHITECTURE.md](../../docs/architecture/AI_ARCHITECTURE.md).
