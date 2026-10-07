-- 03 — Customer segmentation and high-value customers
-- Dialect: SQLite 3.x. NTILE window function for value quartiles; a JOIN back
-- to the customer table (the dataset is a single flat table, so the only
-- genuine JOIN use is joining aggregate segments back to customer rows).

-- 3.1 Value quartiles (NTILE over monthly charges) with churn per quartile.
WITH value_tiers AS (
    SELECT
        customerID,
        MonthlyCharges,
        Contract,
        NTILE(4) OVER (ORDER BY MonthlyCharges) AS value_quartile
    FROM telco_cleaned
)
SELECT
    value_quartile,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(t.MonthlyCharges), 2)                 AS monthly_revenue
FROM telco_cleaned t
JOIN value_tiers v USING (customerID)
GROUP BY value_quartile
ORDER BY value_quartile;

-- 3.2 Business segmentation: contract x tenure-band x churn, with revenue.
SELECT
    Contract,
    CASE
        WHEN tenure <= 12 THEN '0-12 mo'
        WHEN tenure <= 48 THEN '13-48 mo'
        ELSE '49-72 mo'
    END                                             AS tenure_band,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(MonthlyCharges), 2)                   AS monthly_revenue,
    ROUND(SUM(CASE WHEN Churn = 'Yes' THEN MonthlyCharges ELSE 0 END), 2) AS churning_monthly_revenue
FROM telco_cleaned
GROUP BY Contract, tenure_band
ORDER BY churning_monthly_revenue DESC;

-- 3.3 High-value customers: top quartile of MonthlyCharges.
WITH ranked AS (
    SELECT
        customerID,
        MonthlyCharges,
        Contract,
        tenure,
        Churn,
        NTILE(4) OVER (ORDER BY MonthlyCharges DESC) AS value_quartile
    FROM telco_cleaned
)
SELECT
    customerID,
    MonthlyCharges,
    Contract,
    tenure,
    Churn
FROM ranked
WHERE value_quartile = 1
ORDER BY MonthlyCharges DESC
LIMIT 20;
