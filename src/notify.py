"""Sends the validation report by email (Gmail SMTP).
Credentials come ONLY from environment variables (GitHub Secrets)."""
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import pandas as pd

from config import HISTORY_FILE, OUTPUT_DIR

CSS = ("<style>body{font-family:Arial,sans-serif;font-size:14px}"
       "table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:4px 8px;"
       "text-align:left}th{background:#f2f2f2}.fail{color:#b00020;font-weight:bold}"
       ".pass{color:#0a7d33}</style>")


def build_message(summary, history, sender, to, run_url="", history_url=""):
    run = summary["run"]
    msg = EmailMessage()
    msg["Subject"] = (f"[Trade ETL] Run #{run['run_no']} | Quality {run['data_quality_pct']}% | "
                      f"{run['failed_checks']} checks failed | {run['run_time_ist']} IST")
    msg["From"], msg["To"] = sender, to

    checks = pd.DataFrame(summary["checks"])
    checks["status"] = checks["status"].map(
        lambda x: f"<span class='{x.lower()}'>{x}</span>")
    past = history.tail(10).iloc[::-1][
        ["run_no", "run_time_ist", "total_records", "records_with_issues",
         "data_quality_pct", "failed_checks"]]

    links = ""
    if run_url:
        links += f"<p><a href='{run_url}'>Open this run on GitHub</a></p>"
    if history_url:
        links += f"<p><a href='{history_url}'>Full run history (CSV)</a></p>"

    html = (f"<html><head>{CSS}</head><body>"
            f"<h3>Trade Payment Validation - Run #{run['run_no']}</h3>"
            f"<p>Time: {run['run_time_ist']} IST<br>"
            f"Total records: <b>{run['total_records']}</b> | "
            f"With issues: <b>{run['records_with_issues']}</b> | "
            f"Data quality: <b>{run['data_quality_pct']}%</b></p>"
            f"<h4>This run - check results</h4>"
            f"{checks.to_html(index=False, escape=False, border=0)}"
            f"<h4>Previous runs (latest 10)</h4>"
            f"{past.to_html(index=False, border=0)}{links}"
            f"<p>Detailed Excel report is attached.</p></body></html>")
    msg.set_content("Open this email in an HTML-capable client. Excel report attached.")
    msg.add_alternative(html, subtype="html")

    report = Path(summary["report_path"])
    if report.exists():
        msg.add_attachment(
            report.read_bytes(), maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=report.name)
    return msg


def main():
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    to = os.getenv("EMAIL_TO", user)
    if not (user and password):
        print("EMAIL_USER / EMAIL_APP_PASSWORD not set -> skipping email")
        return 0

    summary = json.loads((OUTPUT_DIR / "latest_summary.json").read_text())
    history = pd.read_csv(HISTORY_FILE)

    server, repo = os.getenv("GITHUB_SERVER_URL"), os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if server and repo and run_id else ""
    history_url = f"{server}/{repo}/blob/main/data/history/run_history.csv" if server and repo else ""

    msg = build_message(summary, history, user, to, run_url, history_url)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(user, password)
        s.send_message(msg)
    print(f"Email sent to {to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
