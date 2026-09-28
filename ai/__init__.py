"""Smart Ration AI analytics service (import name `ai`; run: python -m uvicorn ai.api.main:create_app --factory).

Optional, read-only decision-support layer next to the .NET API. It reads the
shared database (MySQL or SQLite) and returns forecasts, inventory analytics,
queue analytics, beneficiary risk scores and shop monitoring. The core PDS
(verification, tokens, distribution, inventory writes) never depends on it:
if this service is down, the .NET API falls back or reports "AI unavailable".

Stages: configs -> preprocessing (read-only data, clean series) -> models (forecasting formulas) ->
training (per-shop model selection by backtest) -> inference (forecast, analytics service, OCR) ->
postprocessing (explanations in en/hi/mr) -> api. evaluation/ measures accuracy; pipelines/ holds the
rule-based analyses (inventory, queue, risk, shop monitoring, alerts).
"""

__version__ = "1.0.0"
