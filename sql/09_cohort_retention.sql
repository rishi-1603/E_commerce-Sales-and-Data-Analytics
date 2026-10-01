-- ============================================================
--  09_cohort_retention.sql
--  E-Commerce Analytics — Cohort Retention Matrix
--
--  Purpose : Group customers by first-purchase month and measure
--            how many are still active k months later. The
--            retention view every growth review starts with.
--
--  Definition (must match data/metrics.json):
--    purchase   = order with status Delivered or Returned
--                 (cancelled never transacted; processing is
--                 not yet a purchase)
--    cohort     = calendar month of a customer's first purchase
--    retention  = % of cohort with >=1 purchase k months after
--                 the cohort month (M0 = 100% by definition)
--
--  Verified pattern (Python: scripts/decision_layer.py):
--    month-1 retention rises from ~15-28% (2023 cohorts) to
--    55-88% (late 2024) — retention improves with business
--    maturity. Decision: invest in the onboarding window that
--    drives the second purchase.
-- ============================================================

-- ── 1. Cohort retention matrix ─────────────────────────────
-- Business Question: Do newer customers stick around better?
-- Why It Matters:   Retention compounds — a point of month-1
--                   retention is worth more than a point of
--                   acquisition at this scale.
WITH purchases AS (                -- purchases only, per definition
    SELECT o.customer_id,
           o.order_id,
           o.order_date,
           DATE_TRUNC('month', o.order_date) AS order_month
    FROM orders o
    WHERE o.status IN ('Delivered', 'Returned')
),
first_purchase AS (                -- cohort assignment
    SELECT customer_id,
           MIN(order_month) AS cohort_month
    FROM purchases
    GROUP BY customer_id
),
activity AS (                      -- one row per customer per active month
    SELECT p.customer_id,
           p.order_month,
           f.cohort_month,
           (EXTRACT(YEAR FROM p.order_month) - EXTRACT(YEAR FROM f.cohort_month)) * 12
             + (EXTRACT(MONTH FROM p.order_month) - EXTRACT(MONTH FROM f.cohort_month)) AS months_since
    FROM purchases p
    JOIN first_purchase f USING (customer_id)
)
SELECT
    TO_CHAR(cohort_month, 'YYYY-MM')                          AS cohort,
    COUNT(DISTINCT customer_id)                               AS cohort_size,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since = 0  THEN customer_id END) / COUNT(DISTINCT customer_id), 1) AS m0_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since = 1  THEN customer_id END) / COUNT(DISTINCT customer_id), 1) AS m1_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since = 2  THEN customer_id END) / COUNT(DISTINCT customer_id), 1) AS m2_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since = 3  THEN customer_id END) / COUNT(DISTINCT customer_id), 1) AS m3_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since = 6  THEN customer_id END) / COUNT(DISTINCT customer_id), 1) AS m6_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since = 12 THEN customer_id END) / COUNT(DISTINCT customer_id), 1) AS m12_pct
FROM activity
GROUP BY cohort_month
ORDER BY cohort_month;

-- ── 2. Average retention curve across all cohorts ─────────
-- Business Question: What does the average customer's decay
--                    curve look like, and where does it flatten?
WITH purchases AS (
    SELECT o.customer_id, DATE_TRUNC('month', o.order_date) AS order_month
    FROM orders o
    WHERE o.status IN ('Delivered', 'Returned')
),
first_purchase AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM purchases GROUP BY customer_id
),
activity AS (
    SELECT p.customer_id, f.cohort_month,
           (EXTRACT(YEAR FROM p.order_month) - EXTRACT(YEAR FROM f.cohort_month)) * 12
             + (EXTRACT(MONTH FROM p.order_month) - EXTRACT(MONTH FROM f.cohort_month)) AS months_since
    FROM purchases p JOIN first_purchase f USING (customer_id)
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size FROM first_purchase GROUP BY cohort_month
)
SELECT a.months_since,
       ROUND(100.0 * COUNT(DISTINCT a.customer_id) / SUM(s.cohort_size), 1) AS avg_retention_pct
FROM activity a
JOIN sizes s ON a.cohort_month = s.cohort_month
WHERE a.months_since <= 12
GROUP BY a.months_since
ORDER BY a.months_since;
