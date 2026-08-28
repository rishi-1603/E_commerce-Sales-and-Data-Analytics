-- ============================================================
--  03_kpi_analysis.sql
--  E-Commerce Analytics — Executive KPIs & Growth
--
--  The numbers a leadership review actually opens with.
--  All revenue/profit figures use the valid_orders rule
--  (Delivered + Processing only).
-- ============================================================

-- ── 1. Company-level KPI summary ──────────────────────────
-- Business Question: What is the state of the business overall?
-- Why It Matters:   These six numbers anchor every review:
--                   revenue, profit, margin, orders, customers,
--                   and average order value.
-- Key Insight:      One row = the business health snapshot.
WITH revenue_orders AS (
    SELECT o.order_id, o.customer_id, o.order_date
    FROM orders o
    WHERE o.status NOT IN ('Cancelled', 'Returned')
),
order_totals AS (
    SELECT order_id, SUM(line_total) AS order_total,
           SUM(line_total - cost_total) AS order_profit
    FROM order_items
    GROUP BY order_id
)
SELECT
    ROUND(SUM(ot.order_total), 2)                       AS total_revenue,
    ROUND(SUM(ot.order_profit), 2)                      AS total_profit,
    ROUND(SUM(ot.order_profit) / NULLIF(SUM(ot.order_total),0) * 100, 2)
                                                        AS gross_margin_pct,
    COUNT(DISTINCT ro.order_id)                         AS total_orders,
    COUNT(DISTINCT ro.customer_id)                      AS total_customers,
    ROUND(AVG(ot.order_total), 2)                       AS avg_order_value,
    ROUND(SUM(ot.order_total) / NULLIF(COUNT(DISTINCT ro.customer_id),0), 2)
                                                        AS revenue_per_customer
FROM revenue_orders ro
JOIN order_totals ot ON ro.order_id = ot.order_id;

-- ── 2. Monthly KPI trend with MoM growth (LAG window) ─────
-- Business Question: Is revenue growing or shrinking month over month?
-- Why It Matters:   MoM growth is the earliest warning signal —
--                   it turns before quarterly results do.
-- Key Insight:      revenue_mom_growth_pct flags exactly which
--                   months turned negative, separating trend
--                   from noise.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', o.order_date) AS month,
        COUNT(DISTINCT o.order_id)        AS orders,
        COUNT(DISTINCT o.customer_id)     AS active_customers,
        SUM(oi.line_total)                AS revenue,
        SUM(oi.line_total - oi.cost_total) AS profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY 1
)
SELECT
    TO_CHAR(month, 'YYYY-MM')                          AS month,
    orders,
    active_customers,
    ROUND(revenue, 2)                                   AS revenue,
    ROUND(profit, 2)                                    AS profit,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2)
                                                        AS revenue_change,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
          / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 1)
                                                        AS revenue_mom_growth_pct
FROM monthly
ORDER BY month;

-- ── 3. Year-over-year comparison ──────────────────────────
-- Business Question: How does each year compare to the last?
-- Why It Matters:   Seasonality makes month-to-month reads noisy;
--                   YoY is the fair comparison retailers use.
-- Key Insight:      yoy_growth_pct shows annual trajectory and
--                   whether growth is accelerating or fading.
WITH yearly AS (
    SELECT
        EXTRACT(YEAR FROM o.order_date) AS yr,
        SUM(oi.line_total)              AS revenue,
        SUM(oi.line_total - oi.cost_total) AS profit,
        COUNT(DISTINCT o.order_id)      AS orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY 1
)
SELECT
    yr,
    orders,
    ROUND(revenue, 2)                                        AS revenue,
    ROUND(profit, 2)                                         AS profit,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY yr), 2)      AS revenue_change,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY yr))
          / NULLIF(LAG(revenue) OVER (ORDER BY yr), 0) * 100, 1) AS yoy_growth_pct
FROM yearly
ORDER BY yr;

-- ── 4. AOV trend (are baskets getting bigger?) ────────────
-- Business Question: Is average order value improving over time?
-- Why It Matters:   Revenue = orders × AOV. Knowing which lever
--                   moved tells marketing whether to chase
--                   traffic or basket size.
-- Key Insight:      Direction of AOV per month — rising AOV with
--                   flat orders means upsell/cross-sell is working.
WITH monthly AS (
    SELECT DATE_TRUNC('month', o.order_date) AS month,
           SUM(oi.line_total)                AS revenue,
           COUNT(DISTINCT o.order_id)        AS orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY 1
)
SELECT
    TO_CHAR(month, 'YYYY-MM')                            AS month,
    ROUND(revenue / NULLIF(orders, 0), 2)                AS avg_order_value,
    ROUND((revenue / NULLIF(orders,0))
          - LAG(revenue / NULLIF(orders,0)) OVER (ORDER BY month), 2) AS aov_change
FROM monthly
ORDER BY month;

-- ── 5. Revenue concentration — Pareto check ───────────────
-- Business Question: How dependent is revenue on few customers?
-- Why It Matters:   If a small share of customers drives most
--                   revenue, retention of that group becomes a
--                   risk-management question, not a marketing one.
-- Key Insight:      The share of total revenue held by the top
--                   10% of customers.
WITH customer_spend AS (
    SELECT o.customer_id,
           SUM(oi.line_total) AS spend
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY 1
),
ranked AS (
    SELECT customer_id, spend,
           NTILE(10) OVER (ORDER BY spend DESC) AS spend_decile
    FROM customer_spend
)
SELECT
    spend_decile,
    COUNT(*)                                   AS customers,
    ROUND(SUM(spend), 2)                       AS revenue,
    ROUND(SUM(spend) * 100.0 / SUM(SUM(spend)) OVER (), 2) AS pct_of_revenue
FROM ranked
GROUP BY spend_decile
ORDER BY spend_decile;
