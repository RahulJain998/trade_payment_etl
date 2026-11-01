-- Each block starts with "-- name: <check name> | <severity>"

-- name: Duplicate invoices | HIGH
SELECT p.*
FROM trade_payments p
JOIN (SELECT invoice_id FROM trade_payments
      GROUP BY invoice_id HAVING COUNT(*) > 1) d
  ON p.invoice_id = d.invoice_id
ORDER BY p.invoice_id;

-- name: Missing mandatory fields | HIGH
SELECT * FROM trade_payments
WHERE customer_id IS NULL OR amount IS NULL
   OR invoice_id IS NULL OR payment_date IS NULL;

-- name: Zero or negative amount | HIGH
SELECT * FROM trade_payments WHERE amount <= 0;

-- name: Orphan customer not in master | HIGH
SELECT p.*
FROM trade_payments p
LEFT JOIN customers c ON p.customer_id = c.customer_id
WHERE p.customer_id IS NOT NULL AND c.customer_id IS NULL;

-- name: Missing in bank statement | HIGH
SELECT p.*
FROM trade_payments p
LEFT JOIN bank_statement b ON p.invoice_id = b.invoice_id
WHERE b.invoice_id IS NULL AND p.status = 'PAID';

-- name: SAP vs Bank amount variance | HIGH
SELECT p.payment_id, p.invoice_id, p.customer_id, p.amount AS sap_amount,
       b.amount AS bank_amount,
       ROUND(p.amount - b.amount, 2) AS variance
FROM trade_payments p
JOIN bank_statement b ON p.invoice_id = b.invoice_id
WHERE ABS(p.amount - b.amount) > 0.01;
