-- ============================================================
--  12_discount_margin.sql
--  E-Commerce Analytics — Discount Cost, Margin Erosion & Break-Even
--
--  Purpose : Answer the pricing question the sales dashboard
--            never asks — is the discount we give buying us
--            anything, and what would have to be true for it
--            to be worth giving?
--
--  Conventions (match 01_database_schema.sql):
--    grain           = order line items (order_items)
--    valid orders    = status NOT IN ('Cancelled','Returned')
--    profit          = line_total - cost_total
--    discount_pct    = stored as a FRACTION (0.05 = 5%), matching
--                      data/raw/orders.csv and data/metrics.json.
--                      If your load stores percent units, divide
--                      by 100 in the expressions below.
--
--  Definitions (must match data/metrics.json and
--               python/pricing/elasticity.py):
--    margin_rate        = profit / line_total
--    margin_pct_of_list = margin_rate * (1 - discount_pct)
--    break_even_lift    = (margin_pct_of_list at 0%)
--                         / (margin_pct_of_list at depth) - 1
--
--  Verified pattern (Python: python/pricing/elasticity.py):
--    Measured volume response to discount depth is NOT
--    statistically significant overall (Kruskal-Wallis p=0.305).
--    Break-even needs +10.6% / +23.1% / +38.1% / +59.2% volume at
--    5 / 10 / 15 / 20% discounts. The one significant category
--    (Sports, p=0.003) moves -7.0% — the wrong direction.
--    Decision: treat the discount ladder as a margin policy, not
--    a demand lever, until an experiment says otherwise.
-- ============================================================

-- ── 1. Margin erosion by discount depth ────────────────────
-- Business Question: What does each rung of the discount ladder
--                    cost us in margin?
-- Why It Matters:   The cost side of every promotion decision,
--                   stated at the depth it is granted.
SELECT
    oi.discount_pct,
    COUNT(*)                                                          AS line_items,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)                AS pct_of_items,
    ROUND(AVG((oi.line_total - oi.cost_total) / oi.line_total), 4)    AS margin_rate,
    ROUND(AVG(((oi.line_total - oi.cost_total) / oi.line_total)
              * (1 - oi.discount_pct)), 4)                            AS margin_pct_of_list
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY oi.discount_pct
ORDER BY oi.discount_pct;


-- ── 2. Break-even volume lift per depth ────────────────────
-- Business Question: How much extra volume must this discount
--                    generate just to pay for itself?
-- Why It Matters:   Converts "is the promotion working?" from an
--                   opinion into a number that can be falsified.
WITH curve AS (
    SELECT
        oi.discount_pct,
        AVG(((oi.line_total - oi.cost_total) / oi.line_total)
            * (1 - oi.discount_pct)) AS margin_pct_of_list
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY oi.discount_pct
),
base AS (
    SELECT margin_pct_of_list AS base_margin_pct
    FROM curve
    WHERE discount_pct = 0
)
SELECT
    c.discount_pct,
    ROUND(c.margin_pct_of_list, 4)                                 AS margin_pct_of_list,
    ROUND(b.base_margin_pct / c.margin_pct_of_list - 1, 4)         AS break_even_volume_lift
FROM curve c
CROSS JOIN base b
ORDER BY c.discount_pct;


-- ── 3. Is there any measured volume response? ──────────────
-- Business Question: Do deeper discounts actually sell more units?
-- Why It Matters:   If not, the ladder is margin leakage — a
--                   finding, not a failed analysis.
-- Note: SQL gives the shape; the significance test (Kruskal-Wallis,
--       p=0.305) lives in python/pricing/elasticity.py.
SELECT
    oi.discount_pct,
    COUNT(*)                    AS line_items,
    ROUND(AVG(oi.quantity), 3)  AS avg_units_per_line,
    SUM(oi.quantity)            AS total_units
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY oi.discount_pct
ORDER BY oi.discount_pct;


-- ── 4. Where the deep ladder concentrates ──────────────────
-- Business Question: Which categories carry the deepest mix of
--                    high-discount lines?
-- Why It Matters:   A margin-recovery push starts where the deep
--                   ladder is most used — not everywhere at once.
SELECT
    p.category,
    ROUND(SUM(CASE WHEN oi.discount_pct = 0     THEN 1 ELSE 0 END) * 100.0
          / COUNT(*), 1)                                            AS pct_full_price,
    ROUND(SUM(CASE WHEN oi.discount_pct >= 0.15 THEN 1 ELSE 0 END) * 100.0
          / COUNT(*), 1)                                            AS pct_deep_discount,
    ROUND(SUM(oi.line_total), 0)                                    AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 0)                    AS profit,
    ROUND(SUM(oi.line_total - oi.cost_total) / SUM(oi.line_total) * 100, 1)
                                                                    AS margin_rate_pct
FROM order_items oi
JOIN orders o   ON oi.order_id   = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY p.category
ORDER BY pct_deep_discount DESC;


-- ── 5. Margin recovered by capping the ladder (static) ─────
-- Business Question: If lines above a 10% discount had been
--                    priced at 10%, how much margin returns?
-- Why It Matters:   This is the size of the prize — calculated
--                   holding volume constant, which is exactly the
--                   assumption the break-even table exists to test.
SELECT
    COUNT(*)                                                     AS lines_repriced,
    ROUND(SUM(
        (oi.line_total * 0.90 / (1 - oi.discount_pct)) - oi.cost_total
        - (oi.line_total - oi.cost_total)
    ), 0)                                                        AS margin_recovered
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
  AND oi.discount_pct > 0.10;


-- ── 6. Margin at risk: what the deep ladder holds ──────────
-- Business Question: How much margin sits behind the 15-20% rungs?
-- Why It Matters:   Sizes the exposure in one line for the
--                   executive summary.
SELECT
    CASE WHEN oi.discount_pct >= 0.15 THEN '15-20% ladder'
         ELSE '0-10% ladder' END                                 AS ladder,
    COUNT(*)                                                     AS line_items,
    ROUND(SUM(oi.line_total), 0)                                 AS revenue,
    ROUND(SUM(oi.line_total - oi.cost_total), 0)                 AS profit,
    ROUND(SUM(oi.line_total * oi.discount_pct), 0)               AS gross_discount_given
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY ladder;
