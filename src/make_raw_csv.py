"""Dumps the sample DB tables to data/raw/*.csv (acts like source-system exports)."""
import sqlite3
import pandas as pd
from config import BASE_DIR, DB_PATH
import generate_data

RAW = BASE_DIR / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

generate_data.build()
conn = sqlite3.connect(DB_PATH)
files = {"sap_payments": "trade_payments", "customers": "customers",
         "agreements": "agreements", "bank_statement": "bank_statement",
         "fx_rates": "fx_rates"}
for fname, table in files.items():
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    if fname == "sap_payments":      # make raw data a bit messy like real exports
        df["customer_id"] = df["customer_id"].apply(
            lambda x: f" {x.lower()} " if isinstance(x, str) and hash(x) % 7 == 0 else x)
    df.to_csv(RAW / f"{fname}.csv", index=False)
    print(f"{fname}.csv  rows={len(df)}")
conn.close()
