"""Simulates NEW data arriving from the source systems.
Appends fresh rows (with ~20% realistic errors) to the raw CSV files.
In real life this step is replaced by a DB pull / API call / file drop."""
import random
from datetime import datetime

import pandas as pd

from config import BASE_DIR

RAW = BASE_DIR / "data" / "raw"
ROWS_PER_RUN = 20


def add_new_data(raw_dir=RAW, n=ROWS_PER_RUN, seed=None):
    rng = random.Random(seed)
    pay = pd.read_csv(raw_dir / "sap_payments.csv", dtype=str)
    bank = pd.read_csv(raw_dir / "bank_statement.csv", dtype=str)
    cust = pd.read_csv(raw_dir / "customers.csv", dtype=str)
    agr = pd.read_csv(raw_dir / "agreements.csv", dtype=str)

    norm = lambda s: s.str.strip().str.upper()
    pct = dict(zip(norm(agr["customer_id"]), agr["rebate_pct"].astype(float)))
    country = dict(zip(norm(cust["customer_id"]), cust["country"]))
    ccy = {"IN": "INR", "US": "USD", "DE": "EUR", "UK": "GBP", "AE": "AED"}

    next_pid = int(pd.to_numeric(pay["payment_id"]).max()) + 1
    next_inv = int(pay["invoice_id"].str.extract(r"(\d+)")[0].dropna().astype(int).max()) + 1
    today = datetime.now().strftime("%Y-%m-%d")

    new_pay, new_bank = [], []
    for i in range(n):
        cid = rng.choice(list(pct))
        c = country[cid]
        sales = round(rng.uniform(10_000, 500_000), 2)
        amount = round(sales * pct[cid] / 100, 2)
        inv = f"INV{next_inv + i}"
        row = {"payment_id": next_pid, "invoice_id": inv, "customer_id": cid,
               "country": c, "currency": ccy[c], "sales": sales,
               "rebate_pct": pct[cid], "amount": amount,
               "payment_date": today, "status": "PAID"}
        bank_amt, add_bank, dup = amount, True, False

        r = rng.random()                       # inject errors in ~19% of rows
        if r < 0.03:   row["amount"] = round(amount * 1.1, 2)      # wrong calculation
        elif r < 0.06: add_bank = False                            # missing in bank
        elif r < 0.09: bank_amt = round(amount - 50, 2)            # bank variance
        elif r < 0.11: row["customer_id"] = "C999"                 # orphan customer
        elif r < 0.13: row["amount"] = -abs(amount)                # negative amount
        elif r < 0.15: row["currency"] = "JPY"                     # wrong currency
        elif r < 0.17: row["payment_date"] = "31-13-2025"          # invalid date
        elif r < 0.19: dup = True                                  # duplicate invoice

        new_pay.append(row)
        next_pid += 1
        if dup:
            new_pay.append({**row, "payment_id": next_pid})
            next_pid += 1
        if add_bank:
            new_bank.append({"invoice_id": inv, "amount": bank_amt, "bank_date": today})

    pay = pd.concat([pay, pd.DataFrame(new_pay).astype(str)], ignore_index=True)
    bank = pd.concat([bank, pd.DataFrame(new_bank).astype(str)], ignore_index=True)
    pay.to_csv(raw_dir / "sap_payments.csv", index=False)
    bank.to_csv(raw_dir / "bank_statement.csv", index=False)
    print(f"Added {len(new_pay)} payments, {len(new_bank)} bank rows "
          f"(total now: {len(pay)} payments, {len(bank)} bank rows)")
    return len(new_pay), len(new_bank)


if __name__ == "__main__":
    add_new_data()
