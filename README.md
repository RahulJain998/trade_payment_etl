# Trade Payment Data Validation Pipeline

Automated validation of trade payment data (rebates) using **Python + SQL**,
with reconciliation against bank statements and a standardised USD report.

## Problem
Trade payment data from multiple countries was validated manually in Excel
(2-3 days/month, error-prone). This pipeline automates it.

## Flow
SQLite DB (SAP-like data) -> SQL checks -> Python business rules
-> Excel report (KPI, summary, issue sheets) -> exit code / alert

## Checks
| Check | Layer | Severity |
|---|---|---|
| Duplicate invoices | SQL | HIGH |
| Missing mandatory fields | SQL | HIGH |
| Zero / negative amount | SQL | HIGH |
| Orphan customer | SQL | HIGH |
| Missing in bank statement | SQL | HIGH |
| SAP vs Bank variance | SQL | HIGH |
| Calculation mismatch (sales x % = amount) | Python | HIGH |
| Rebate % differs from agreement | Python | HIGH |
| Invalid / future date | Python | MEDIUM |
| Wrong currency for country | Python | MEDIUM |

## Run
    pip install -r requirements.txt
    python src/generate_data.py      # sample DB with injected errors
    python src/run_validation.py     # run checks, report saved in output/
    pytest tests/                    # unit tests

## Schedule (daily 2 AM, cron)
    0 2 * * * cd /path/to/project && python src/run_validation.py

Exit code: 0 = all pass, 1 = issues found, 2 = setup error.
Use it to trigger email/Slack alerts from cron / Airflow / GitHub Actions.

## Extend
- Swap SQLite for PostgreSQL/SQL Server (change the connection only)
- Add email alert in `main()` using `smtplib`
- Build a Power BI / Streamlit dashboard on the output tables

## ETL pipeline (data/raw -> DB -> validation)
    python src/etl_pipeline.py
Extract (CSV) -> Transform (trim, uppercase, types, dates) -> Load (SQLite) -> Validate.
GitHub Actions workflow: `.github/workflows/pipeline.yml` (runs on push + daily + manual).
