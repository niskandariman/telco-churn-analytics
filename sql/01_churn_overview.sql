-- 01 — Overall churn, customer counts and revenue metrics
-- Dialect: SQLite 3.x. Table: telco_cleaned (loaded from data/processed/telco_cleaned.csv).

-- 1.1 Headline KPIs: customers, churners, churn rate, monthly revenue, avg ticket.
SELECT
    COUNT(*)                                              AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)        AS churned_customers,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(MonthlyCharges), 2)                         AS total_monthly_revenue,
    ROUND(AVG(MonthlyCharges), 2)                         AS avg_monthly_charges,
    ROUND(SUM(TotalCharges), 2)                           AS total_charges_to_date
FROM telco_cleaned;

-- 1.2 Customer counts by churn outcome.
SELECT
    Churn,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM telco_cleaned
GROUP BY Churn;

-- 1.3 Revenue metrics by churn outcome.
SELECT
    Churn,
    COUNT(*)                                       AS customers,
    ROUND(SUM(MonthlyCharges), 2)                  AS monthly_revenue,
    ROUND(AVG(MonthlyCharges), 2)                  AS avg_monthly_charges,
    ROUND(SUM(TotalCharges), 2)                    AS total_charges_to_date,
    ROUND(AVG(tenure), 1)                          AS avg_tenure_months
FROM telco_cleaned
GROUP BY Churn;
