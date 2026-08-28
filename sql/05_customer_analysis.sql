-- ============================================================
--  05_customer_analysis.sql
--  E-Commerce Analytics — Customer Behaviour, RFM & CLV
--
--  Who the customers are, what they are worth, and how they
--  lapse. This is the SQL heart of the retention story.
-- ============================================================

-- ── 1. RFM scoring (NTILE quintiles) ──────────────────────
-- Business Question: Who are our best, and most at-risk, customers?
-- Why It Matters:   RFM (Recency, Frequency, Monetary) is the
--                   proven triage for retention budget — every
--                   segment gets a different treatment.
-- Key Insight:      The 8 named segments used across the project
--                   (Champions, Loyal, At Risk, ...) with sizes
--                   and value — the campaign targeting map.
WITH customer_orders AS (
    SELECT
        o.customer_id,
        MAX(o.order_date)             AS last_order_date,
        COUNT(DISTINCT o.order_id)    AS frequency,
        ROUND(SUM(oi.line_total), 2)  AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY o.customer_id
),
rfm AS (
    SELECT
        customer_id,
        (SELECT MAX(order_date) FROM orders WHERE status NOT IN ('Cancelled','Returned'))
            - last_order_date                          AS recency_days,
        frequency, monetary,
        NTILE(5) OVER (ORDER BY (SELECT MAX(order_date) FROM orders WHERE status NOT IN ('Cancelled','Returned'))
            - last_order_date DESC)                    AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)          AS m_score
    FROM customer_orders
)
SELECT
    r_score, f_score, m_score,
    r_score + f_score + m_score                        AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'Recent Customers'
        WHEN r_score >= 3 AND m_score >= 3                  THEN 'Potential Loyalists'
        WHEN r_score <= 2 AND f_score >= 4                  THEN 'At Risk'
        WHEN r_score <= 2 AND f_score >= 2                  THEN 'About To Sleep'
        WHEN r_score <= 1                                    THEN 'Lost Customers'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM rfm;

-- ── 2. Segment sizes & value (the targeting table) ────────
-- Business Question: How big and how valuable is each segment?
-- Why It Matters:   Converts segments into a budget-allocation
--                   table: spend follows value and risk.
-- Key Insight:      Segment counts and total spend — identifies
--                   where a win-back campaign pays for itself.
WITH rfm AS (
    SELECT o.customer_id,
           MAX(o.order_date)            AS last_order_date,
           COUNT(DISTINCT o.order_id)   AS frequency,
           SUM(oi.line_total)           AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY o.customer_id
),
scored AS (
    SELECT customer_id, frequency, monetary,
           NTILE(5) OVER (ORDER BY (SELECT MAX(order_date) FROM orders WHERE status NOT IN ('Cancelled','Returned')) - last_order_date DESC) AS r,
           NTILE(5) OVER (ORDER BY frequency ASC)  AS f,
           NTILE(5) OVER (ORDER BY monetary ASC)   AS m
    FROM rfm
)
SELECT
    CASE
        WHEN r >= 4 AND f >= 4 AND m >= 4 THEN 'Champions'
        WHEN r >= 3 AND f >= 3            THEN 'Loyal Customers'
        WHEN r >= 4 AND f <= 2            THEN 'Recent Customers'
        WHEN r >= 3 AND m >= 3            THEN 'Potential Loyalists'
        WHEN r <= 2 AND f >= 4            THEN 'At Risk'
        WHEN r <= 2 AND f >= 2            THEN 'About To Sleep'
        WHEN r <= 1                        THEN 'Lost Customers'
        ELSE 'Needs Attention'
    END AS segment,
    COUNT(*)                     AS customers,
    ROUND(AVG(monetary), 2)      AS avg_spend,
    ROUND(SUM(monetary), 2)      AS total_spend
FROM scored
GROUP BY 1
ORDER BY total_spend DESC;

-- ── 3. High-value customers (DENSE_RANK) ──────────────────
-- Business Question: Who exactly are the top 25 customers?
-- Why It Matters:   Named VIP list for loyalty programmes,
--                   white-glove service and churn escalation.
-- Key Insight:      A ranked list with recency — a VIP who has
--                   gone quiet appears here first.
WITH customer_spend AS (
    SELECT
        o.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.segment, c.region, c.acquisition_channel,
        MAX(o.order_date)            AS last_order,
        COUNT(DISTINCT o.order_id)   AS total_orders,
        SUM(oi.line_total)           AS total_revenue
    FROM orders o
    JOIN customers c  ON o.customer_id  = c.customer_id
    JOIN order_items oi ON o.order_id   = oi.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY 1, 2, 3, 4, 5
)
SELECT
    DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS value_rank,
    customer_id, customer_name, segment, region, acquisition_channel,
    total_orders,
    ROUND(total_revenue, 2)  AS total_revenue,
    last_order
FROM customer_spend
ORDER BY value_rank
LIMIT 25;

-- ── 4. Repeat-purchase behaviour ──────────────────────────
-- Business Question: Do customers come back after the first order?
-- Why It Matters:   Repeat rate is the economics of e-commerce —
--                   CAC is only justified if customers reorder.
-- Key Insight:      Distribution of customers by order count;
--                   heavy left-tails mean acquisition without
--                   retention.
SELECT
    CASE
        WHEN order_count = 1  THEN '1 order'
        WHEN order_count <= 3 THEN '2-3 orders'
        WHEN order_count <= 5 THEN '4-5 orders'
        ELSE '6+ orders'
    END AS repeat_bucket,
    COUNT(*)                                            AS customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)  AS pct
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
    GROUP BY customer_id
) t
GROUP BY 1
ORDER BY MIN(order_count);

-- ── 5. Time between orders (LAG per customer) ─────────────
-- Business Question: How long do customers typically wait between orders?
-- Why It Matters:   The waiting-time distribution defines a
--                   data-driven "we miss you" trigger — far better
--                   than guessing a number of days.
-- Key Insight:      Median days between consecutive purchases;
--                   customers far past their own cadence are the
--                   natural churn watchlist.
WITH ordered AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
),
gaps AS (
    SELECT customer_id, order_date - prev_order_date AS days_between
    FROM ordered
    WHERE prev_order_date IS NOT NULL
)
SELECT
    ROUND(AVG(days_between), 1)     AS avg_days_between_orders,
    ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY days_between), 1) AS median_days_between,
    MAX(days_between)               AS max_gap
FROM gaps;

-- ── 6. Monthly cohort retention ───────────────────────────
-- Business Question: Do newer cohorts retain as well as older ones?
-- Why It Matters:   Retention is visible only in cohorts —
--                   blended totals hide decay.
-- Key Insight:      Rows per cohort-month; shrinking rows to the
--                   right = the retention curve of each cohort.
WITH first_order AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
    GROUP BY customer_id
),
activity AS (
    SELECT
        fo.cohort_month,
        DATE_TRUNC('month', o.order_date) AS order_month,
        (EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', o.order_date), fo.cohort_month)) * 12
         + EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', o.order_date), fo.cohort_month))) AS period_number
    FROM orders o
    JOIN first_order fo ON o.customer_id = fo.customer_id
    WHERE o.status NOT IN ('Cancelled','Returned')
)
SELECT
    cohort_month,
    period_number,
    COUNT(DISTINCT cohort_month || customer_id) AS customers
FROM (
    SELECT DISTINCT a.cohort_month, a.order_month, a.period_number, o.customer_id
    FROM activity a
    JOIN orders o ON DATE_TRUNC('month', o.order_date) = a.order_month
                 AND o.status NOT IN ('Cancelled','Returned')
) x
GROUP BY cohort_month, period_number
ORDER BY cohort_month, period_number;

-- ── 7. New vs returning customers per month ───────────────
-- Business Question: Is growth coming from new customers or repeats?
-- Why It Matters:   A business growing only on new customers is
--                   renting growth; the mix reveals it.
-- Key Insight:      Monthly split of new vs returning buyers and
--                   their revenue — the acquisition/retention mix.
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
    GROUP BY customer_id
)
SELECT
    DATE_TRUNC('month', o.order_date)         AS month,
    COUNT(DISTINCT CASE WHEN o.order_date = fo.first_date THEN o.customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN o.order_date >  fo.first_date THEN o.customer_id END) AS returning_customers,
    ROUND(SUM(CASE WHEN o.order_date = fo.first_date THEN oi.line_total ELSE 0 END), 2) AS new_revenue,
    ROUND(SUM(CASE WHEN o.order_date >  fo.first_date THEN oi.line_total ELSE 0 END), 2) AS returning_revenue
FROM orders o
JOIN first_order fo ON o.customer_id = fo.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY 1
ORDER BY 1;

-- ── 8. Churn watchlist (SQL mirror of the ML label) ───────
-- Business Question: Which customers have gone quiet, and how
--                    much historical spend do they represent?
-- Why It Matters:   This is the campaign list. Note: this is
--                   descriptive (already lapsed). The Python
--                   model predicts who will lapse next.
-- Key Insight:      Customers with no purchase in 180+ days and
--                   their spend — the size of the win-back prize.
WITH last_purchase AS (
    SELECT
        o.customer_id,
        MAX(o.order_date)           AS last_order_date,
        COUNT(DISTINCT o.order_id)  AS total_orders,
        SUM(oi.line_total)          AS total_spent
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY o.customer_id
)
SELECT
    c.customer_id, c.segment, c.region,
    lp.last_order_date,
    (SELECT MAX(order_date) FROM orders WHERE status NOT IN ('Cancelled','Returned'))
        - lp.last_order_date AS days_since_purchase,
    lp.total_orders,
    ROUND(lp.total_spent, 2) AS total_spent,
    CASE
        WHEN (SELECT MAX(order_date) FROM orders WHERE status NOT IN ('Cancelled','Returned'))
             - lp.last_order_date <= 90  THEN 'Active'
        WHEN (SELECT MAX(order_date) FROM orders WHERE status NOT IN ('Cancelled','Returned'))
             - lp.last_order_date <= 180 THEN 'Cooling'
        ELSE 'Lapsed (churn watchlist)'
    END AS churn_status
FROM customers c
JOIN last_purchase lp ON c.customer_id = lp.customer_id
ORDER BY days_since_purchase DESC;
