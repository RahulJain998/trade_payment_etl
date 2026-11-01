"""EXTRACT: read raw source files."""
import logging
import pandas as pd

log = logging.getLogger("etl.extract")

SOURCES = {
    "payments":   "sap_payments.csv",
    "customers":  "customers.csv",
    "agreements": "agreements.csv",
    "bank":       "bank_statement.csv",
    "fx":         "fx_rates.csv",
}


def extract(raw_dir):
    data = {}
    for name, fname in SOURCES.items():
        path = raw_dir / fname
        if not path.exists():
            raise FileNotFoundError(f"Missing source file: {path}")
        data[name] = pd.read_csv(path, dtype=str)   # read all as text, convert later
        log.info("Extracted %-10s rows=%d", name, len(data[name]))
    return data
