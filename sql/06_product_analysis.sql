-- ============================================================
--  06_product_analysis.sql
--  E-Commerce Analytics — Product Profitability & BCG Matrix
--
--  Which SKUs make money, which destroy it, and where each
--  sits on the volume × margin grid (BCG).
-- ============================================================

-- ── 1. Product profitability matrix ───────────────────────
-- Business Question: What does each SKU actually contribute?
-- Why It Matters:   Catalog decisions (price, stock, delist)
--                   must be made on profit, not revenue.
-- Key Insight:      Full P&L per SKU — revenue, cost, profit,
--                   margin %, plus rank by profit.
WITH product_pnl AS (
    SELECT
        p.product_id, p.product_name, p.category, p.subcategory,
        SUM(oi.quantity)                  AS units_sold,
        SUM(oi.line_total)                AS revenue,
        SUM(oi.cost_total)                AS cost,
        SUM(oi.line_total - oi.cost_total) AS profit
    FROM order_items oi
    JOIN orders o   ON oi.order_id   = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY 1, 2, 3, 4
)
SELECT
    RANK() OVER (ORDER BY profit DESC)     AS profit_rank,
    product_id, product_name, category, subcategory,
    units_sold,
    ROUND(revenue, 2)                       AS revenue,
    ROUND(cost, 2)                          AS cost,
    ROUND(profit, 2)                        AS profit,
    ROUND(profit / NULLIF(revenue, 0) * 100, 2) AS margin_pct
FROM product_pnl
ORDER BY profit_rank;

-- ── 2. Category profitability summary ─────────────────────
-- Business Question: Where is margin concentrated across categories?
-- Why It Matters:   Marketing budgets and buy plans follow
--                   category margin, not category hype.
-- Key Insight:      Margin comparison across the 5 categories —
--                   identifies which category subsidises which.
SELECT
    p.category,
    COUNT(DISTINCT p.product_id)   AS skus,
    SUM(oi.quantity)               AS units_sold,
    ROUND(SUM(oi.line_total), 2)   AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
    ROUND(SUM(oi.line_total - oi.cost_total)
          / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct,
    ROUND(AVG(p.rating), 2)        AS avg_rating
FROM order_items oi
JOIN orders o   ON oi.order_id   = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY p.category
ORDER BY profit DESC;

-- ── 3. BCG matrix (PERCENTILE_CONT window) ────────────────
-- Business Question: Which products are Stars, Cash Cows,
--                    Question Marks or Dogs?
-- Why It Matters:   The BCG lens turns 150 SKUs into four
--                   portfolio decisions: invest, harvest,
--                   evaluate, exit.
-- Key Insight:      Every SKU labelled with its quadrant — the
--                   strategic map behind the dashboard's BCG page.
WITH product_pnl AS (
    SELECT
        p.product_id, p.product_name, p.category,
        SUM(oi.quantity)   AS units_sold,
        SUM(oi.line_total) AS revenue,
        SUM(oi.line_total - oi.cost_total) AS profit
    FROM order_items oi
    JOIN orders o   ON oi.order_id   = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY 1, 2, 3
)
SELECT
    product_id, product_name, category,
    units_sold,
    ROUND(revenue, 2) AS revenue,
    ROUND(profit, 2)  AS profit,
    CASE
        WHEN units_sold > PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY units_sold) OVER ()
         AND profit     > PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY profit)     OVER ()
            THEN '⭐ Star'
        WHEN units_sold > PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY units_sold) OVER ()
            THEN '🐄 Cash Cow'
        WHEN profit     > PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY profit)     OVER ()
            THEN '❓ Question Mark'
        ELSE '🐕 Dog'
    END AS bcg_quadrant
FROM product_pnl
ORDER BY units_sold DESC;

-- ── 4. Bottom 15 products (delist / reprice review) ───────
-- Business Question: Which SKUs are dragging the catalog down?
-- Why It Matters:   Dogs consume shelf space, working capital
--                   and attention — knowing them is the first
--                   step to pruning.
-- Key Insight:      The lowest-profit SKUs with their volumes —
--                   the shortlist for repricing or delisting.
WITH product_pnl AS (
    SELECT
        p.product_id, p.product_name, p.category,
        SUM(oi.quantity)   AS units_sold,
        SUM(oi.line_total) AS revenue,
        SUM(oi.line_total - oi.cost_total) AS profit
    FROM order_items oi
    JOIN orders o   ON oi.order_id   = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY 1, 2, 3
)
SELECT
    DENSE_RANK() OVER (ORDER BY profit ASC) AS worst_rank,
    product_id, product_name, category,
    units_sold,
    ROUND(revenue, 2) AS revenue,
    ROUND(profit, 2)  AS profit,
    ROUND(profit / NULLIF(revenue,0) * 100, 2) AS margin_pct
FROM product_pnl
ORDER BY profit ASC
LIMIT 15;

-- ── 5. Discount impact on margin ──────────────────────────
-- Business Question: What does discounting cost in margin?
-- Why It Matters:   Discounts are the most common margin leak —
--                   this quantifies the leak per band.
-- Key Insight:      Margin by discount band. (On this synthetic
--                   dataset, discounts and outcomes are unrelated —
--                   the method is demonstrated, not a causal claim.)
SELECT
    CASE
        WHEN o.discount_pct = 0  THEN '0% (none)'
        WHEN o.discount_pct <= 5 THEN '1-5%'
        WHEN o.discount_pct <= 10 THEN '6-10%'
        WHEN o.discount_pct <= 15 THEN '11-15%'
        ELSE '16-20%'
    END AS discount_band,
    COUNT(DISTINCT o.order_id)  AS orders,
    SUM(oi.quantity)            AS units,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
    ROUND(SUM(oi.line_total - oi.cost_total)
          / NULLIF(SUM(oi.line_total), 0) * 100, 2) AS margin_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY 1
ORDER BY MIN(o.discount_pct);

-- ── 6. Stock risk — best sellers running low ──────────────
-- Business Question: Are any high-velocity products close to
--                    stocking out?
-- Why It Matters:   A stock-out on a top earner is pure lost
--                   revenue — this joins demand to inventory.
-- Key Insight:      Top sellers ranked against remaining stock;
--                   low stock + high velocity = reorder now.
WITH product_sales AS (
    SELECT
        oi.product_id,
        SUM(oi.quantity)              AS units_sold,
        ROUND(SUM(oi.line_total), 2)  AS revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY 1
)
SELECT
    ps.product_id, p.product_name, p.category,
    ps.units_sold,
    ROUND(ps.revenue, 2) AS revenue,
    p.stock_qty,
    ROUND(ps.units_sold / NULLIF(p.stock_qty, 0), 2) AS sell_through_ratio
FROM product_sales ps
JOIN products p ON ps.product_id = p.product_id
ORDER BY revenue DESC
LIMIT 20;
