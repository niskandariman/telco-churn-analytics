-- 04 — Rule-based high-risk identification and revenue-at-risk (pre-ML view)
-- Dialect: SQLite 3.x.
--
-- These queries are an EDA-stage risk view built from business rules that EDA
-- found to be associated with churn (month-to-month contract, low tenure,
-- electronic check, no add-ons, fiber optic). The ML model later replaces this
-- rule-based proxy with learned probabilities; the rule-based view is kept for
-- comparison and for the SQL chapter of the portfolio.

-- 4.1 Rule-based risk flag and churn outcome per risk tier.
WITH risk_flags AS (
    SELECT
        customerID,
        MonthlyCharges,
        Contract,
        tenure,
        PaymentMethod,
        Churn,
        (
            (Contract = 'Month-to-month') +
            (tenure <= 12) +
            (PaymentMethod = 'Electronic check') +
            (InternetService = 'Fiber optic')
        ) AS risk_points
    FROM telco_cleaned
),
tiered AS (
    SELECT
        *,
        CASE
            WHEN risk_points >= 3 THEN 'High'
            WHEN risk_points = 2  THEN 'Medium'
            ELSE 'Low'
        END AS rule_risk_level
    FROM risk_flags
)
SELECT
    rule_risk_level,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(MonthlyCharges), 2)                   AS monthly_revenue
FROM tiered
GROUP BY rule_risk_level
ORDER BY churn_rate_pct DESC;

-- 4.2 Revenue at risk among rule-based high-risk customers (explicit estimate:
--     monthly revenue of high-risk customers; annualized = x12 with the stated
--     assumption that the exposure horizon is one year of billing).
WITH risk_flags AS (
    SELECT
        customerID,
        MonthlyCharges,
        (
            (Contract = 'Month-to-month') +
            (tenure <= 12) +
            (PaymentMethod = 'Electronic check') +
            (InternetService = 'Fiber optic')
        ) AS risk_points
    FROM telco_cleaned
)
SELECT
    COUNT(*)                                                            AS high_risk_customers,
    ROUND(SUM(t.MonthlyCharges), 2)                                     AS monthly_revenue_at_risk_est,
    ROUND(SUM(t.MonthlyCharges) * 12, 2)                                AS annualized_revenue_at_risk_est,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN t.MonthlyCharges ELSE 0 END), 2) AS monthly_revenue_currently_churning
FROM telco_cleaned t
JOIN risk_flags r USING (customerID)
WHERE r.risk_points >= 3;

-- 4.3 High-risk AND high-value customers (top quartile monthly charges,
--     joined back to the customer table): the retention short-list.
WITH high_risk AS (
    SELECT customerID
    FROM telco_cleaned
    WHERE (Contract = 'Month-to-month') * 1
        + (tenure <= 12) * 1
        + (PaymentMethod = 'Electronic check') * 1
        + (InternetService = 'Fiber optic') * 1 >= 3
),
high_value AS (
    SELECT customerID
    FROM (
        SELECT customerID,
               NTILE(4) OVER (ORDER BY MonthlyCharges DESC) AS q
        FROM telco_cleaned
    )
    WHERE q = 1
)
SELECT
    t.customerID,
    t.MonthlyCharges,
    t.Contract,
    t.tenure,
    t.PaymentMethod,
    t.Churn
FROM telco_cleaned t
JOIN high_risk h  ON t.customerID = h.customerID
JOIN high_value v ON t.customerID = v.customerID
ORDER BY t.MonthlyCharges DESC;
