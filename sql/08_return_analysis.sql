-- ============================================================
--  08_return_analysis.sql
--  E-Commerce Analytics — Returns, Cancellations & Leakage
--
--  Revenue that never becomes revenue. Returns are a margin
--  leak and an operational cost — this quantifies both.
--
--  CAVEAT (honesty): on this synthetic dataset, order status is
--  assigned randomly and independently of products, discounts
--  and channels. Any "driver" of returns found here is noise.
--  The queries demonstrate the method; a real dataset would
--  yield real drivers. Correlation ≠ causation either way.
-- ============================================================

-- ── 1. Overall return & cancellation rates ────────────────
-- Business Question: How much of what we sell comes back?
-- Why It Matters:   Returns reverse revenue AND add logistics
--                   cost — the double leak every retailer tracks.
-- Key Insight:      Return and cancellation share of all orders.
SELECT
    COUNT(*)                                            AS all_orders,
    COUNT(*) FILTER (WHERE status = 'Returned')         AS returned_orders,
    ROUND(COUNT(*) FILTER (WHERE status = 'Returned') * 100.0
          / NULLIF(COUNT(*), 0), 2)                     AS return_rate_pct,
    COUNT(*) FILTER (WHERE status = 'Cancelled')        AS cancelled_orders,
    ROUND(COUNT(*) FILTER (WHERE status = 'Cancelled') * 100.0
          / NULLIF(COUNT(*), 0), 2)                     AS cancellation_rate_pct
FROM orders;

-- ── 2. Revenue value of returned orders ───────────────────
-- Business Question: What is the ₹ size of the return leak?
-- Why It Matters:   Rates alone hide scale — the money value
--                   lands this on the P&L agenda.
-- Key Insight:      Gross value of returned/cancelled baskets
--                   that never became revenue.
SELECT
    o.status,
    COUNT(DISTINCT o.order_id)      AS orders,
    ROUND(SUM(oi.line_total), 2)    AS basket_value_at_risk,
    ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit_at_risk
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status IN ('Returned', 'Cancelled')
GROUP BY o.status
ORDER BY basket_value_at_risk DESC;

-- ── 3. Return rate by category ────────────────────────────
-- Business Question: Do some categories come back more than others?
-- Why It Matters:   High-return categories need different sizing
--                   guides, packaging or return policies.
-- Key Insight:      Return share per category vs the overall
--                   rate — outliers are the investigation list.
SELECT
    p.category,
    COUNT(DISTINCT o.order_id)                                   AS total_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) AS returned_orders,
    ROUND(COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) * 100.0
          / NULLIF(COUNT(DISTINCT o.order_id), 0), 2)            AS return_rate_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY return_rate_pct DESC;

-- ── 4. Return rate by discount band ───────────────────────
-- Business Question: Are discounted orders returned more often?
-- Why It Matters:   If discount-driven impulse buys return at a
--                   higher rate, discounting is even more
--                   expensive than it looks.
-- Key Insight:      Return rate per discount band. (Synthetic
--                   data: expect no real relationship — see the
--                   caveat at the top of this file. The Python
--                   chi-square test in reports/statistical_analysis.md
--                   tests this formally and finds no significant
--                   association.)
SELECT
    CASE
        WHEN o.discount_pct = 0   THEN '0% (none)'
        WHEN o.discount_pct <= 5  THEN '1-5%'
        WHEN o.discount_pct <= 10 THEN '6-10%'
        WHEN o.discount_pct <= 15 THEN '11-15%'
        ELSE '16-20%'
    END AS discount_band,
    COUNT(DISTINCT o.order_id)                                   AS orders,
    COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) AS returns,
    ROUND(COUNT(DISTINCT CASE WHEN o.status = 'Returned' THEN o.order_id END) * 100.0
          / NULLIF(COUNT(DISTINCT o.order_id), 0), 2)            AS return_rate_pct
FROM orders o
GROUP BY 1
ORDER BY MIN(o.discount_pct);

-- ── 5. Most-returned products ─────────────────────────────
-- Business Question: Which SKUs trigger the most returns?
-- Why It Matters:   Product-specific return clusters usually
--                   indicate sizing, quality or description
--                   problems worth fixing at the source.
-- Key Insight:      Products ranked by number and value of
--                   returns — the fix-this-first list.
SELECT
    p.product_id, p.product_name, p.category,
    COUNT(DISTINCT o.order_id) AS returned_orders,
    ROUND(SUM(oi.line_total), 2) AS returned_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
WHERE o.status = 'Returned'
GROUP BY 1, 2, 3
ORDER BY returned_orders DESC
LIMIT 15;

-- ── 6. Repeat returners (possible abuse) ──────────────────
-- Business Question: Do a few customers account for many returns?
-- Why It Matters:   Serial returners are a policy (and sometimes
--                   fraud) problem — a watchlist is standard
--                   practice in e-commerce operations.
-- Key Insight:      Customers with multiple returned orders,
--                   ranked — the exception-review list.
WITH customer_returns AS (
    SELECT customer_id,
           COUNT(DISTINCT CASE WHEN status = 'Returned' THEN order_id END) AS returned_orders
    FROM orders
    GROUP BY customer_id
)
SELECT
    cr.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.segment, c.region,
    cr.returned_orders
FROM customer_returns cr
JOIN customers c ON cr.customer_id = c.customer_id
WHERE cr.returned_orders >= 2
ORDER BY cr.returned_orders DESC
LIMIT 25;
