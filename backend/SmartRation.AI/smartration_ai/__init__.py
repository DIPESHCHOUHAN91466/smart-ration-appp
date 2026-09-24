"""Smart Ration AI analytics service.

Optional, read-only decision-support layer next to the .NET API. It reads the
shared database (MySQL or SQLite) and returns forecasts, inventory analytics,
queue analytics, beneficiary risk scores and shop monitoring. The core PDS
(verification, tokens, distribution, inventory writes) never depends on it:
if this service is down, the .NET API falls back or reports "AI unavailable".
"""

__version__ = "1.0.0"
