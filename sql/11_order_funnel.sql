-- ============================================================
--  11_order_funnel.sql
--  E-Commerce Analytics — Order-Status Funnel
--
--  Purpose : Where do orders leave between placed, delivered
--            and kept? The operational-leak view.
--
--  Definitions (data/metrics.json):
--    placed   = every order row (raw orders.csv, 12,000)
--    delivered= status Delivered
--    kept     = delivered - returned (a return unwinds a sale)
--    exits    = Cancelled (never shipped journey),
--               Processing (still open at snapshot),
--               Returned (unwound after delivery)
--
--  Verified (Python: scripts/decision_layer.py, raw orders):
--    12,000 placed -> 9,312 delivered (77.6%) -> 8,089 kept.
--    Exits: 844 cancelled, 621 processing, 1,223 returned.
--    Decision: the 1,223 returns are a revenue-quality problem
--    worth a root-cause pass (return reasons by category).
-- ============================================================

-- ── 1. Funnel stages ───────────────────────────────────────
-- Business Question: Of everything customers placed, how much
--                    did we actually keep?
WITH status_counts AS (
    SELECT status, COUNT(*) AS n FROM orders GROUP BY status
), funnel AS (
    SELECT
        (SELECT SUM(n) FROM status_counts)                                     AS placed,
        (SELECT n FROM status_counts WHERE status = 'Delivered')               AS delivered,
        (SELECT COALESCE((SELECT n FROM status_counts WHERE status = 'Delivered'), 0)
              - COALESCE((SELECT n FROM status_counts WHERE status = 'Returned'), 0)) AS kept
)
SELECT
    placed,
    delivered,
    kept,
    ROUND(100.0 * delivered / placed, 1)          AS delivery_rate_pct,
    ROUND(100.0 * kept    / delivered, 1)         AS keep_rate_pct,
    ROUND(100.0 * kept    / placed, 1)            AS end_to_end_pct
FROM funnel;

-- ── 2. Funnel exits, ranked ────────────────────────────────
-- Business Question: Which exit drains the funnel most?
SELECT status          AS exit_reason,
       COUNT(*)        AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_placed
FROM orders
WHERE status IN ('Cancelled', 'Processing', 'Returned')
GROUP BY status
ORDER BY orders DESC;

-- ── 3. Returned revenue at risk, by category ───────────────
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
