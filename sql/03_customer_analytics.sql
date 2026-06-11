-- ============================================================
--  03 — Customer Analytics: RFM + Retention + Churn SQL
-- ============================================================

-- ── 1. RFM Base Calculation ───────────────────────────────
WITH customer_orders AS (
    SELECT
        o.customer_id,
        MAX(o.order_date)                  AS last_order_date,
        COUNT(DISTINCT o.order_id)         AS frequency,
        ROUND(SUM(oi.line_total), 2)       AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled', 'Returned')
    GROUP BY o.customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        CURRENT_DATE - last_order_date     AS recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY CURRENT_DATE - last_order_date DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)     AS m_score
    FROM customer_orders
)
SELECT
    rs.*,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'Recent Customers'
        WHEN r_score >= 3 AND f_score >= 1 AND m_score >= 3 THEN 'Potential Loyalists'
        WHEN r_score <= 2 AND f_score >= 4                  THEN 'At Risk'
        WHEN r_score <= 2 AND f_score >= 2                  THEN 'About To Sleep'
        WHEN r_score <= 1                                    THEN 'Lost Customers'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM rfm_scores rs;

-- ── 2. Customer Lifetime Value (CLV) ─────────────────────
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.segment,
    c.region,
    c.acquisition_channel,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    ROUND(SUM(oi.line_total), 2)        AS total_revenue,
    ROUND(SUM(oi.line_total) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
    MIN(o.order_date)                   AS first_order,
    MAX(o.order_date)                   AS last_order,
    MAX(o.order_date) - MIN(o.order_date) AS customer_lifespan_days
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id    = oi.order_id
WHERE o.status NOT IN ('Cancelled', 'Returned')
GROUP BY c.customer_id, c.first_name, c.last_name, c.segment, c.region, c.acquisition_channel
ORDER BY total_revenue DESC;

-- ── 3. Monthly Cohort Retention ──────────────────────────
WITH first_order AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
    GROUP BY customer_id
),
orders_with_cohort AS (
    SELECT
        o.customer_id,
        fo.cohort_month,
        DATE_TRUNC('month', o.order_date) AS order_month,
        EXTRACT(YEAR FROM AGE(DATE_TRUNC('month', o.order_date), fo.cohort_month))
            * 12 +
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', o.order_date), fo.cohort_month))
            AS period
    FROM orders o
    JOIN first_order fo ON o.customer_id = fo.customer_id
    WHERE o.status NOT IN ('Cancelled','Returned')
)
SELECT
    cohort_month,
    period,
    COUNT(DISTINCT customer_id) AS customers
FROM orders_with_cohort
GROUP BY cohort_month, period
ORDER BY cohort_month, period;

-- ── 4. Customer Churn Indicators ─────────────────────────
WITH last_purchase AS (
    SELECT
        o.customer_id,
        MAX(o.order_date)          AS last_order_date,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.line_total)         AS total_spent
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('Cancelled','Returned')
    GROUP BY o.customer_id
)
SELECT
    c.customer_id,
    c.segment,
    c.region,
    lp.last_order_date,
    CURRENT_DATE - lp.last_order_date AS days_since_purchase,
    lp.total_orders,
    ROUND(lp.total_spent, 2) AS total_spent,
    CASE
        WHEN CURRENT_DATE - lp.last_order_date <= 30  THEN 'Active'
        WHEN CURRENT_DATE - lp.last_order_date <= 90  THEN 'Warm'
        WHEN CURRENT_DATE - lp.last_order_date <= 180 THEN 'Cooling'
        WHEN CURRENT_DATE - lp.last_order_date <= 365 THEN 'At Risk'
        ELSE 'Churned'
    END AS churn_status
FROM customers c
JOIN last_purchase lp ON c.customer_id = lp.customer_id
ORDER BY days_since_purchase DESC;

-- ── 5. New vs Returning Customers Monthly ────────────────
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
    GROUP BY customer_id
)
SELECT
    DATE_TRUNC('month', o.order_date) AS month,
    SUM(CASE WHEN o.order_date = fo.first_date THEN 1 ELSE 0 END) AS new_customers,
    SUM(CASE WHEN o.order_date > fo.first_date THEN 1 ELSE 0 END) AS returning_customers,
    ROUND(SUM(CASE WHEN o.order_date > fo.first_date THEN oi.line_total ELSE 0 END), 2) AS returning_revenue,
    ROUND(SUM(CASE WHEN o.order_date = fo.first_date THEN oi.line_total ELSE 0 END), 2) AS new_revenue
FROM orders o
JOIN first_order fo  ON o.customer_id = fo.customer_id
JOIN order_items oi  ON o.order_id    = oi.order_id
WHERE o.status NOT IN ('Cancelled','Returned')
GROUP BY 1
ORDER BY 1;

-- ── 6. Repeat Purchase Rate ───────────────────────────────
SELECT
    repeat_bucket,
    COUNT(*) AS customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM (
    SELECT
        customer_id,
        CASE
            WHEN COUNT(DISTINCT order_id) = 1 THEN '1 order'
            WHEN COUNT(DISTINCT order_id) <= 3 THEN '2-3 orders'
            WHEN COUNT(DISTINCT order_id) <= 5 THEN '4-5 orders'
            ELSE '6+ orders'
        END AS repeat_bucket
    FROM orders
    WHERE status NOT IN ('Cancelled','Returned')
    GROUP BY customer_id
) t
GROUP BY repeat_bucket
ORDER BY MIN(CASE repeat_bucket
    WHEN '1 order' THEN 1
    WHEN '2-3 orders' THEN 2
    WHEN '4-5 orders' THEN 3
    ELSE 4 END);
