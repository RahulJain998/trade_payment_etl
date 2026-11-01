"""Central config: paths and tolerances."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "trade_payments.db"
SQL_FILE = BASE_DIR / "sql" / "checks.sql"
OUTPUT_DIR = BASE_DIR / "output"

AMOUNT_TOLERANCE = 0.01      # calculation / reconciliation tolerance

# ---- time helpers (GitHub runners use UTC; we show IST) ----
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
HISTORY_FILE = BASE_DIR / "data" / "history" / "run_history.csv"


def now_ist():
    return datetime.now(IST)
