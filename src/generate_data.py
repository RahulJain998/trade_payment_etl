"""Creates a sample SQLite DB with realistic trade payment data
and deliberately injected errors (so the validators have something to catch)."""
import random
import sqlite3
from datetime import date, timedelta

from config import DB_PATH

random.seed(42)

COUNTRIES = {"IN": "INR", "US": "USD", "DE": "EUR", "UK": "GBP", "AE": "AED"}
FX = {"INR": 0.012, "USD": 1.0, "EUR": 1.08, "GBP": 1.27, "AED": 0.272}

SCHEMA = """
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS agreements;
DROP TABLE IF EXISTS trade_payments;
DROP TABLE IF EXISTS bank_statement;
DROP TABLE IF EXISTS fx_rates;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY, name TEXT, country TEXT, channel TEXT);
CREATE TABLE agreements (
    customer_id TEXT, rebate_pct REAL);
CREATE TABLE trade_payments (
    payment_id INTEGER PRIMARY KEY, invoice_id TEXT, customer_id TEXT,
    country TEXT, currency TEXT, sales REAL, rebate_pct REAL,
    amount REAL, payment_date TEXT, status TEXT);
CREATE TABLE bank_statement (
    invoice_id TEXT, amount REAL, bank_date TEXT);
CREATE TABLE fx_rates (currency TEXT PRIMARY KEY, rate_to_usd REAL);
"""


def build(n_customers=40, n_payments=500):
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    customers, agreements = [], {}
    for i in range(1, n_customers + 1):
        cid = f"C{i:03d}"
        country = random.choice(list(COUNTRIES))
        channel = random.choice(["Wholesale", "Retail"])
        customers.append((cid, f"Customer {i}", country, channel))
        agreements[cid] = random.choice([2, 3, 5, 7.5, 10])
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)
    conn.executemany("INSERT INTO agreements VALUES (?,?)", agreements.items())
    conn.executemany("INSERT INTO fx_rates VALUES (?,?)", FX.items())

    cust_country = {c[0]: c[2] for c in customers}
    payments, bank = [], []
    start = date.today() - timedelta(days=90)
    for i in range(1, n_payments + 1):
        cid = random.choice(list(agreements))
        country = cust_country[cid]
        sales = round(random.uniform(10_000, 500_000), 2)
        pct = agreements[cid]
        amount = round(sales * pct / 100, 2)
        inv = f"INV{100000 + i}"
        d = (start + timedelta(days=random.randint(0, 89))).isoformat()
        payments.append([i, inv, cid, country, COUNTRIES[country],
                         sales, pct, amount, d, "PAID"])
        bank.append([inv, amount, d])

    # ---- inject errors ----
    for k in random.sample(range(len(payments)), 5):          # duplicates
        dup = payments[k][:]
        dup[0] = 10_000 + len(payments) + random.randint(1, 999)
        payments.append(dup)
    for k in random.sample(range(len(payments)), 4):          # null customer
        payments[k][2] = None
    for k in random.sample(range(len(payments)), 3):          # null amount
        payments[k][7] = None
    for k in random.sample(range(len(payments)), 3):          # negative amount
        payments[k][7] = -round(payments[k][5] * 0.05, 2)
    for k in random.sample(range(len(payments)), 6):          # wrong calculation
        if payments[k][7] and payments[k][7] > 0:
            payments[k][7] = round(payments[k][7] * 1.1, 2)
    for k in random.sample(range(len(payments)), 5):          # % != agreement
        payments[k][6] = payments[k][6] + 2
    for k in random.sample(range(len(payments)), 3):          # orphan customer
        payments[k][2] = "C999"
    for k in random.sample(range(len(payments)), 3):          # invalid date
        payments[k][8] = "31-13-2025"
    for k in random.sample(range(len(payments)), 2):          # future date
        payments[k][8] = (date.today() + timedelta(days=30)).isoformat()
    for k in random.sample(range(len(payments)), 3):          # wrong currency
        payments[k][4] = "JPY"

    conn.executemany(
        "INSERT INTO trade_payments VALUES (?,?,?,?,?,?,?,?,?,?)", payments)

    for k in random.sample(range(len(bank)), 6):              # bank amount differs
        bank[k][1] = round(bank[k][1] - random.choice([50, 100, 250]), 2)
    for k in sorted(random.sample(range(len(bank)), 5), reverse=True):  # missing
        bank.pop(k)
    conn.executemany("INSERT INTO bank_statement VALUES (?,?,?)", bank)

    conn.commit()
    conn.close()
    print(f"DB ready: {DB_PATH}  ({len(payments)} payments, {len(bank)} bank rows)")


if __name__ == "__main__":
    build()
