"""Constants shared by the AI service's conftest and test modules.

Lives in its own uniquely named module (not conftest) so tests can import it without
the tests folder being a package; works from this folder and from the repository root.
"""

from datetime import datetime

NOW = datetime(2026, 9, 24, 6, 0, 0)  # naive UTC (11:30 IST)
API_KEY = "test-api-key-000000000000000000"
