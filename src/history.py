"""Keeps a permanent log of every run (so old results never disappear)
and writes output/latest_summary.json for the email step."""
import json
import os
from datetime import datetime, timezone

import pandas as pd

from config import HISTORY_FILE, OUTPUT_DIR, now_ist


def append_history(summary: pd.DataFrame, kpi: pd.DataFrame, report_path) -> pd.DataFrame:
    k = dict(zip(kpi["metric"], kpi["value"]))
    row = {
        "run_no": os.getenv("GITHUB_RUN_NUMBER", "local"),
        "run_time_ist": now_ist().strftime("%Y-%m-%d %H:%M:%S"),
        "run_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": int(float(k["Total records"])),
        "records_with_issues": int(float(k["Records with issues"])),
        "data_quality_pct": float(k["Data quality %"]),
        "failed_checks": int((summary["status"] == "FAIL").sum()),
        "total_issues": int(summary["issues_found"].sum()),
        "report_file": os.path.basename(str(report_path)),
    }
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    hist = pd.concat([pd.read_csv(HISTORY_FILE), new], ignore_index=True) \
        if HISTORY_FILE.exists() else new
    hist.to_csv(HISTORY_FILE, index=False)

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "latest_summary.json").write_text(json.dumps({
        "run": row,
        "checks": summary.to_dict(orient="records"),
        "report_path": str(report_path),
    }, indent=2))
    return hist
