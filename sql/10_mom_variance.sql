-- ============================================================
--  10_mom_variance.sql
--  E-Commerce Analytics — Month-over-Month Variance Engine
--
--  Purpose : The "What changed?" engine. Monthly revenue,
--            orders, active customers and AOV with previous-
--            period values and deltas via LAG — the exact
--            numbers the dashboard's MoM chip row displays.
--
--  Convention (test-pinned): revenue = SUM(line_total) across
--  ALL order statuses (matches DATA.monthly_revenue and
--  tests/test_dashboard_consistency.py).
--
--  Verified (Python: scripts/decision_layer.py):
--    2024-11 -> 2024-12: revenue +17.0%, orders +21.3%,
--    active customers +8.2%, AOV -3.5%.
--    Decision: growth is order-volume-led, not price-led.
-- ============================================================

-- ── 1. Monthly KPIs with MoM deltas ────────────────────────
-- Business Question: Is this month's movement volume-led,
--                    price-led, or customer-led?
-- Why It Matters:   The same revenue growth can mean three
--                   different things operationally.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', o.order_date)                        AS month,
        SUM(oi.line_total)                                       AS revenue,
        COUNT(DISTINCT o.order_id)                               AS orders,
        COUNT(DISTINCT o.customer_id)                            AS active_customers
    FROM orders o
    JOIN order_items oi USING (order_id)
    GROUP BY 1
),
with_prev AS (
    SELECT
        month,
        revenue, orders, active_customers,
        revenue / NULLIF(orders, 0)                              AS aov,
        LAG(revenue)          OVER (ORDER BY month)              AS prev_revenue,
        LAG(orders)           OVER (ORDER BY month)              AS prev_orders,
        LAG(active_customers) OVER (ORDER BY month)              AS prev_active_customers,
        LAG(revenue / NULLIF(orders, 0)) OVER (ORDER BY month)   AS prev_aov
    FROM monthly
)
SELECT
    TO_CHAR(month, 'YYYY-MM')                                            AS month,
    ROUND(revenue)                                                       AS revenue,
    ROUND(100.0 * (revenue - prev_revenue) / prev_revenue, 1)            AS revenue_mom_pct,
    orders,
    ROUND(100.0 * (orders - prev_orders) / prev_orders, 1)               AS orders_mom_pct,
    active_customers,
    ROUND(100.0 * (active_customers - prev_active_customers)
          / prev_active_customers, 1)                                    AS active_mom_pct,
    ROUND(aov)                                                           AS aov,
    ROUND(100.0 * (aov - prev_aov) / prev_aov, 1)                        AS aov_mom_pct
FROM with_prev
ORDER BY month;

-- ── 2. Alert-grade months only ─────────────────────────────
-- Business Question: Which months moved enough to explain?
-- Why It Matters:   A ±10% relative move is the dashboard's
--                   alert threshold — these are the months a
--                   reviewer should be able to explain.
WITH monthly AS (
    SELECT DATE_TRUNC('month', o.order_date) AS month,
           SUM(oi.line_total)                AS revenue
    FROM orders o JOIN order_items oi USING (order_id)
    GROUP BY 1
), deltas AS (
    SELECT month, revenue,
           LAG(revenue) OVER (ORDER BY month) AS prev_revenue
    FROM monthly
)
SELECT TO_CHAR(month, 'YYYY-MM') AS month,
       ROUND(revenue)            AS revenue,
       ROUND(100.0 * (revenue - prev_revenue) / prev_revenue, 1) AS mom_pct,
       CASE WHEN (revenue - prev_revenue) / prev_revenue >= 0.10 THEN 'ALERT up'
            WHEN (revenue - prev_revenue) / prev_revenue <= -0.10 THEN 'ALERT down'
            ELSE 'normal' END    AS status
FROM deltas
WHERE prev_revenue IS NOT NULL
ORDER BY month;
