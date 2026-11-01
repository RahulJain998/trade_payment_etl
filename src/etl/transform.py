"""TRANSFORM: clean + standardise. Does NOT hide bad business data
(duplicates, wrong amounts etc. must still reach the validation layer)."""
import logging
import pandas as pd

log = logging.getLogger("etl.transform")


def _clean_text(s: pd.Series, upper=True) -> pd.Series:
    s = s.str.strip()
    return s.str.upper() if upper else s


def _normalise_date(s: pd.Series) -> pd.Series:
    """Valid dates -> YYYY-MM-DD. Unparseable values are kept as-is
    so the validation layer can flag them."""
    parsed = pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")
    return parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), s)


def transform(data):
    p = data["payments"].copy()
    for col in ["invoice_id", "customer_id", "country", "currency", "status"]:
        p[col] = _clean_text(p[col])
    for col in ["sales", "rebate_pct", "amount"]:
        p[col] = pd.to_numeric(p[col], errors="coerce")
    p["payment_id"] = pd.to_numeric(p["payment_id"]).astype(int)
    p["payment_date"] = _normalise_date(p["payment_date"])

    c = data["customers"].copy()
    c["customer_id"] = _clean_text(c["customer_id"])

    a = data["agreements"].copy()
    a["customer_id"] = _clean_text(a["customer_id"])
    a["rebate_pct"] = pd.to_numeric(a["rebate_pct"], errors="coerce")

    b = data["bank"].copy()
    b["invoice_id"] = _clean_text(b["invoice_id"])
    b["amount"] = pd.to_numeric(b["amount"], errors="coerce")

    fx = data["fx"].copy()
    fx["currency"] = _clean_text(fx["currency"])
    fx["rate_to_usd"] = pd.to_numeric(fx["rate_to_usd"], errors="coerce")

    log.info("Transformed all tables")
    return {"trade_payments": p, "customers": c, "agreements": a,
            "bank_statement": b, "fx_rates": fx}
