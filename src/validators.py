"""Python-side validation rules (business logic awkward to write in SQL)."""
import pandas as pd

from config import AMOUNT_TOLERANCE

COUNTRY_CURRENCY = {"IN": "INR", "US": "USD", "DE": "EUR", "UK": "GBP", "AE": "AED"}


def check_calculation(df: pd.DataFrame) -> pd.DataFrame:
    """amount must equal sales * rebate_pct / 100."""
    d = df.dropna(subset=["sales", "rebate_pct", "amount"]).copy()
    d["expected_amount"] = (d["sales"] * d["rebate_pct"] / 100).round(2)
    d["difference"] = (d["amount"] - d["expected_amount"]).round(2)
    return d[d["difference"].abs() > AMOUNT_TOLERANCE]


def check_agreement(payments: pd.DataFrame, agreements: pd.DataFrame) -> pd.DataFrame:
    """rebate_pct used in the payment must match the contract."""
    m = payments.merge(agreements, on="customer_id", how="inner",
                       suffixes=("", "_agreed"))
    return m[(m["rebate_pct"] - m["rebate_pct_agreed"]).abs() > 1e-9]


def check_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Dates must parse and must not be in the future."""
    parsed = pd.to_datetime(df["payment_date"], errors="coerce", format="%Y-%m-%d")
    today = pd.Timestamp.today().normalize()
    bad = parsed.isna() | (parsed > today)
    out = df[bad].copy()
    out["reason"] = ["Invalid date" if pd.isna(p) else "Future date"
                     for p in parsed[bad]]
    return out


def check_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Currency must be the expected one for the country."""
    expected = df["country"].map(COUNTRY_CURRENCY)
    return df[expected.notna() & (df["currency"] != expected)]


def add_usd(df: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    """Standardise all amounts to USD for global reporting."""
    out = df.merge(fx, on="currency", how="left")
    out["amount_usd"] = (out["amount"] * out["rate_to_usd"]).round(2)
    return out
