-- ============================================================
--  02 — Sales Performance Queries
--  Use with: PostgreSQL / SQLite (via DBeaver, pgAdmin, etc.)
-- ============================================================

-- ── 1. Monthly Revenue Overview ───────────────────────────
SELECT
    DATE_TRUNC('month', o.order_date)  AS month,
    COUNT(DISTINCT o.order_id)         AS total_orders,
    COUNT(DISTINCT o.customer_id)      AS unique_customers,
    ROUND(SUM(oi.line_total), 2)       AS gross_revenue,
    ROUND(SUM(oi.cost_total), 2)       AS total_cost,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS gross_profit,
    ROUND(AVG(oi.line_total / NULLIF(oi.quantity, 0)), 2) AS avg_item_value,
    ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY 1
ORDER BY 1;

-- ── 2. Revenue by Category ────────────────────────────────
SELECT
    p.category,
    COUNT(DISTINCT o.order_id)   AS orders,
    SUM(oi.quantity)             AS units_sold,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
    ROUND(SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct
FROM order_items oi
JOIN orders o    ON oi.order_id   = o.order_id
JOIN products p  ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY p.category
ORDER BY revenue DESC;

-- ── 3. Top 20 Products by Revenue ────────────────────────
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity)             AS units_sold,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
    ROUND(AVG(p.rating), 1)      AS avg_rating
FROM order_items oi
JOIN orders o   ON oi.order_id   = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 20;

-- ── 4. Revenue by Region ──────────────────────────────────
SELECT
    c.region,
    COUNT(DISTINCT o.order_id)   AS orders,
    COUNT(DISTINCT c.customer_id) AS customers,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(SUM(oi.line_total) / COUNT(DISTINCT o.order_id), 2) AS aov
FROM orders o
JOIN customers c  ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id  = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY c.region
ORDER BY revenue DESC;

-- ── 5. Sales by Channel & Segment ────────────────────────
SELECT
    c.acquisition_channel,
    c.segment,
    COUNT(DISTINCT o.order_id)    AS orders,
    ROUND(SUM(oi.line_total), 2)  AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct
FROM orders o
JOIN customers c    ON o.customer_id   = c.customer_id
JOIN order_items oi ON o.order_id      = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY c.acquisition_channel, c.segment
ORDER BY revenue DESC;

-- ── 6. Daily Sales Trend (last 90 days) ──────────────────
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
  AND o.order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY o.order_date
ORDER BY o.order_date;

-- ── 7. Payment Method Analysis ────────────────────────────
SELECT
    payment_method,
    COUNT(*)                     AS transactions,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(AVG(oi.line_total), 2) AS avg_basket
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY payment_method
ORDER BY revenue DESC;

-- ── 8. Order Status Distribution ──────────────────────────
SELECT
    status,
    COUNT(*)              AS orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders
GROUP BY status
ORDER BY orders DESC;

-- ── 9. YoY Revenue Comparison ─────────────────────────────
SELECT
    EXTRACT(YEAR FROM o.order_date)  AS year,
    EXTRACT(MONTH FROM o.order_date) AS month,
    ROUND(SUM(oi.line_total), 2)     AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY 1, 2
ORDER BY 1, 2;

-- ── 10. KPI Summary View ──────────────────────────────────
SELECT
    ROUND(SUM(oi.line_total), 2)                  AS total_revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2)  AS total_profit,
    ROUND(SUM(oi.line_total - oi.cost_total)
        / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS overall_margin_pct,
    COUNT(DISTINCT o.order_id)                     AS total_orders,
    COUNT(DISTINCT o.customer_id)                  AS total_customers,
    ROUND(AVG(order_vals.order_total), 2)          AS avg_order_value,
    ROUND(SUM(oi.line_total)
        / NULLIF(COUNT(DISTINCT o.customer_id), 0), 2) AS revenue_per_customer
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN (
    SELECT order_id, SUM(line_total) AS order_total
    FROM order_items GROUP BY order_id
) order_vals ON o.order_id = order_vals.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned');
