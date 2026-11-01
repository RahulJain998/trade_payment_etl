"""Central config: paths and tolerances."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "trade_payments.db"
SQL_FILE = BASE_DIR / "sql" / "checks.sql"
OUTPUT_DIR = BASE_DIR / "output"

AMOUNT_TOLERANCE = 0.01      # calculation / reconciliation tolerance
