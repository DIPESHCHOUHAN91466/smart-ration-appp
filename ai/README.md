# ai — the AI subsystem

Two things live here:

1. **The AI analytics service** (Python package `ai`, FastAPI on :8001): demand forecasts, stock-out risk,
   queue prediction, beneficiary risk scores, shop monitoring and alerts, optional OCR — in English, Hindi
   and Marathi. Read-only: its database account can only `SELECT`.
2. **The chatbot's content** (`chatbot/`): the Public Help knowledge base, its evaluation set and prompt
   templates. The chatbot *engine* runs inside the Python gateway (`backend/SmartRation/app/ai/chatbot`)
   because it answers the website directly; this folder is what it knows and how it is graded.

**Why a separate service?** The core ration system (bookings, QR, collections) must keep working when
analytics is slow or down — the C# API then shows "AI unavailable" and carries on. Statistical work is
also easier to write, test and explain in Python.

## Package layout — one folder per stage

```
DATA ─► preprocessing ─► models ─► training ─► inference ─► postprocessing ─► api
                                      ▲             │
                                  evaluation ◄──────┘  (backtests, accuracy report)
```

| Folder | What it does | Main files |
|---|---|---|
| `configs/` | settings from the environment / `ai/.env` (read-only DB URL, API key, thresholds) | `settings.py` |
| `preprocessing/` | read-only SQL access; rows → typed values; events → clean daily series; outlier capping | `repository.py`, `series.py` |
| `models/` | the forecasting formulas: weighted moving average, exponential smoothing, monthly-cycle seasonal average; `MODEL_VERSION` | `forecasting.py` |
| `training/` | picks, per shop and item, the model that backtests best on that history, and rates confidence | `model_selection.py` |
| `evaluation/` | one-step and rolling-horizon backtests (wMAPE); the accuracy report used for model monitoring | `backtest.py`, `report.py` |
| `inference/` | runs it: the forecast, the `AnalyticsService` that combines every analysis, OCR | `forecast.py`, `service.py`, `ocr.py` |
| `pipelines/` | rule-based analyses: inventory days-remaining, queue waits, beneficiary risk, shop monitoring, alerts | `inventory.py`, `queue.py`, `risk.py`, `shop_monitor.py`, `alerts.py` |
| `postprocessing/` | every explanation and reason code in en/hi/mr (numbers never go out without their basis) | `i18n.py` |
| `api/` | FastAPI app: `/health`, `/v1/*` (API key required), error envelope | `main.py` |
| `scripts/` | `generate_history.py` — synthetic distribution history for development (writes; never production) | |
| `tests/` | 58 tests on a throwaway SQLite database shaped like the real schema | |

There are no trained weight files: every model is a transparent formula, and "training" is choosing
between them by measured error. That keeps each forecast explainable to a shop owner or an auditor.

## Run

```powershell
cd ai
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env                       # SMARTRATION_AI_DB_URL (read-only account), SMARTRATION_AI_API_KEY
.venv\Scripts\python -m pytest               # 58 tests (ai/pytest.ini puts the repository root on the path)
cd ..
ai\.venv\Scripts\python -m uvicorn ai.api.main:create_app --factory --host 127.0.0.1 --port 8001
ai\.venv\Scripts\python -m ai.evaluation.report     # forecast accuracy per shop and item (read-only)
```

The package is imported as `ai`, so commands that import it run from the **repository root**; only
`pytest` and `scripts\generate_history.py` run inside `ai/`. On the synthetic development history
(2026-09-28) the report gives 60 forecasts, median wMAPE 0.375, confidence 34 MEDIUM / 26 LOW — honest
numbers for noisy synthetic data, which is why every forecast ships with its range and confidence. Docs at http://127.0.0.1:8001/docs. Lint: `backend\SmartRation\.venv\Scripts\python -m ruff check ai`.

Chatbot content:
```powershell
cd backend\SmartRation
.venv\Scripts\python -m app.ai.chatbot.evaluate      # score the assistant on chatbot/evaluation (en/hi/mr)
```

## How it connects

- The C# API calls the service over HTTP with a shared key (`AiService:ApiKey` = `SMARTRATION_AI_API_KEY`);
  the Python gateway's `/health` reports whether it is up. `/health` here also reports `forecast_model`.
- It reads MySQL with the read-only `smartration_ai` account (`database/schema/mysql-setup.sql`).
- The gateway loads `chatbot/knowledge` at startup (`CHATBOT_KNOWLEDGE_DIR` overrides; the Docker image
  copies it in).

## Safety rules

Forecasts refuse to produce a number with under 14 days of history and always report data sufficiency,
confidence and model version; alerts are review prompts, never proof of wrongdoing; OCR masks Aadhaar and
mobile numbers and never replaces verification; no personal data is stored in this folder.

Architecture: [../docs/architecture/AI_ARCHITECTURE.md](../docs/architecture/AI_ARCHITECTURE.md).
