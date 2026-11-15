-- ============================================================
--  11_order_funnel.sql
--  E-Commerce Analytics — Order-Status Funnel
--
--  Purpose : Where do orders leave between placed and delivered?
--            The operational-leak view.
--
--  Definitions (data/metrics.json):
--    placed    = every order row (raw orders.csv, 12,000)
--    delivered = status Delivered
--    exits     = Cancelled (never shipped), Processing (still open
--                at snapshot), Returned (unwound after delivery)
--
--  Statuses are MUTUALLY EXCLUSIVE, so 'Returned' is its own exit —
--  it is NOT subtracted from 'Delivered'. Earlier versions used a
--  non-mutually-exclusive 'kept' subtraction; that logic has been removed.
--
--  Verified (Python: scripts/decision_layer.py, raw orders):
--    12,000 placed -> 9,312 delivered (77.6%).
--    Exits: 844 cancelled (7.0%), 621 processing (5.2%),
--           1,223 returned (10.2%).
--    Cancelled + Returned = 17.2% of placed; Processing = 5.2%.
--    Decision: the 1,223 returns are a revenue-quality problem
--    worth a root-cause pass (return reasons by category).
-- ============================================================

-- ── 1. Funnel stages ─────────────────────────────────────────
-- Business Question: Of everything customers placed, how much
--                    did we actually deliver?
WITH status_counts AS (
    SELECT status, COUNT(*) AS n FROM orders GROUP BY status
), funnel AS (
    SELECT
        (SELECT SUM(n) FROM status_counts)                                     AS placed,
        (SELECT n FROM status_counts WHERE status = 'Delivered')               AS delivered
)
SELECT
    placed,
    delivered,
    ROUND(100.0 * delivered / placed, 1)          AS delivery_rate_pct
FROM funnel;

-- ── 2. Funnel exits, ranked ──────────────────────────────────
-- Business Question: Which exit drains the funnel most?
SELECT status          AS exit_reason,
       COUNT(*)        AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_placed
FROM orders
WHERE status IN ('Cancelled', 'Processing', 'Returned')
GROUP BY status
ORDER BY orders DESC;

-- ── 3. Returned revenue at risk, by category ─────────────────
-- Business Question: When an order is returned, which
--                    categories lose the most revenue?
-- Why It Matters:   Sizes the root-cause investigation.
SELECT p.category,
       COUNT(DISTINCT o.order_id)                          AS returned_orders,
       ROUND(SUM(oi.line_total))                           AS returned_revenue
FROM orders o
JOIN order_items oi USING (order_id)
JOIN products p USING (product_id)
WHERE o.status = 'Returned'
GROUP BY p.category
ORDER BY returned_revenue DESC;
