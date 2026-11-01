import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
import validators as v


def test_calculation_detects_wrong_amount():
    df = pd.DataFrame({"sales": [1000, 1000], "rebate_pct": [5, 5], "amount": [50, 60]})
    out = v.check_calculation(df)
    assert len(out) == 1 and out.iloc[0]["amount"] == 60


def test_agreement_mismatch():
    p = pd.DataFrame({"customer_id": ["C1"], "rebate_pct": [7]})
    a = pd.DataFrame({"customer_id": ["C1"], "rebate_pct": [5]})
    assert len(v.check_agreement(p, a)) == 1


def test_dates_invalid_and_future():
    df = pd.DataFrame({"payment_date": ["2024-01-01", "31-13-2025", "2999-01-01"]})
    assert set(v.check_dates(df)["reason"]) == {"Invalid date", "Future date"}


def test_currency():
    df = pd.DataFrame({"country": ["IN", "US"], "currency": ["INR", "JPY"]})
    assert len(v.check_currency(df)) == 1


def test_usd_conversion():
    df = pd.DataFrame({"currency": ["INR"], "amount": [1000.0]})
    fx = pd.DataFrame({"currency": ["INR"], "rate_to_usd": [0.012]})
    assert v.add_usd(df, fx).iloc[0]["amount_usd"] == 12.0


def test_transform_cleans_ids_and_keeps_bad_dates():
    from etl.transform import transform
    raw = {
        "payments": pd.DataFrame({
            "payment_id": ["1"], "invoice_id": [" inv1 "], "customer_id": [" c001 "],
            "country": ["in"], "currency": ["inr"], "sales": ["1000"],
            "rebate_pct": ["5"], "amount": ["50"], "payment_date": ["31-13-2025"],
            "status": ["paid"]}),
        "customers": pd.DataFrame({"customer_id": [" c001 "]}),
        "agreements": pd.DataFrame({"customer_id": ["c001"], "rebate_pct": ["5"]}),
        "bank": pd.DataFrame({"invoice_id": ["inv1"], "amount": ["50"]}),
        "fx": pd.DataFrame({"currency": ["inr"], "rate_to_usd": ["0.012"]}),
    }
    out = transform(raw)["trade_payments"].iloc[0]
    assert out["customer_id"] == "C001" and out["invoice_id"] == "INV1"
    assert out["payment_date"] == "31-13-2025"      # bad date preserved for validation
    assert out["amount"] == 50
