-- ============================================================
--  07_regional_analysis.sql
--  E-Commerce Analytics — Regional & Channel Performance
--
--  Where the business works geographically, and whether
--  performance gaps are real or just population differences.
-- ============================================================

-- ── 1. Revenue by region ──────────────────────────────────
-- Business Question: Which regions generate revenue?
-- Why It Matters:   Logistics, marketing and expansion decisions
--                   are regional — totals hide local failure.
-- Key Insight:      Revenue, orders, customers and AOV per region
--                   — identifies underperforming territories.
SELECT
    c.region,
    COUNT(DISTINCT c.customer_id)   AS customers,
    COUNT(DISTINCT o.order_id)      AS orders,
    ROUND(SUM(oi.line_total), 2)    AS revenue,
    ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_order_value
FROM orders o
JOIN customers c   ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id  = oi.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY c.region
ORDER BY revenue DESC;

-- ── 2. Regional revenue per customer (fair comparison) ────
-- Business Question: Is the "best" region best because it is big,
--                    or because customers there spend more?
-- Why It Matters:   Raw revenue favours populous regions;
--                   per-customer revenue reveals true quality.
-- Key Insight:      Ranks regions by value per customer — often
--                   reorders the raw revenue table.
WITH region_agg AS (
    SELECT
        c.region,
        COUNT(DISTINCT c.customer_id) AS customers,
        SUM(oi.line_total)            AS revenue
    FROM orders o
    JOIN customers c   ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id  = oi.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY c.region
)
SELECT
    region,
    customers,
    ROUND(revenue, 2)                          AS revenue,
    ROUND(revenue / NULLIF(customers, 0), 2)   AS revenue_per_customer,
    RANK()     OVER (ORDER BY revenue DESC)    AS rank_by_revenue,
    RANK()     OVER (ORDER BY revenue / NULLIF(customers, 0) DESC) AS rank_by_value_per_customer
FROM region_agg
ORDER BY rank_by_value_per_customer;

-- ── 3. Region × category — local tastes ───────────────────
-- Business Question: Do categories sell differently by region?
-- Why It Matters:   Regional merchandising and inventory
--                   placement follow this grid.
-- Key Insight:      Category mix per region — any strong local
--                   preference sticks out immediately.
SELECT
    c.region,
    p.category,
    ROUND(SUM(oi.line_total), 2) AS revenue
FROM orders o
JOIN customers c   ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id  = oi.order_id
JOIN products p    ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY c.region, p.category
ORDER BY c.region, revenue DESC;

-- ── 4. Regional YoY growth (LAG window) ───────────────────
-- Business Question: Which regions are growing and which are fading?
-- Why It Matters:   Expansion and support decisions need
--                   direction, not just size.
-- Key Insight:      YoY growth per region — a shrinking region
--                   with high revenue is the early warning.
WITH region_year AS (
    SELECT
        c.region,
        EXTRACT(YEAR FROM o.order_date) AS yr,
        SUM(oi.line_total)              AS revenue
    FROM orders o
    JOIN customers c   ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id  = oi.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY 1, 2
)
SELECT
    region, yr,
    ROUND(revenue, 2) AS revenue,
    ROUND((revenue - LAG(revenue) OVER (PARTITION BY region ORDER BY yr))
          / NULLIF(LAG(revenue) OVER (PARTITION BY region ORDER BY yr), 0) * 100, 1)
          AS yoy_growth_pct
FROM region_year
ORDER BY region, yr;

-- ── 5. Channel performance by region ──────────────────────
-- Business Question: Do acquisition channels work differently
--                    by region?
-- Why It Matters:   Channel spend is allocated regionally in
--                   most organisations — the interaction matters.
-- Key Insight:      Channel × region revenue grid; strong cells
--                   indicate where to concentrate spend.
SELECT
    c.region,
    c.acquisition_channel,
    COUNT(DISTINCT o.order_id)   AS orders,
    ROUND(SUM(oi.line_total), 2) AS revenue
FROM orders o
JOIN customers c   ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id  = oi.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY c.region, c.acquisition_channel
ORDER BY c.region, revenue DESC;
