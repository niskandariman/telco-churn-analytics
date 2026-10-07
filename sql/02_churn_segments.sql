-- 02 — Churn by business segments
-- Dialect: SQLite 3.x. CASE WHEN tenure bands, GROUP BY aggregations,
-- and a window function (RANK) that genuinely ranks segments by churn rate.

-- 2.1 Churn by contract type (ranked worst-first with a window function).
WITH contract_churn AS (
    SELECT
        Contract,
        COUNT(*)                                        AS customers,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
        ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
    FROM telco_cleaned
    GROUP BY Contract
)
SELECT
    Contract,
    customers,
    churners,
    churn_rate_pct,
    RANK() OVER (ORDER BY churn_rate_pct DESC) AS risk_rank
FROM contract_churn
ORDER BY churn_rate_pct DESC;

-- 2.2 Churn by payment method.
SELECT
    PaymentMethod,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM telco_cleaned
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;

-- 2.3 Churn by tenure band (CASE WHEN bands).
SELECT
    CASE
        WHEN tenure <= 6  THEN '0-6 mo'
        WHEN tenure <= 12 THEN '7-12 mo'
        WHEN tenure <= 24 THEN '13-24 mo'
        WHEN tenure <= 48 THEN '25-48 mo'
        ELSE '49-72 mo'
    END                                             AS tenure_band,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM telco_cleaned
GROUP BY tenure_band
ORDER BY MIN(tenure);

-- 2.4 Churn by internet service and add-on service usage (service-level view).
SELECT
    InternetService,
    CASE
        WHEN OnlineSecurity = 'Yes' THEN 'OnlineSecurity: Yes'
        WHEN InternetService = 'No' THEN 'n/a (no internet)'
        ELSE 'OnlineSecurity: No'
    END                                             AS addon_flag,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM telco_cleaned
GROUP BY InternetService, addon_flag
ORDER BY InternetService, churn_rate_pct DESC;

-- 2.5 Churn by contract x internet service: the high-risk pockets.
SELECT
    Contract,
    InternetService,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM telco_cleaned
GROUP BY Contract, InternetService
ORDER BY churn_rate_pct DESC;
