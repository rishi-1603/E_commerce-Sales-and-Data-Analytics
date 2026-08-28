-- ============================================================
--  02_data_cleaning.sql
--  E-Commerce Analytics — Data Quality Audit & Cleaning Rules
--
--  These queries are the SQL mirror of tests/test_data_quality.py
--  (31 pytest checks). Data quality is not a checkbox here —
--  every downstream KPI depends on it.
--
--  Business rule used across the whole project:
--    Revenue/profit metrics count only Delivered + Processing
--    orders (Cancelled & Returned are excluded).
-- ============================================================

-- ── 1. Duplicate primary keys ─────────────────────────────
-- Business Question: Is any entity accidentally loaded twice?
-- Why It Matters:   Duplicate keys double-count revenue and
--                   silently corrupt every KPI downstream.
-- Key Insight:      Returns the count of duplicated keys per
--                   table — anything above 0 must be resolved
--                   before any analysis is trusted.
SELECT 'customers'  AS table_name, COUNT(*) - COUNT(DISTINCT customer_id) AS duplicate_rows FROM customers
UNION ALL
SELECT 'products',   COUNT(*) - COUNT(DISTINCT product_id)  FROM products
UNION ALL
SELECT 'orders',     COUNT(*) - COUNT(DISTINCT order_id)    FROM orders
UNION ALL
SELECT 'order_items',COUNT(*) - COUNT(DISTINCT item_id)     FROM order_items;

-- ── 2. Orphaned foreign keys ──────────────────────────────
-- Business Question: Do all orders/items reference real parents?
-- Why It Matters:   Orphan rows break joins and understate or
--                   crash aggregated metrics.
-- Key Insight:      Counts of orphaned orders (no customer) and
--                   orphaned items (no order / no product).
SELECT
    (SELECT COUNT(*) FROM orders o
      LEFT JOIN customers c ON o.customer_id = c.customer_id
      WHERE c.customer_id IS NULL)                 AS orphaned_orders,
    (SELECT COUNT(*) FROM order_items oi
      LEFT JOIN orders o ON oi.order_id = o.order_id
      WHERE o.order_id IS NULL)                    AS orphaned_items_no_order,
    (SELECT COUNT(*) FROM order_items oi
      LEFT JOIN products p ON oi.product_id = p.product_id
      WHERE p.product_id IS NULL)                  AS orphaned_items_no_product;

-- ── 3. Impossible values ──────────────────────────────────
-- Business Question: Are there negative amounts or invalid statuses?
-- Why It Matters:   A single negative line_total distorts sums;
--                   unknown statuses leak into metrics.
-- Key Insight:      Row counts violating each business rule —
--                   all should be 0.
SELECT
    SUM(CASE WHEN oi.line_total  <= 0 THEN 1 ELSE 0 END) AS nonpositive_line_totals,
    SUM(CASE WHEN oi.cost_total  <  0 THEN 1 ELSE 0 END) AS negative_cost_totals,
    SUM(CASE WHEN oi.quantity    <= 0 THEN 1 ELSE 0 END) AS nonpositive_quantities,
    SUM(CASE WHEN p.selling_price <= 0 THEN 1 ELSE 0 END) AS nonpositive_prices
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id;

SELECT status, COUNT(*) AS orders
FROM orders
GROUP BY status
ORDER BY orders DESC;
-- Expect exactly: Delivered, Returned, Cancelled, Processing.

-- ── 4. Arithmetic integrity of line totals ────────────────
-- Business Question: Does final_price × quantity equal line_total?
-- Why It Matters:   If the money columns disagree, margin is
--                   fiction — this is the cheapest audit with
--                   the highest payoff.
-- Key Insight:      Number of rows where the identity breaks by
--                   more than a 1-unit rounding tolerance.
SELECT COUNT(*) AS broken_line_math
FROM order_items
WHERE ABS(final_price * quantity - line_total) > 0.01;

-- ── 5. Timeline sanity ────────────────────────────────────
-- Business Question: Did any order pre-date the customer's registration?
-- Why It Matters:   Time-travelling orders indicate a broken ETL
--                   or joined keys from different loads.
-- Key Insight:      Count of orders placed before registration —
--                   expected 0 by construction of the pipeline.
SELECT COUNT(*) AS orders_before_registration
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date < c.registration_date;

-- ── 6. The canonical cleaning decision, as a view ─────────
-- Business Question: Which orders count toward revenue?
-- Why It Matters:   One rule, applied identically in SQL, Python
--                   and the dashboard — so every tool reports
--                   the same numbers.
-- Key Insight:      valid_orders is the single source of truth
--                   for revenue/profit across all scripts.
-- (View created in 01_database_schema.sql; re-created here for
--  standalone use of this file.)
CREATE OR REPLACE VIEW valid_orders AS
SELECT o.*
FROM orders o
WHERE o.status NOT IN ('Cancelled', 'Returned');

-- ── 7. Before/after cleaning row counts ───────────────────
-- Business Question: How much data does the business rule remove?
-- Why It Matters:   Quantifies the gap between "orders placed"
--                   and "revenue-earning orders" — analysts must
--                   always know which one they are reporting.
-- Key Insight:      The share of orders excluded from revenue
--                   metrics (Cancelled + Returned).
SELECT
    COUNT(*)                                             AS all_orders,
    COUNT(*) FILTER (WHERE status IN ('Cancelled','Returned')) AS excluded_orders,
    ROUND(COUNT(*) FILTER (WHERE status IN ('Cancelled','Returned')) * 100.0
          / NULLIF(COUNT(*), 0), 2)                      AS pct_excluded,
    COUNT(*) FILTER (WHERE status NOT IN ('Cancelled','Returned')) AS revenue_orders
FROM orders;
