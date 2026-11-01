"""LOAD: write clean tables into the database (full refresh)."""
import logging
import sqlite3

log = logging.getLogger("etl.load")


def load(tables, db_path):
    conn = sqlite3.connect(db_path)
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
        log.info("Loaded %-15s rows=%d", name, len(df))
    conn.close()
