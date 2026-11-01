"""End-to-end: Extract -> Transform -> Load -> Validate."""
import logging
import sys

from config import BASE_DIR, DB_PATH
from etl.extract import extract
from etl.transform import transform
from etl.load import load
import run_validation

log = logging.getLogger("pipeline")


def main():
    raw_dir = BASE_DIR / "data" / "raw"
    log.info("=== ETL start ===")
    data = extract(raw_dir)
    tables = transform(data)
    load(tables, DB_PATH)
    log.info("=== ETL done, starting validation ===")
    return run_validation.main()      # 0 pass, 1 issues found, 2 setup error


if __name__ == "__main__":
    sys.exit(main())
