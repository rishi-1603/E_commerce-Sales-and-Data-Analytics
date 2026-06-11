-- ============================================================
--  04 — Product Profitability Analysis SQL
-- ============================================================

-- ── 1. Product Profitability Matrix ──────────────────────
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.selling_price,
    p.cost_price,
    ROUND((p.selling_price - p.cost_price) / p.selling_price * 100, 2) AS list_margin_pct,
    SUM(oi.quantity)             AS units_sold,
    ROUND(SUM(oi.line_total), 2) AS total_revenue,
    ROUND(SUM(oi.cost_total), 2) AS total_cost,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS gross_profit,
    ROUND(SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS actual_margin_pct,
    p.rating,
    p.stock_qty
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o       ON oi.order_id  = o.order_id
    AND o.status NOT IN ('Cancelled','Returned')
GROUP BY p.product_id, p.product_name, p.category, p.subcategory,
         p.selling_price, p.cost_price, p.rating, p.stock_qty
ORDER BY gross_profit DESC;

-- ── 2. Category Profitability Summary ────────────────────
SELECT
    p.category,
    COUNT(DISTINCT p.product_id)  AS products,
    SUM(oi.quantity)              AS units_sold,
    ROUND(SUM(oi.line_total), 2)  AS revenue,
    ROUND(SUM(oi.cost_total), 2)  AS cost,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
    ROUND(SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct,
    ROUND(AVG(p.rating), 2)       AS avg_rating
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o       ON oi.order_id  = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY p.category
ORDER BY profit DESC;

-- ── 3. High Margin vs High Volume (BCG-style) ────────────
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct,
    CASE
        WHEN SUM(oi.quantity) > PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY SUM(oi.quantity)) OVER ()
             AND SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) > 0.3
             THEN 'Star'
        WHEN SUM(oi.quantity) > PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY SUM(oi.quantity)) OVER ()
             AND SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) <= 0.3
             THEN 'Cash Cow'
        WHEN SUM(oi.quantity) <= PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY SUM(oi.quantity)) OVER ()
             AND SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) > 0.3
             THEN 'Question Mark'
        ELSE 'Dog'
    END AS product_quadrant
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o       ON oi.order_id  = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY p.product_id, p.product_name, p.category;

-- ── 4. Return Rate by Product ─────────────────────────────
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT CASE WHEN o.status = 'Returned'  THEN o.order_id END) AS returned_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'Delivered' THEN o.order_id END) AS delivered_orders,
    ROUND(COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) * 100.0
        / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS return_rate_pct
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o       ON oi.order_id  = o.order_id
GROUP BY p.product_id, p.product_name, p.category
HAVING COUNT(DISTINCT o.order_id) > 5
ORDER BY return_rate_pct DESC;

-- ── 5. Discount Impact on Margin ─────────────────────────
SELECT
    CASE
        WHEN oi.discount_pct = 0    THEN 'No Discount'
        WHEN oi.discount_pct <= 0.05 THEN '1-5%'
        WHEN oi.discount_pct <= 0.10 THEN '6-10%'
        WHEN oi.discount_pct <= 0.15 THEN '11-15%'
        ELSE '16-20%'
    END AS discount_tier,
    COUNT(DISTINCT o.order_id)   AS orders,
    SUM(oi.quantity)             AS units,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total) / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct,
    ROUND(AVG(oi.line_total / NULLIF(oi.quantity, 0)), 2) AS avg_item_value
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY 1
ORDER BY MIN(oi.discount_pct);
