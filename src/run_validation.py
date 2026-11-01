"""Main pipeline: load -> SQL checks -> Python checks -> Excel report -> exit code."""
import logging
import re
import sqlite3
import sys
from datetime import datetime

import pandas as pd

import validators as v
from config import DB_PATH, OUTPUT_DIR, SQL_FILE

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("validation")


def parse_sql_checks(path):
    """Read '-- name: X | SEVERITY' + query blocks from checks.sql."""
    blocks = re.split(r"^-- name:\s*", path.read_text(), flags=re.M)[1:]
    checks = []
    for b in blocks:
        header, query = b.split("\n", 1)
        name, severity = [x.strip() for x in header.split("|")]
        checks.append((name, severity, query.strip().rstrip(";")))
    return checks


def run_checks(conn):
    results = []  # (name, severity, dataframe)
    for name, sev, query in parse_sql_checks(SQL_FILE):
        results.append((name, sev, pd.read_sql(query, conn)))

    payments = pd.read_sql("SELECT * FROM trade_payments", conn)
    agreements = pd.read_sql("SELECT * FROM agreements", conn)
    results += [
        ("Calculation mismatch", "HIGH", v.check_calculation(payments)),
        ("Rebate pct differs from agreement", "HIGH",
         v.check_agreement(payments, agreements)),
        ("Invalid or future date", "MEDIUM", v.check_dates(payments)),
        ("Wrong currency for country", "MEDIUM", v.check_currency(payments)),
    ]
    return payments, results


def build_report(payments, results, fx, out_path):
    summary = pd.DataFrame(
        [{"check": n, "severity": s, "issues_found": len(df),
          "status": "FAIL" if len(df) else "PASS"} for n, s, df in results])

    bad_ids = set()
    for _, _, df in results:
        if "payment_id" in df.columns:
            bad_ids.update(df["payment_id"].tolist())
    total, clean = len(payments), len(payments) - len(bad_ids)
    kpi = pd.DataFrame({
        "metric": ["Total records", "Records with issues", "Clean records",
                   "Data quality %", "Run time"],
        "value": [total, len(bad_ids), clean, round(clean / total * 100, 2),
                  datetime.now().strftime("%Y-%m-%d %H:%M")]})

    usd = v.add_usd(payments.dropna(subset=["amount"]), fx)
    by_country = (usd.groupby("country")["amount_usd"].agg(["count", "sum"])
                  .round(2).reset_index()
                  .rename(columns={"count": "payments", "sum": "total_usd"}))

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        kpi.to_excel(w, sheet_name="KPI", index=False)
        summary.to_excel(w, sheet_name="Summary", index=False)
        by_country.to_excel(w, sheet_name="By_Country_USD", index=False)
        for name, _, df in results:
            if len(df):
                df.to_excel(w, sheet_name=re.sub(r"[^A-Za-z0-9 _]", "", name)[:31],
                            index=False)
        for ws in w.book.worksheets:                      # auto column width
            for col in ws.columns:
                width = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(width + 2, 40)
    return summary, kpi


def main():
    if not DB_PATH.exists():
        log.error("DB not found. Run: python src/generate_data.py")
        return 2
    OUTPUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    log.info("Running validations...")
    payments, results = run_checks(conn)
    fx = pd.read_sql("SELECT * FROM fx_rates", conn)
    conn.close()

    out = OUTPUT_DIR / f"validation_report_{datetime.now():%Y%m%d_%H%M}.xlsx"
    summary, kpi = build_report(payments, results, fx, out)

    print("\n" + summary.to_string(index=False))
    print("\n" + kpi.to_string(index=False))
    log.info("Report saved: %s", out)

    failed = summary[summary["status"] == "FAIL"]
    if len(failed):
        log.warning("%d checks failed. (Hook email/Slack alert here)", len(failed))
        return 1
    log.info("All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
