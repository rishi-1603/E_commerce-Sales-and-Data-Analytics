-- ============================================================
--  04_sales_analysis.sql
--  E-Commerce Analytics — Sales Performance Deep-Dive
--
--  Where revenue comes from and how it moves: time, category,
--  channel, payment method. Uses window functions for ranking
--  and moving averages.
-- ============================================================

-- ── 1. Monthly revenue, orders & customers ────────────────
-- Business Question: What is the shape of the revenue trend?
-- Why It Matters:   The baseline every other analysis is read
--                   against — growth, seasonality, and scale.
-- Key Insight:      Reveals seasonality and the growth trajectory
--                   (strong upward trend 2022 → 2024 in this data).
SELECT
    DATE_TRUNC('month', o.order_date)  AS month,
    COUNT(DISTINCT o.order_id)         AS total_orders,
    COUNT(DISTINCT o.customer_id)      AS unique_customers,
    ROUND(SUM(oi.line_total), 2)       AS gross_revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS gross_profit,
    ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY 1
ORDER BY 1;

-- ── 2. Revenue & margin by category ───────────────────────
-- Business Question: Which categories earn, and which only sell?
-- Why It Matters:   Revenue without margin is vanity — a category
--                   can be big and still contribute little profit.
-- Key Insight:      Separates categories by margin quality, not
--                   just size — the input for category-level
--                   investment decisions.
SELECT
    p.category,
    COUNT(DISTINCT o.order_id)   AS orders,
    SUM(oi.quantity)             AS units_sold,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
    ROUND(SUM(oi.line_total - oi.cost_total)
          / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct
FROM order_items oi
JOIN orders o   ON oi.order_id   = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY p.category
ORDER BY revenue DESC;

-- ── 3. Top 20 products by revenue, with RANK() ────────────
-- Business Question: Which SKUs are the revenue engines?
-- Why It Matters:   Inventory, marketing and pricing decisions
--                   concentrate on the head of the catalog.
-- Key Insight:      revenue_rank makes the ordering explicit and
--                   gap_to_next shows where revenue cliffs exist.
WITH product_revenue AS (
    SELECT
        p.product_id, p.product_name, p.category,
        SUM(oi.line_total)   AS revenue,
        SUM(oi.quantity)     AS units_sold,
        SUM(oi.line_total - oi.cost_total) AS profit
    FROM order_items oi
    JOIN orders o   ON oi.order_id   = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY 1, 2, 3
)
SELECT
    RANK() OVER (ORDER BY revenue DESC)            AS revenue_rank,
    product_id, product_name, category,
    units_sold,
    ROUND(revenue, 2)                              AS revenue,
    ROUND(profit, 2)                               AS profit,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY revenue DESC), 2) AS gap_to_next
FROM product_revenue
ORDER BY revenue_rank
LIMIT 20;

-- ── 4. Sales by acquisition channel & customer segment ────
-- Business Question: Which channels bring revenue, and at what margin?
-- Why It Matters:   CAC budgets are allocated on this table —
--                   volume without margin can be a trap.
-- Key Insight:      Channel × segment performance grid; on this
--                   (synthetic) data margins are flat across
--                   channels — a real dataset would steer spend.
SELECT
    c.acquisition_channel,
    c.segment,
    COUNT(DISTINCT o.order_id)    AS orders,
    ROUND(SUM(oi.line_total), 2)  AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total)
          / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct
FROM orders o
JOIN customers c    ON o.customer_id   = c.customer_id
JOIN order_items oi ON o.order_id      = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY c.acquisition_channel, c.segment
ORDER BY revenue DESC;

-- ── 5. Daily revenue with 7-day moving average ────────────
-- Business Question: What does the short-term trend look like
--                    once daily noise is smoothed out?
-- Why It Matters:   Daily numbers are too noisy to act on; the
--                   7-day MA is the standard operational view.
-- Key Insight:      The window function separates signal
--                   (moving average) from noise (daily).
SELECT
    o.order_date,
    COUNT(DISTINCT o.order_id)   AS orders,
    ROUND(SUM(oi.line_total), 2) AS daily_revenue,
    ROUND(AVG(SUM(oi.line_total)) OVER (
        ORDER BY o.order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS revenue_7day_ma
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
  AND o.order_date >= (SELECT MAX(order_date) - INTERVAL '90 days' FROM orders)
GROUP BY o.order_date
ORDER BY o.order_date;

-- ── 6. Payment method analysis ────────────────────────────
-- Business Question: How do customers pay, and does method
--                    relate to basket size?
-- Why It Matters:   Payment mix affects processing fees and
--                   failure rates; basket differences inform
--                   payment-promotion decisions.
-- Key Insight:      Transaction counts and average basket per
--                   method.
SELECT
    o.payment_method,
    COUNT(DISTINCT o.order_id)      AS orders,
    ROUND(SUM(oi.line_total), 2)    AS revenue,
    ROUND(SUM(oi.line_total)
          / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_basket
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY o.payment_method
ORDER BY revenue DESC;

-- ── 7. Order status distribution ──────────────────────────
-- Business Question: What share of orders actually completes?
-- Why It Matters:   Fulfilment quality = delivery rate; the
--                   cancelled/returned share is direct leakage.
-- Key Insight:      The completion funnel of all orders placed.
SELECT
    status,
    COUNT(*)              AS orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders
GROUP BY status
ORDER BY orders DESC;

-- ── 8. Month-over-month revenue by category (pivoted view) ─
-- Business Question: Is any category shrinking while the total grows?
-- Why It Matters:   Aggregate growth can hide a dying category;
--                   this exposes category-level momentum.
-- Key Insight:      Category momentum per month — divergence
--                   between categories is visible at a glance.
SELECT
    TO_CHAR(DATE_TRUNC('month', o.order_date), 'YYYY-MM') AS month,
    ROUND(SUM(CASE WHEN p.category = 'Electronics'    THEN oi.line_total END), 0) AS electronics,
    ROUND(SUM(CASE WHEN p.category = 'Clothing'       THEN oi.line_total END), 0) AS clothing,
    ROUND(SUM(CASE WHEN p.category = 'Home & Garden'  THEN oi.line_total END), 0) AS home_garden,
    ROUND(SUM(CASE WHEN p.category = 'Sports'         THEN oi.line_total END), 0) AS sports,
    ROUND(SUM(CASE WHEN p.category = 'Beauty'         THEN oi.line_total END), 0) AS beauty
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY 1
ORDER BY 1;
