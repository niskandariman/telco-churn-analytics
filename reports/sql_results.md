# SQL Analysis Results

Executed against `data/processed/telco_cleaned.csv` (7,043 rows) in SQLite. Dialect: SQLite 3.x; results identical on any ANSI-compatible engine for the constructs used.

## 01_churn_overview.sql

### 01_churn_overview — statement 1

```sql
SELECT
    COUNT(*)                                              AS total_customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)        AS churned_customers,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(MonthlyCharges), 2)                         AS total_monthly_revenue,
    ROUND(AVG(MonthlyCharges), 2)                         AS avg_monthly_charges,
    ROUND(SUM(TotalCharges), 2)                           AS total_charges_to_date
FROM telco_cleaned;
```

|   total_customers |   churned_customers |   churn_rate_pct |   total_monthly_revenue |   avg_monthly_charges |   total_charges_to_date |
|------------------:|--------------------:|-----------------:|------------------------:|----------------------:|------------------------:|
|              7043 |                1869 |            26.54 |                  456117 |                 64.76 |             1.60562e+07 |

### 01_churn_overview — statement 2

```sql
SELECT
    Churn,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM telco_cleaned
GROUP BY Churn;
```

| Churn   |   customers |   share_pct |
|:--------|------------:|------------:|
| No      |        5174 |       73.46 |
| Yes     |        1869 |       26.54 |

### 01_churn_overview — statement 3

```sql
SELECT
    Churn,
    COUNT(*)                                       AS customers,
    ROUND(SUM(MonthlyCharges), 2)                  AS monthly_revenue,
    ROUND(AVG(MonthlyCharges), 2)                  AS avg_monthly_charges,
    ROUND(SUM(TotalCharges), 2)                    AS total_charges_to_date,
    ROUND(AVG(tenure), 1)                          AS avg_tenure_months
FROM telco_cleaned
GROUP BY Churn;
```

| Churn   |   customers |   monthly_revenue |   avg_monthly_charges |   total_charges_to_date |   avg_tenure_months |
|:--------|------------:|------------------:|----------------------:|------------------------:|--------------------:|
| No      |        5174 |            316986 |                 61.27 |             1.31932e+07 |                37.6 |
| Yes     |        1869 |            139131 |                 74.44 |             2.86293e+06 |                18   |

## 02_churn_segments.sql

### 02_churn_segments — statement 1

```sql
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
```

| Contract       |   customers |   churners |   churn_rate_pct |   risk_rank |
|:---------------|------------:|-----------:|-----------------:|------------:|
| Month-to-month |        3875 |       1655 |            42.71 |           1 |
| One year       |        1473 |        166 |            11.27 |           2 |
| Two year       |        1695 |         48 |             2.83 |           3 |

### 02_churn_segments — statement 2

```sql
SELECT
    PaymentMethod,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM telco_cleaned
GROUP BY PaymentMethod
ORDER BY churn_rate_pct DESC;
```

| PaymentMethod             |   customers |   churners |   churn_rate_pct |
|:--------------------------|------------:|-----------:|-----------------:|
| Electronic check          |        2365 |       1071 |            45.29 |
| Mailed check              |        1612 |        308 |            19.11 |
| Bank transfer (automatic) |        1544 |        258 |            16.71 |
| Credit card (automatic)   |        1522 |        232 |            15.24 |

### 02_churn_segments — statement 3

```sql
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
```

| tenure_band   |   customers |   churners |   churn_rate_pct |
|:--------------|------------:|-----------:|-----------------:|
| 0-6 mo        |        1481 |        784 |            52.94 |
| 7-12 mo       |         705 |        253 |            35.89 |
| 13-24 mo      |        1024 |        294 |            28.71 |
| 25-48 mo      |        1594 |        325 |            20.39 |
| 49-72 mo      |        2239 |        213 |             9.51 |

### 02_churn_segments — statement 4

```sql
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
```

| InternetService   | addon_flag          |   customers |   churners |   churn_rate_pct |
|:------------------|:--------------------|------------:|-----------:|-----------------:|
| DSL               | OnlineSecurity: No  |        1241 |        347 |            27.96 |
| DSL               | OnlineSecurity: Yes |        1180 |        112 |             9.49 |
| Fiber optic       | OnlineSecurity: No  |        2257 |       1114 |            49.36 |
| Fiber optic       | OnlineSecurity: Yes |         839 |        183 |            21.81 |
| No                | n/a (no internet)   |        1526 |        113 |             7.4  |

### 02_churn_segments — statement 5

```sql
SELECT
    Contract,
    InternetService,
    COUNT(*)                                        AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END)  AS churners,
    ROUND(100.0 * SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct
FROM telco_cleaned
GROUP BY Contract, InternetService
ORDER BY churn_rate_pct DESC;
```

| Contract       | InternetService   |   customers |   churners |   churn_rate_pct |
|:---------------|:------------------|------------:|-----------:|-----------------:|
| Month-to-month | Fiber optic       |        2128 |       1162 |            54.61 |
| Month-to-month | DSL               |        1223 |        394 |            32.22 |
| One year       | Fiber optic       |         539 |        104 |            19.29 |
| Month-to-month | No                |         524 |         99 |            18.89 |
| One year       | DSL               |         570 |         53 |             9.3  |
| Two year       | Fiber optic       |         429 |         31 |             7.23 |
| One year       | No                |         364 |          9 |             2.47 |
| Two year       | DSL               |         628 |         12 |             1.91 |
| Two year       | No                |         638 |          5 |             0.78 |

## 03_segmentation_value.sql

### 03_segmentation_value — statement 1

```sql
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
```

|   value_quartile |   customers |   churners |   churn_rate_pct |   monthly_revenue |
|-----------------:|------------:|-----------:|-----------------:|------------------:|
|                1 |        1761 |        198 |            11.24 |           39134.3 |
|                2 |        1761 |        434 |            24.65 |           98031.4 |
|                3 |        1761 |        659 |            37.42 |          141391   |
|                4 |        1760 |        578 |            32.84 |          177560   |

### 03_segmentation_value — statement 2

```sql
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
```

| Contract       | tenure_band   |   customers |   churners |   churn_rate_pct |   monthly_revenue |   churning_monthly_revenue |
|:---------------|:--------------|------------:|-----------:|-----------------:|------------------:|---------------------------:|
| Month-to-month | 0-12 mo       |        1994 |       1024 |            51.35 |         116086    |                   68301.4  |
| Month-to-month | 13-48 mo      |        1539 |        542 |            35.22 |         111985    |                   44537.3  |
| Month-to-month | 49-72 mo      |         342 |         89 |            26.02 |          29222.5  |                    8008.35 |
| One year       | 49-72 mo      |         634 |         82 |            12.93 |          50443.3  |                    7842.95 |
| One year       | 13-48 mo      |         715 |         71 |             9.93 |          40934.4  |                    5622.7  |
| Two year       | 49-72 mo      |        1263 |         42 |             3.33 |          85897.9  |                    3781.15 |
| One year       | 0-12 mo       |         124 |         13 |            10.48 |           4438.9  |                     652.8  |
| Two year       | 13-48 mo      |         364 |          6 |             1.65 |          15003.5  |                     384.15 |
| Two year       | 0-12 mo       |          68 |          0 |             0    |           2104.35 |                       0    |

### 03_segmentation_value — statement 3

```sql
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
```

| customerID   |   MonthlyCharges | Contract       |   tenure | Churn   |
|:-------------|-----------------:|:---------------|---------:|:--------|
| 7569-NMZYQ   |           118.75 | Two year       |       72 | No      |
| 8984-HPEMB   |           118.65 | Two year       |       71 | No      |
| 5989-AXPUC   |           118.6  | Two year       |       68 | No      |
| 5734-EJKXG   |           118.6  | One year       |       61 | No      |
| 8199-ZLLSA   |           118.35 | One year       |       67 | Yes     |
| 9924-JPRMC   |           118.2  | Two year       |       72 | No      |
| 2889-FPWRM   |           117.8  | One year       |       72 | Yes     |
| 3810-DVDQQ   |           117.6  | Two year       |       72 | No      |
| 9739-JLPQJ   |           117.5  | Two year       |       72 | No      |
| 2302-ANTDP   |           117.45 | Month-to-month |       48 | Yes     |
| 6904-JLBGY   |           117.35 | Two year       |       72 | No      |
| 4282-MSACW   |           117.2  | One year       |       68 | No      |
| 6650-BWFRT   |           117.15 | Two year       |       72 | No      |
| 9788-HNGUT   |           116.95 | Two year       |       72 | No      |
| 1488-PBLJN   |           116.85 | Two year       |       72 | No      |
| 0017-IUDMW   |           116.8  | Two year       |       72 | No      |
| 8628-MFKAX   |           116.75 | Two year       |       72 | No      |
| 3680-CTHUH   |           116.6  | One year       |       60 | No      |
| 3258-ZKPAI   |           116.6  | Two year       |       72 | No      |
| 3795-CAWEX   |           116.55 | Two year       |       70 | No      |

## 04_risk_revenue.sql

### 04_risk_revenue — statement 1

```sql
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
```

| rule_risk_level   |   customers |   churners |   churn_rate_pct |   monthly_revenue |
|:------------------|------------:|-----------:|-----------------:|------------------:|
| High              |        1919 |       1137 |            59.25 |            151724 |
| Medium            |        1818 |        522 |            28.71 |            115269 |
| Low               |        3306 |        210 |             6.35 |            189124 |

### 04_risk_revenue — statement 2

```sql
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
```

|   high_risk_customers |   monthly_revenue_at_risk_est |   annualized_revenue_at_risk_est |   monthly_revenue_currently_churning |
|----------------------:|------------------------------:|---------------------------------:|-------------------------------------:|
|                  1919 |                        151724 |                      1.82068e+06 |                              90936.6 |

### 04_risk_revenue — statement 3

```sql
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
```

| customerID   |   MonthlyCharges | Contract       |   tenure | PaymentMethod             | Churn   |
|:-------------|-----------------:|:---------------|---------:|:--------------------------|:--------|
| 2302-ANTDP   |           117.45 | Month-to-month |       48 | Electronic check          | Yes     |
| 8016-NCFVO   |           116.5  | Month-to-month |       55 | Electronic check          | No      |
| 9659-QEQSY   |           115.65 | Month-to-month |       45 | Electronic check          | No      |
| 6710-HSJRD   |           114.1  | Month-to-month |       61 | Electronic check          | No      |
| 7279-BUYWN   |           113.2  | Month-to-month |       41 | Electronic check          | Yes     |
| 0771-WLCLA   |           112.95 | Month-to-month |       16 | Electronic check          | No      |
| 1583-IHQZE   |           112.95 | Month-to-month |       12 | Mailed check              | Yes     |
| 2587-EKXTS   |           111.5  | Month-to-month |       44 | Electronic check          | No      |
| 3292-PBZEJ   |           111.4  | Month-to-month |       11 | Electronic check          | No      |
| 6168-YBYNP   |           111.35 | Month-to-month |       59 | Electronic check          | No      |
| 0115-TFERT   |           111.2  | Month-to-month |       21 | Electronic check          | Yes     |
| 2067-QYTCF   |           111.15 | Month-to-month |       64 | Electronic check          | No      |
| 9079-YEXQJ   |           111.1  | Month-to-month |       54 | Electronic check          | Yes     |
| 6030-REHUX   |           110.85 | Month-to-month |       28 | Electronic check          | No      |
| 1320-REHCS   |           110.75 | Month-to-month |       52 | Electronic check          | No      |
| 3336-JORSO   |           110.45 | Month-to-month |       33 | Electronic check          | Yes     |
| 7576-JMYWV   |           110.2  | Month-to-month |       46 | Electronic check          | No      |
| 9851-KIELU   |           110.1  | Month-to-month |       10 | Electronic check          | Yes     |
| 3174-RKMOW   |           109.95 | Month-to-month |       35 | Electronic check          | No      |
| 3992-YWPKO   |           109.9  | Month-to-month |        6 | Credit card (automatic)   | Yes     |
| 6599-RCLCJ   |           109.55 | Month-to-month |       47 | Electronic check          | Yes     |
| 4176-FXYBO   |           109.55 | Month-to-month |       54 | Electronic check          | No      |
| 3571-RFHAR   |           109.15 | Month-to-month |       65 | Electronic check          | Yes     |
| 9278-VZKCD   |           109.1  | Month-to-month |       52 | Electronic check          | No      |
| 9971-ZWPBF   |           108.9  | Month-to-month |       34 | Electronic check          | No      |
| 2027-WKXMW   |           108.75 | Month-to-month |       63 | Electronic check          | No      |
| 5760-IFJOZ   |           107.95 | Month-to-month |        3 | Mailed check              | No      |
| 2081-VEYEH   |           107.95 | Month-to-month |        3 | Electronic check          | No      |
| 7821-DPRQE   |           107.7  | Month-to-month |       68 | Electronic check          | No      |
| 0114-PEGZZ   |           107.55 | Month-to-month |       33 | Electronic check          | No      |
| 8800-ZKRFW   |           107.5  | Month-to-month |       30 | Electronic check          | No      |
| 2615-YVMYX   |           107.5  | Month-to-month |       71 | Electronic check          | No      |
| 4716-HHKQH   |           107.05 | Month-to-month |       20 | Electronic check          | No      |
| 3606-TWKGI   |           106.9  | Month-to-month |       13 | Electronic check          | Yes     |
| 9137-UIYPG   |           106.9  | Month-to-month |       35 | Electronic check          | No      |
| 9572-MTILT   |           106.75 | Month-to-month |       59 | Electronic check          | Yes     |
| 2027-FECZV   |           106.7  | Month-to-month |       12 | Electronic check          | Yes     |
| 7825-ECJRF   |           106.6  | Month-to-month |       19 | Electronic check          | Yes     |
| 9822-WMWVG   |           106.5  | Month-to-month |       41 | Electronic check          | No      |
| 8535-SFUTN   |           106.45 | Month-to-month |       61 | Electronic check          | No      |
| 8118-LSUEL   |           106.4  | Month-to-month |       23 | Electronic check          | Yes     |
| 8938-UMKPI   |           106.4  | Month-to-month |       47 | Electronic check          | Yes     |
| 7048-GXDAY   |           106.4  | Month-to-month |       39 | Electronic check          | No      |
| 5380-WJKOV   |           106.35 | Month-to-month |       34 | Electronic check          | Yes     |
| 4220-TINQT   |           106.35 | Month-to-month |       61 | Electronic check          | No      |
| 5630-IXDXV   |           106.35 | Month-to-month |       47 | Electronic check          | No      |
| 0337-CNPZE   |           106.3  | Month-to-month |       41 | Electronic check          | Yes     |
| 1548-FEHVL   |           106.2  | Month-to-month |       61 | Electronic check          | No      |
| 6377-WHAOX   |           106.15 | Month-to-month |       60 | Electronic check          | No      |
| 3957-LXOLK   |           106.15 | Month-to-month |       28 | Electronic check          | Yes     |
| 1309-BXVOQ   |           106.1  | Month-to-month |       21 | Electronic check          | Yes     |
| 5804-HYIEZ   |           106.05 | Month-to-month |       70 | Electronic check          | No      |
| 7752-XUSCI   |           105.9  | Month-to-month |       60 | Electronic check          | Yes     |
| 5647-FXOTP   |           105.9  | Month-to-month |       60 | Electronic check          | No      |
| 1400-MMYXY   |           105.9  | Month-to-month |        3 | Electronic check          | Yes     |
| 1104-TNLZA   |           105.8  | Month-to-month |       28 | Electronic check          | No      |
| 6900-PXRMS   |           105.75 | Month-to-month |       26 | Electronic check          | Yes     |
| 8868-WOZGU   |           105.7  | Month-to-month |       28 | Electronic check          | Yes     |
| 8111-SLLHI   |           105.65 | Month-to-month |       39 | Electronic check          | Yes     |
| 3932-CMDTD   |           105.65 | One year       |        4 | Electronic check          | Yes     |
| 4446-BZKHU   |           105.55 | Month-to-month |       61 | Electronic check          | Yes     |
| 5129-JLPIS   |           105.5  | Month-to-month |       25 | Electronic check          | No      |
| 7207-RMRDB   |           105.5  | Month-to-month |       65 | Electronic check          | Yes     |
| 5339-TJFEK   |           105.5  | Month-to-month |       62 | Electronic check          | No      |
| 3389-YGYAI   |           105.5  | Month-to-month |        8 | Electronic check          | Yes     |
| 4191-XOVOM   |           105.4  | Month-to-month |       63 | Electronic check          | No      |
| 5052-PNLOS   |           105.35 | Month-to-month |        3 | Bank transfer (automatic) | Yes     |
| 2697-NQBPF   |           105.35 | Month-to-month |       34 | Electronic check          | No      |
| 6734-GMPVK   |           105.3  | Month-to-month |        5 | Electronic check          | No      |
| 7145-FEJWU   |           105.3  | Month-to-month |       12 | Electronic check          | No      |
| 4587-VVTOX   |           105.3  | Month-to-month |        6 | Electronic check          | Yes     |
| 9090-SGQXL   |           105.3  | Month-to-month |       68 | Electronic check          | Yes     |
| 1469-LBJQJ   |           105.2  | Month-to-month |       66 | Electronic check          | No      |
| 9661-ACXBS   |           105.2  | Month-to-month |       42 | Electronic check          | Yes     |
| 9408-HRXRK   |           105.15 | Month-to-month |       45 | Electronic check          | No      |
| 0207-MDKNV   |           105.1  | Month-to-month |       15 | Electronic check          | Yes     |
| 2874-YXVVA   |           105.1  | Month-to-month |       34 | Electronic check          | No      |
| 4484-GLZOU   |           105.05 | Month-to-month |       52 | Electronic check          | Yes     |
| 5055-MGMGF   |           105.05 | Month-to-month |       65 | Electronic check          | No      |
| 6496-SLWHQ   |           105    | Month-to-month |        3 | Electronic check          | Yes     |
| 6518-LGAOV   |           105    | Month-to-month |       38 | Electronic check          | Yes     |
| 2786-GCDPI   |           104.95 | Month-to-month |       50 | Electronic check          | No      |
| 3001-CBHLQ   |           104.9  | Month-to-month |       32 | Electronic check          | Yes     |
| 9221-OTIVJ   |           104.85 | Month-to-month |       14 | Electronic check          | Yes     |
| 7892-POOKP   |           104.8  | Month-to-month |       28 | Electronic check          | Yes     |
| 4840-ORQXB   |           104.75 | Month-to-month |       56 | Electronic check          | No      |
| 9851-QXEEQ   |           104.7  | Month-to-month |       41 | Electronic check          | Yes     |
| 8625-AZYZY   |           104.65 | Month-to-month |       24 | Electronic check          | Yes     |
| 9927-DSWDF   |           104.6  | Month-to-month |       22 | Electronic check          | No      |
| 8552-OBVRU   |           104.5  | Month-to-month |       48 | Electronic check          | No      |
| 8818-DOPVL   |           104.45 | Month-to-month |       46 | Electronic check          | No      |
| 5995-SNNEW   |           104.45 | Month-to-month |       23 | Electronic check          | No      |
| 1875-QIVME   |           104.4  | Month-to-month |        2 | Electronic check          | Yes     |
| 5219-YIPTK   |           104.4  | Month-to-month |       33 | Electronic check          | Yes     |
| 5923-GXUOC   |           104.4  | Month-to-month |       10 | Electronic check          | Yes     |
| 2080-CAZNM   |           104.4  | Month-to-month |       41 | Electronic check          | No      |
| 0654-HMSHN   |           104.4  | Month-to-month |       21 | Electronic check          | Yes     |
| 1550-EENBN   |           104.35 | Month-to-month |       31 | Electronic check          | No      |
| 5956-YHHRX   |           104.35 | Month-to-month |       21 | Electronic check          | No      |
| 2378-VTKDH   |           104.35 | Month-to-month |       65 | Electronic check          | No      |
| 0895-DQHEW   |           104.3  | Month-to-month |       54 | Electronic check          | Yes     |
| 2360-RDGRO   |           104.25 | Month-to-month |       65 | Electronic check          | No      |
| 6892-XPFPU   |           104.25 | Month-to-month |       24 | Electronic check          | Yes     |
| 9874-QLCLH   |           104.2  | Month-to-month |       17 | Electronic check          | Yes     |
| 5385-SUIRI   |           104.2  | Month-to-month |       52 | Electronic check          | Yes     |
| 4077-CROMM   |           104.2  | Month-to-month |       31 | Electronic check          | Yes     |
| 8313-NDOIA   |           104.15 | Month-to-month |       24 | Electronic check          | No      |
| 9168-INPSZ   |           104.15 | Month-to-month |       44 | Electronic check          | No      |
| 2107-FBPTK   |           104.1  | Month-to-month |       30 | Electronic check          | No      |
| 2369-UAPKZ   |           104.1  | Month-to-month |        5 | Mailed check              | Yes     |
| 3384-CTMSF   |           104.1  | Month-to-month |       47 | Electronic check          | No      |
| 5293-WXJAK   |           104.05 | Month-to-month |       11 | Bank transfer (automatic) | Yes     |
| 5502-RLUYV   |           103.95 | Month-to-month |       69 | Electronic check          | Yes     |
| 3001-UNBTL   |           103.95 | Month-to-month |       29 | Electronic check          | No      |
| 5519-YLDGW   |           103.9  | Month-to-month |       21 | Electronic check          | Yes     |
| 2038-LLMLM   |           103.85 | Month-to-month |       48 | Electronic check          | No      |
| 6646-VRFOL   |           103.85 | Month-to-month |       53 | Electronic check          | Yes     |
| 1842-EZJMK   |           103.7  | Month-to-month |       50 | Electronic check          | Yes     |
| 2832-KJCRD   |           103.65 | Month-to-month |       38 | Electronic check          | No      |
| 1035-IPQPU   |           103.5  | Month-to-month |       63 | Electronic check          | No      |
| 4298-OYIFC   |           103.45 | Month-to-month |       15 | Electronic check          | No      |
| 9801-GDWGV   |           103.45 | Month-to-month |       39 | Electronic check          | Yes     |
| 1343-EHPYB   |           103.4  | Month-to-month |       63 | Electronic check          | Yes     |
| 7089-IVVAZ   |           103.35 | Month-to-month |        8 | Bank transfer (automatic) | Yes     |
| 2357-COQEK   |           103.3  | Month-to-month |       28 | Electronic check          | Yes     |
| 5449-FIBXJ   |           103.3  | Month-to-month |       19 | Electronic check          | Yes     |
| 2018-PZKMU   |           103.1  | Month-to-month |        9 | Electronic check          | No      |
| 4188-FRABG   |           103.05 | Month-to-month |       57 | Electronic check          | No      |
| 4062-HBMOS   |           103.05 | Month-to-month |       52 | Electronic check          | No      |
| 7142-HVGBG   |           103    | Month-to-month |       43 | Electronic check          | Yes     |
| 4550-VBOFE   |           102.95 | Month-to-month |       70 | Electronic check          | Yes     |
| 4658-HCOHW   |           102.8  | Month-to-month |       21 | Electronic check          | Yes     |
| 2439-LYPMQ   |           102.6  | Month-to-month |       38 | Electronic check          | No      |
| 9547-ITEFG   |           102.6  | Month-to-month |        9 | Credit card (automatic)   | No      |
| 0365-BZUWY   |           102.55 | Month-to-month |       17 | Electronic check          | No      |
| 7181-BQYBV   |           102.45 | Month-to-month |        1 | Electronic check          | Yes     |
| 7233-DRTRF   |           102.4  | Month-to-month |       63 | Electronic check          | No      |
| 1465-VINDH   |           102.1  | Month-to-month |       10 | Credit card (automatic)   | Yes     |
| 6688-UZPWD   |           102    | Month-to-month |       11 | Electronic check          | Yes     |
| 8884-ADFVN   |           101.95 | Month-to-month |        7 | Electronic check          | Yes     |
| 7056-IMHCC   |           101.9  | Month-to-month |       53 | Electronic check          | Yes     |
| 2474-BRUCM   |           101.85 | Month-to-month |       40 | Electronic check          | Yes     |
| 3629-ZNKXA   |           101.8  | Month-to-month |       17 | Electronic check          | No      |
| 8903-WMRNW   |           101.75 | Month-to-month |       15 | Electronic check          | No      |
| 1723-HKXJQ   |           101.75 | Month-to-month |       42 | Electronic check          | Yes     |
| 0702-PGIBZ   |           101.7  | Month-to-month |        4 | Electronic check          | Yes     |
| 5299-SJCZT   |           101.55 | Month-to-month |        3 | Bank transfer (automatic) | Yes     |
| 8118-TJAFG   |           101.5  | Month-to-month |        9 | Electronic check          | No      |
| 1028-FFNJK   |           101.5  | Month-to-month |       30 | Electronic check          | No      |
| 5419-JPRRN   |           101.45 | Month-to-month |        1 | Electronic check          | Yes     |
| 2603-HVKCG   |           101.4  | Month-to-month |       31 | Electronic check          | No      |
| 4958-XCBDQ   |           101.4  | Month-to-month |       35 | Electronic check          | Yes     |
| 9600-NAXZN   |           101.4  | Month-to-month |       43 | Electronic check          | Yes     |
| 0125-LZQXK   |           101.35 | Month-to-month |       15 | Electronic check          | Yes     |
| 3902-FOIGH   |           101.35 | Month-to-month |       12 | Electronic check          | Yes     |
| 4553-DVPZG   |           101.35 | Month-to-month |       62 | Electronic check          | No      |
| 2809-ZMYOQ   |           101.35 | Month-to-month |       32 | Electronic check          | No      |
| 7234-FECYN   |           101.35 | Month-to-month |        8 | Electronic check          | Yes     |
| 4289-DTDKW   |           101.3  | Month-to-month |       40 | Electronic check          | Yes     |
| 7748-UMTRK   |           101.3  | Month-to-month |       30 | Electronic check          | No      |
| 3663-MITLP   |           101.25 | Month-to-month |       15 | Electronic check          | Yes     |
| 4597-NUCQV   |           101.25 | Month-to-month |       24 | Electronic check          | Yes     |
| 0147-ESWWR   |           101.25 | Month-to-month |       39 | Electronic check          | No      |
| 0886-QGENL   |           101.25 | Month-to-month |       27 | Electronic check          | Yes     |
| 3167-SNQPL   |           101.15 | Month-to-month |       38 | Electronic check          | No      |
| 0880-TKATG   |           101.15 | Month-to-month |        4 | Electronic check          | Yes     |
| 0302-JOIVN   |           101.15 | Month-to-month |        8 | Electronic check          | Yes     |
| 0680-DFNNY   |           101.1  | Month-to-month |       15 | Electronic check          | Yes     |
| 6029-WTIPC   |           101.1  | Month-to-month |       37 | Electronic check          | Yes     |
| 4523-WXCEF   |           101.1  | Month-to-month |       59 | Electronic check          | Yes     |
| 7901-TBKJX   |           101.05 | Month-to-month |       56 | Electronic check          | No      |
| 2430-USGXP   |           101.05 | Month-to-month |       24 | Electronic check          | Yes     |
| 4433-JCGCG   |           101    | Month-to-month |       46 | Electronic check          | Yes     |
| 8374-XGEJJ   |           101    | Month-to-month |       43 | Electronic check          | Yes     |
| 6023-YEBUP   |           100.95 | Month-to-month |        3 | Electronic check          | Yes     |
| 6326-MTTXK   |           100.85 | Month-to-month |        8 | Electronic check          | Yes     |
| 4132-KALRO   |           100.85 | Month-to-month |        4 | Mailed check              | No      |
| 0899-LIIBW   |           100.85 | Month-to-month |       34 | Electronic check          | No      |
| 6851-WEFYX   |           100.8  | Month-to-month |       35 | Electronic check          | No      |
| 7216-EWTRS   |           100.8  | Month-to-month |        1 | Electronic check          | Yes     |
| 1013-QCWAM   |           100.8  | Month-to-month |       66 | Electronic check          | No      |
| 8510-AWCXC   |           100.8  | Month-to-month |       13 | Electronic check          | Yes     |
| 7587-AOVVU   |           100.75 | Month-to-month |       27 | Electronic check          | No      |
| 5590-BYNII   |           100.75 | Month-to-month |       22 | Electronic check          | Yes     |
| 7315-WYOAW   |           100.75 | Month-to-month |       13 | Electronic check          | No      |
| 4078-SAYYN   |           100.75 | Month-to-month |       11 | Electronic check          | Yes     |
| 7641-EUYET   |           100.7  | Month-to-month |       46 | Electronic check          | Yes     |
| 7392-YYPYJ   |           100.65 | Month-to-month |       22 | Electronic check          | No      |
| 4822-RVYBB   |           100.6  | Month-to-month |        8 | Electronic check          | Yes     |
| 8384-FZBJK   |           100.6  | Month-to-month |       57 | Electronic check          | No      |
| 2968-SSGAA   |           100.6  | Month-to-month |       10 | Electronic check          | Yes     |
| 3768-NLUBH   |           100.6  | Month-to-month |       57 | Electronic check          | Yes     |
| 7549-MYGPK   |           100.55 | Month-to-month |       63 | Electronic check          | Yes     |
| 6615-NGGZJ   |           100.55 | Month-to-month |       14 | Electronic check          | Yes     |
| 8761-NSOBC   |           100.55 | Month-to-month |       44 | Electronic check          | Yes     |
| 0434-CSFON   |           100.5  | Month-to-month |       47 | Electronic check          | No      |
| 0781-LKXBR   |           100.5  | Month-to-month |        9 | Electronic check          | Yes     |
| 9681-OXGVC   |           100.5  | Month-to-month |        5 | Electronic check          | Yes     |
| 6116-RFVHN   |           100.45 | Month-to-month |       34 | Electronic check          | No      |
| 4998-IKFSE   |           100.45 | Month-to-month |       30 | Electronic check          | No      |
| 1641-RQDAY   |           100.4  | Month-to-month |       32 | Electronic check          | No      |
| 0722-SVSFK   |           100.4  | Month-to-month |        7 | Electronic check          | No      |
| 9330-IJWIO   |           100.35 | Month-to-month |       13 | Electronic check          | Yes     |
| 9889-TMAHG   |           100.3  | Month-to-month |        8 | Credit card (automatic)   | Yes     |
| 2800-QQUSO   |           100.3  | Month-to-month |       42 | Electronic check          | No      |
| 5299-RULOA   |           100.25 | Month-to-month |       10 | Electronic check          | Yes     |
| 0939-YAPAF   |           100.25 | Month-to-month |       35 | Electronic check          | Yes     |
| 3178-FESZO   |           100.25 | Month-to-month |        1 | Credit card (automatic)   | Yes     |
| 3393-FMZPV   |           100.25 | Month-to-month |       25 | Electronic check          | Yes     |
| 2656-TABEH   |           100.2  | Month-to-month |        4 | Electronic check          | Yes     |
| 4817-VYYWS   |           100.2  | Month-to-month |       30 | Electronic check          | Yes     |
| 0324-BRPCJ   |           100.2  | Month-to-month |       68 | Electronic check          | Yes     |
| 7379-FNIUJ   |           100.2  | Month-to-month |        2 | Electronic check          | No      |
| 3621-CEOVK   |           100.2  | Month-to-month |       14 | Electronic check          | Yes     |
| 9094-AZPHK   |           100.15 | Month-to-month |       15 | Electronic check          | No      |
| 2754-SDJRD   |           100.15 | Month-to-month |        8 | Credit card (automatic)   | No      |
| 0596-BQCEQ   |           100.15 | Month-to-month |       62 | Electronic check          | Yes     |
| 2612-RANWT   |           100.15 | Month-to-month |       12 | Bank transfer (automatic) | Yes     |
| 5515-AKOAJ   |           100.1  | Month-to-month |       54 | Electronic check          | Yes     |
| 8397-MVTAZ   |           100.05 | Month-to-month |       34 | Electronic check          | Yes     |
| 1666-JXLKU   |           100.05 | Month-to-month |       37 | Electronic check          | No      |
| 9647-ERGBE   |           100.05 | Month-to-month |       30 | Electronic check          | Yes     |
| 8634-MPHTR   |           100.05 | Month-to-month |       47 | Electronic check          | Yes     |
| 3473-XIIIT   |           100    | Month-to-month |       16 | Electronic check          | Yes     |
| 8709-KRDVL   |           100    | Month-to-month |       33 | Electronic check          | No      |
| 1571-SAVHK   |            99.95 | Month-to-month |       12 | Mailed check              | Yes     |
| 1254-IZEYF   |            99.95 | Month-to-month |       31 | Electronic check          | Yes     |
| 3440-JPSCL   |            99.95 | Month-to-month |        6 | Mailed check              | Yes     |
| 5883-GTGVD   |            99.95 | Month-to-month |       19 | Electronic check          | Yes     |
| 0320-JDNQG   |            99.85 | Month-to-month |       23 | Electronic check          | Yes     |
| 8443-WVPSS   |            99.85 | Month-to-month |       10 | Electronic check          | Yes     |
| 3811-VBYBZ   |            99.8  | Month-to-month |        7 | Electronic check          | Yes     |
| 5419-CONWX   |            99.8  | Month-to-month |        4 | Credit card (automatic)   | Yes     |
| 8785-CJSHH   |            99.8  | Month-to-month |       60 | Electronic check          | No      |
| 6651-AZVTJ   |            99.8  | Month-to-month |       49 | Electronic check          | Yes     |
| 2845-AFFTX   |            99.8  | Month-to-month |       41 | Electronic check          | Yes     |
| 8631-WUXGY   |            99.8  | Month-to-month |       46 | Electronic check          | No      |
| 0107-YHINA   |            99.75 | Month-to-month |        1 | Electronic check          | Yes     |
| 0420-HLGXF   |            99.75 | Month-to-month |       39 | Electronic check          | No      |
| 7783-YKGDV   |            99.7  | Month-to-month |       12 | Bank transfer (automatic) | Yes     |
| 6543-XRMYR   |            99.7  | Month-to-month |       30 | Electronic check          | Yes     |
| 4128-ETESU   |            99.7  | Month-to-month |       47 | Electronic check          | No      |
| 6215-NQCPY   |            99.7  | Month-to-month |       15 | Electronic check          | No      |
| 9305-CDSKC   |            99.65 | Month-to-month |        8 | Electronic check          | Yes     |
| 8468-EHYJA   |            99.65 | Month-to-month |       57 | Electronic check          | No      |
| 2265-CYWIV   |            99.6  | Month-to-month |        4 | Electronic check          | Yes     |
| 4803-AXVYP   |            99.55 | Month-to-month |       38 | Electronic check          | Yes     |
| 2012-NWRPA   |            99.55 | Month-to-month |       11 | Electronic check          | Yes     |
| 2003-CKLOR   |            99.5  | Month-to-month |       66 | Electronic check          | Yes     |
| 0897-FEGMU   |            99.5  | Month-to-month |       11 | Electronic check          | Yes     |
| 2568-OIADY   |            99.5  | Month-to-month |       37 | Electronic check          | Yes     |
| 4009-ALQFH   |            99.5  | Month-to-month |       25 | Electronic check          | Yes     |
| 6210-KBBPI   |            99.45 | Month-to-month |        9 | Credit card (automatic)   | Yes     |
| 7450-NWRTR   |            99.45 | Month-to-month |       12 | Electronic check          | Yes     |
| 8019-ENHXU   |            99.45 | Month-to-month |       42 | Electronic check          | Yes     |
| 7780-OTDSO   |            99.4  | Month-to-month |       18 | Electronic check          | Yes     |
| 9732-EQMWY   |            99.4  | Month-to-month |       49 | Electronic check          | No      |
| 6467-CHFZW   |            99.35 | Month-to-month |       47 | Electronic check          | Yes     |
| 4445-ZJNMU   |            99.3  | Month-to-month |        9 | Credit card (automatic)   | No      |
| 6861-XWTWQ   |            99.25 | Month-to-month |        7 | Electronic check          | Yes     |
| 3934-HXCFZ   |            99.25 | Month-to-month |       23 | Electronic check          | Yes     |
| 0310-MVLET   |            99.15 | Month-to-month |       61 | Electronic check          | Yes     |
| 4236-XPXAV   |            99.15 | Month-to-month |        5 | Mailed check              | Yes     |
| 6907-NZZIJ   |            99.15 | Month-to-month |       36 | Electronic check          | Yes     |
| 7028-DVOIQ   |            99.05 | Month-to-month |       35 | Electronic check          | Yes     |
| 3588-WSTTJ   |            99.05 | Month-to-month |       35 | Electronic check          | No      |
| 2277-DJJDL   |            99    | Month-to-month |       60 | Electronic check          | No      |
| 5649-RXQTV   |            99    | Month-to-month |       51 | Electronic check          | No      |
| 6956-SMUCM   |            99    | Month-to-month |        3 | Credit card (automatic)   | Yes     |
| 4315-MURBD   |            98.9  | Month-to-month |       12 | Bank transfer (automatic) | Yes     |
| 0354-WYROK   |            98.9  | Month-to-month |       31 | Electronic check          | Yes     |
| 2675-DHUTR   |            98.9  | Month-to-month |       58 | Electronic check          | No      |
| 3587-PMCOY   |            98.9  | One year       |       10 | Electronic check          | No      |
| 1751-NCDLI   |            98.85 | Month-to-month |       46 | Electronic check          | No      |
| 6088-BXMRG   |            98.85 | Month-to-month |       32 | Electronic check          | No      |
| 3005-NFMTA   |            98.8  | Month-to-month |       55 | Electronic check          | Yes     |
| 7079-QRCBC   |            98.75 | Month-to-month |       24 | Electronic check          | Yes     |
| 6845-RGTYS   |            98.75 | Month-to-month |       47 | Electronic check          | Yes     |
| 1075-BGWOH   |            98.75 | Month-to-month |       16 | Electronic check          | Yes     |
| 9172-ANCRX   |            98.7  | Month-to-month |       10 | Electronic check          | Yes     |
| 7938-OUHIO   |            98.7  | Month-to-month |        3 | Electronic check          | Yes     |
| 6988-CJEYV   |            98.7  | Month-to-month |       49 | Electronic check          | No      |
| 0946-CLJTI   |            98.7  | Month-to-month |       58 | Electronic check          | Yes     |
| 1427-VERSM   |            98.7  | Month-to-month |       56 | Electronic check          | No      |
| 4902-OHLSK   |            98.65 | Month-to-month |       29 | Electronic check          | Yes     |
| 6559-PDZLR   |            98.65 | Month-to-month |       26 | Electronic check          | No      |
| 2208-UGTGR   |            98.6  | Month-to-month |       56 | Electronic check          | No      |
| 5138-WVKYJ   |            98.55 | Month-to-month |       10 | Electronic check          | Yes     |
| 6683-VLCTZ   |            98.55 | Month-to-month |       20 | Electronic check          | Yes     |
| 4598-XLKNJ   |            98.5  | Month-to-month |       25 | Electronic check          | Yes     |
| 1450-GALXR   |            98.5  | Month-to-month |       10 | Electronic check          | Yes     |
| 4021-RQSNY   |            98.5  | Month-to-month |       29 | Electronic check          | Yes     |
| 1455-UGQVH   |            98.5  | Month-to-month |       10 | Electronic check          | Yes     |
| 1866-RZZQS   |            98.4  | Month-to-month |       41 | Electronic check          | Yes     |
| 4735-ASGMA   |            98.35 | Month-to-month |       26 | Electronic check          | Yes     |
| 3545-CNWRG   |            98.35 | Month-to-month |       49 | Electronic check          | No      |
| 9734-YWGEX   |            98.3  | Month-to-month |        9 | Credit card (automatic)   | Yes     |
| 2446-BEGGB   |            98.25 | Month-to-month |        6 | Electronic check          | Yes     |
| 2506-CLAKW   |            98.15 | Month-to-month |        6 | Bank transfer (automatic) | Yes     |
| 7295-JOMMD   |            98.1  | Month-to-month |        4 | Bank transfer (automatic) | Yes     |
| 2454-RPBRZ   |            98.1  | Month-to-month |       12 | Electronic check          | Yes     |
| 0655-RBDUG   |            98.05 | Month-to-month |        7 | Bank transfer (automatic) | Yes     |
| 0011-IGKFF   |            98    | Month-to-month |       13 | Electronic check          | Yes     |
| 6108-OQZDQ   |            97.95 | Month-to-month |        4 | Electronic check          | Yes     |
| 0329-GTIAJ   |            97.9  | Month-to-month |        3 | Electronic check          | Yes     |
| 8168-UQWWF   |            97.85 | Month-to-month |       11 | Bank transfer (automatic) | Yes     |
| 8276-MQBYC   |            97.8  | Month-to-month |       51 | Electronic check          | Yes     |
| 6393-WRYZE   |            97.65 | Month-to-month |       34 | Electronic check          | Yes     |
| 7969-AULMZ   |            97.35 | Month-to-month |       21 | Electronic check          | Yes     |
| 6645-MXQJT   |            97.1  | Month-to-month |        2 | Electronic check          | No      |
| 3898-GUYTS   |            97.05 | Month-to-month |       45 | Electronic check          | No      |
| 3644-QXEHN   |            97    | Month-to-month |       13 | Electronic check          | No      |
| 9290-SHCMB   |            96.85 | Month-to-month |       13 | Electronic check          | No      |
| 4007-NHVHI   |            96.85 | Month-to-month |       56 | Electronic check          | No      |
| 1264-BYWMS   |            96.8  | Month-to-month |       55 | Electronic check          | Yes     |
| 0480-BIXDE   |            96.8  | Month-to-month |       19 | Electronic check          | No      |
| 0486-HECZI   |            96.75 | Month-to-month |       55 | Electronic check          | Yes     |
| 9809-IMGCQ   |            96.7  | Month-to-month |       22 | Electronic check          | Yes     |
| 6821-BUXUX   |            96.65 | Month-to-month |       13 | Electronic check          | Yes     |
| 9057-SIHCH   |            96.6  | Month-to-month |        3 | Electronic check          | Yes     |
| 2604-IJPDU   |            96.55 | Month-to-month |       20 | Electronic check          | No      |
| 6899-PPEEA   |            96.55 | Month-to-month |       37 | Electronic check          | Yes     |
| 4566-NECEV   |            96.55 | Month-to-month |        5 | Electronic check          | No      |
| 1010-DIAUQ   |            96.5  | Month-to-month |        5 | Bank transfer (automatic) | Yes     |
| 4039-HEUNW   |            96.5  | Month-to-month |       36 | Electronic check          | Yes     |
| 5937-EORGB   |            96.5  | Month-to-month |       15 | Electronic check          | No      |
| 8245-UMPYT   |            96.4  | Month-to-month |       16 | Electronic check          | Yes     |
| 9508-ILZDG   |            96.35 | Month-to-month |       34 | Electronic check          | No      |
| 7548-SEPYI   |            96.25 | Month-to-month |        5 | Electronic check          | Yes     |
| 0963-ZBDRN   |            96.2  | Month-to-month |       32 | Electronic check          | Yes     |
| 5655-JSMZM   |            96.2  | Month-to-month |       49 | Electronic check          | Yes     |
| 3737-GCSPV   |            96.2  | Month-to-month |       11 | Credit card (automatic)   | Yes     |
| 4060-LDNLU   |            96.2  | Month-to-month |        7 | Electronic check          | No      |
| 5565-FILXA   |            96.15 | Month-to-month |       16 | Electronic check          | Yes     |
| 0306-JAELE   |            96.1  | Month-to-month |        5 | Electronic check          | Yes     |
| 5980-NOPLP   |            96.1  | Month-to-month |       44 | Electronic check          | Yes     |
| 7526-BEZQB   |            96.05 | Month-to-month |       12 | Electronic check          | Yes     |
| 9692-TUSXH   |            96.05 | Month-to-month |       18 | Electronic check          | Yes     |
| 3158-MOERK   |            96    | Month-to-month |        2 | Electronic check          | Yes     |
| 6365-MTGZX   |            96    | Month-to-month |       24 | Electronic check          | Yes     |
| 2180-DXNEG   |            96    | Month-to-month |       12 | Electronic check          | Yes     |
| 7426-RHZGU   |            95.9  | Month-to-month |        9 | Bank transfer (automatic) | No      |
| 8393-DLHGA   |            95.9  | Month-to-month |       25 | Electronic check          | Yes     |
| 1771-OADNZ   |            95.9  | Month-to-month |       29 | Electronic check          | Yes     |
| 4989-LIXVT   |            95.9  | Month-to-month |       68 | Electronic check          | No      |
| 1393-IMKZG   |            95.85 | Month-to-month |        1 | Electronic check          | No      |
| 0754-UKWQP   |            95.85 | Month-to-month |        2 | Electronic check          | Yes     |
| 0916-QOFDP   |            95.8  | Month-to-month |       14 | Electronic check          | No      |
| 0407-BDJKB   |            95.75 | Month-to-month |       60 | Electronic check          | Yes     |
| 3319-DWOEP   |            95.75 | Month-to-month |        6 | Electronic check          | Yes     |
| 8272-ONJLV   |            95.7  | One year       |       12 | Electronic check          | No      |
| 6212-ATMLK   |            95.7  | Month-to-month |       50 | Electronic check          | No      |
| 7480-QNVZJ   |            95.7  | Month-to-month |       50 | Electronic check          | Yes     |
| 2507-QZPQS   |            95.7  | Month-to-month |       15 | Electronic check          | No      |
| 6857-VWJDT   |            95.65 | Month-to-month |        1 | Mailed check              | Yes     |
| 8413-VONUO   |            95.65 | Month-to-month |        2 | Electronic check          | Yes     |
| 3585-ISXZP   |            95.65 | Month-to-month |        8 | Bank transfer (automatic) | Yes     |
| 3643-AHCFP   |            95.6  | Month-to-month |        7 | Bank transfer (automatic) | Yes     |
| 6356-ELRKD   |            95.6  | Month-to-month |        1 | Electronic check          | Yes     |
| 3320-VEOYC   |            95.6  | Month-to-month |       14 | Electronic check          | No      |
| 8610-WFCJF   |            95.6  | Month-to-month |       49 | Electronic check          | Yes     |
| 0576-WNXXC   |            95.55 | Month-to-month |       27 | Electronic check          | Yes     |
| 4690-PKDQG   |            95.55 | Month-to-month |       42 | Electronic check          | No      |
| 4929-XIHVW   |            95.5  | Month-to-month |        2 | Credit card (automatic)   | No      |
| 5302-BDJNT   |            95.5  | Month-to-month |       35 | Electronic check          | No      |
| 0564-JJHGS   |            95.5  | Month-to-month |        9 | Electronic check          | Yes     |
| 1658-BYGOY   |            95.45 | Month-to-month |       18 | Electronic check          | Yes     |
| 8098-LLAZX   |            95.45 | Month-to-month |        4 | Electronic check          | Yes     |
| 3318-OSATS   |            95.45 | Month-to-month |       35 | Electronic check          | Yes     |
| 0295-PPHDO   |            95.45 | Month-to-month |        1 | Electronic check          | Yes     |
| 2984-AFWNC   |            95.4  | Month-to-month |        3 | Electronic check          | No      |
| 0396-YCHWO   |            95.4  | Month-to-month |       36 | Electronic check          | No      |
| 4724-WXVWF   |            95.4  | Month-to-month |       48 | Electronic check          | No      |
| 8357-EQXFO   |            95.35 | Month-to-month |        7 | Electronic check          | Yes     |
| 2660-EMUBI   |            95.35 | Month-to-month |       10 | Electronic check          | Yes     |
| 2386-OWURY   |            95.3  | Month-to-month |       58 | Electronic check          | No      |
| 1960-UYCNN   |            95.25 | Month-to-month |       10 | Electronic check          | No      |
| 9061-TIHDA   |            95.25 | Month-to-month |       13 | Electronic check          | Yes     |
| 2824-MYYBN   |            95.25 | Month-to-month |       37 | Electronic check          | No      |
| 3049-SOLAY   |            95.2  | Month-to-month |        3 | Electronic check          | Yes     |
| 2754-VDLTR   |            95.2  | Month-to-month |       10 | Electronic check          | Yes     |
| 3003-CMDUU   |            95.15 | Month-to-month |       25 | Electronic check          | No      |
| 7851-WZEKY   |            95.15 | Month-to-month |        2 | Electronic check          | Yes     |
| 4659-NZRUF   |            95.15 | Month-to-month |       19 | Electronic check          | Yes     |
| 5982-FPVQN   |            95.15 | Month-to-month |       37 | Electronic check          | No      |
| 6328-ZPBGN   |            95.15 | Month-to-month |       11 | Bank transfer (automatic) | Yes     |
| 5183-SNMJQ   |            95.1  | Month-to-month |       10 | Credit card (automatic)   | No      |
| 9944-HKVVB   |            95.1  | Month-to-month |        3 | Electronic check          | Yes     |
| 5382-SOYZL   |            95.1  | Month-to-month |       22 | Electronic check          | No      |
| 6242-MBHPK   |            95.1  | Month-to-month |       23 | Electronic check          | No      |
| 5649-ANRML   |            95.1  | Month-to-month |        2 | Credit card (automatic)   | Yes     |
| 5178-LMXOP   |            95.1  | Month-to-month |        1 | Electronic check          | Yes     |
| 3951-NJCVI   |            95.05 | Month-to-month |       42 | Electronic check          | No      |
| 3793-MMFUH   |            95.05 | Month-to-month |       13 | Electronic check          | Yes     |
| 5889-JTMUL   |            95.05 | Month-to-month |       50 | Electronic check          | Yes     |
| 1095-JUDTC   |            95.05 | Month-to-month |       47 | Electronic check          | Yes     |
| 3874-EQOEP   |            95    | Month-to-month |        7 | Mailed check              | Yes     |
| 0094-OIFMO   |            95    | Month-to-month |       11 | Electronic check          | Yes     |
| 0684-AOSIH   |            95    | Month-to-month |        1 | Electronic check          | Yes     |
| 1597-LHYNC   |            95    | Month-to-month |       26 | Electronic check          | Yes     |
| 3452-GWUIN   |            94.95 | Month-to-month |       19 | Electronic check          | No      |
| 5349-IECLD   |            94.95 | Month-to-month |        2 | Electronic check          | Yes     |
| 7398-SKNQZ   |            94.9  | Month-to-month |        3 | Electronic check          | No      |
| 7209-JCUDS   |            94.9  | Month-to-month |       10 | Electronic check          | Yes     |
| 9714-EDSUC   |            94.9  | Month-to-month |        4 | Mailed check              | No      |
| 3387-VATUS   |            94.85 | Month-to-month |        5 | Bank transfer (automatic) | Yes     |
| 5150-ITWWB   |            94.85 | Month-to-month |        3 | Electronic check          | No      |
| 3045-XETSH   |            94.85 | Month-to-month |       10 | Electronic check          | Yes     |
| 2344-JMOGN   |            94.85 | Month-to-month |        9 | Mailed check              | Yes     |
| 7225-CBZPL   |            94.8  | Month-to-month |       17 | Electronic check          | No      |
| 5168-MSWXT   |            94.75 | Month-to-month |        8 | Electronic check          | No      |
| 7943-RQCHR   |            94.75 | Month-to-month |        9 | Electronic check          | Yes     |
| 8017-LXHFA   |            94.75 | Month-to-month |       23 | Electronic check          | Yes     |
| 5144-TVGLP   |            94.75 | Month-to-month |       38 | Electronic check          | No      |
| 6350-XFYGW   |            94.75 | Month-to-month |        4 | Electronic check          | No      |
| 0060-FUALY   |            94.75 | Month-to-month |       59 | Electronic check          | No      |
| 3096-GKWEB   |            94.75 | Month-to-month |       18 | Electronic check          | No      |
| 5955-ERIHD   |            94.7  | Month-to-month |       18 | Electronic check          | Yes     |
| 0325-XBFAC   |            94.7  | Month-to-month |        8 | Electronic check          | Yes     |
| 6502-HCJTI   |            94.7  | Month-to-month |        7 | Credit card (automatic)   | Yes     |
| 1472-TNCWL   |            94.7  | Month-to-month |       36 | Electronic check          | No      |
| 5364-XYIRR   |            94.65 | Month-to-month |       51 | Electronic check          | Yes     |
| 2037-SGXHH   |            94.65 | Month-to-month |       38 | Electronic check          | Yes     |
| 0129-KPTWJ   |            94.65 | Month-to-month |       72 | Electronic check          | No      |
| 6583-KQJLK   |            94.65 | Month-to-month |       15 | Electronic check          | No      |
| 4910-GMJOT   |            94.6  | Month-to-month |        1 | Electronic check          | Yes     |
| 9058-MJLZC   |            94.6  | Month-to-month |       24 | Electronic check          | No      |
| 5567-WSELE   |            94.6  | Month-to-month |        3 | Electronic check          | Yes     |
| 6522-YRBXD   |            94.55 | Month-to-month |       35 | Electronic check          | No      |
| 1626-ERCMM   |            94.55 | Month-to-month |       20 | Electronic check          | Yes     |
| 5439-WIKXB   |            94.55 | Month-to-month |       41 | Electronic check          | No      |
| 3338-CVVEH   |            94.55 | Month-to-month |       12 | Electronic check          | No      |
| 5244-IRFIH   |            94.5  | Month-to-month |       33 | Electronic check          | Yes     |
| 5899-OUVKV   |            94.5  | Month-to-month |       31 | Electronic check          | No      |
| 9699-UBQFS   |            94.5  | Month-to-month |       43 | Electronic check          | No      |
| 6101-IMRMM   |            94.5  | Month-to-month |        6 | Mailed check              | Yes     |
| 4385-GZQXV   |            94.45 | Month-to-month |       16 | Electronic check          | Yes     |
| 3143-ILDAL   |            94.45 | Month-to-month |       56 | Electronic check          | Yes     |
| 3217-FZDMN   |            94.45 | Month-to-month |        8 | Credit card (automatic)   | Yes     |
| 4192-GORJT   |            94.45 | Month-to-month |        5 | Electronic check          | Yes     |
| 9253-QXKBE   |            94.45 | Month-to-month |       29 | Electronic check          | Yes     |
| 5698-BQJOH   |            94.4  | Month-to-month |        9 | Electronic check          | Yes     |
| 9058-HRZSV   |            94.4  | Month-to-month |       65 | Electronic check          | No      |
| 9763-PDTKK   |            94.4  | Month-to-month |        4 | Bank transfer (automatic) | Yes     |
| 2979-SXESE   |            94.4  | Month-to-month |       17 | Electronic check          | Yes     |
| 9658-WYUFB   |            94.4  | Month-to-month |       17 | Electronic check          | Yes     |
| 9574-RKJIF   |            94.4  | Month-to-month |       30 | Electronic check          | Yes     |
| 2347-WKKAE   |            94.4  | Month-to-month |       42 | Electronic check          | No      |
| 9223-UCPVT   |            94.4  | Month-to-month |        1 | Electronic check          | Yes     |
| 1374-DMZUI   |            94.3  | Month-to-month |        4 | Electronic check          | Yes     |
| 5461-QKNTN   |            94.3  | Month-to-month |       43 | Electronic check          | No      |
| 9919-KNPOO   |            94.3  | Month-to-month |       21 | Electronic check          | No      |
| 8621-MNIHH   |            94.25 | Month-to-month |       34 | Electronic check          | Yes     |
| 1728-CXQBE   |            94.25 | Month-to-month |       64 | Electronic check          | No      |
| 4094-NSEDU   |            94.25 | Month-to-month |       21 | Electronic check          | Yes     |
| 2645-QTLMB   |            94.25 | Month-to-month |        7 | Electronic check          | Yes     |
| 8063-RJYNF   |            94.25 | Month-to-month |       16 | Electronic check          | Yes     |
| 7218-HKQFK   |            94.2  | Month-to-month |        2 | Electronic check          | Yes     |
| 5935-FCCNB   |            94.2  | Month-to-month |       17 | Electronic check          | No      |
| 2929-ERCFZ   |            94.2  | Month-to-month |        8 | Electronic check          | Yes     |
| 9093-FPDLG   |            94.2  | Month-to-month |       11 | Electronic check          | No      |
| 5519-NPHVG   |            94.2  | Month-to-month |       12 | Electronic check          | Yes     |
| 0082-OQIQY   |            94.2  | Month-to-month |       29 | Electronic check          | No      |
| 3006-XIMLN   |            94.2  | Month-to-month |        2 | Bank transfer (automatic) | Yes     |
| 8708-XPXHZ   |            94.2  | Month-to-month |       42 | Electronic check          | Yes     |
| 5609-CEBID   |            94.1  | Month-to-month |       20 | Electronic check          | Yes     |
| 4760-THGOT   |            94.1  | Month-to-month |       43 | Electronic check          | No      |
| 8161-QYMTT   |            94.1  | Month-to-month |        7 | Electronic check          | No      |
| 9360-OMDZZ   |            94.1  | Month-to-month |       24 | Electronic check          | No      |
| 0023-XUOPT   |            94.1  | Month-to-month |       13 | Electronic check          | Yes     |
| 8087-LGYHQ   |            94.05 | Month-to-month |        9 | Electronic check          | No      |
| 6137-NICCO   |            94.05 | Month-to-month |        6 | Mailed check              | No      |
| 1567-DSCIC   |            94    | Month-to-month |        8 | Electronic check          | Yes     |
| 9300-AGZNL   |            94    | Month-to-month |        1 | Electronic check          | Yes     |
| 2982-VPSGI   |            94    | Month-to-month |       11 | Electronic check          | Yes     |
| 2720-WGKHP   |            94    | Month-to-month |        2 | Electronic check          | Yes     |
| 4307-KTUMW   |            93.9  | Month-to-month |       53 | Electronic check          | Yes     |
| 5380-AFSSK   |            93.9  | Month-to-month |        5 | Mailed check              | Yes     |
| 2719-BDAQO   |            93.85 | Month-to-month |       17 | Electronic check          | Yes     |
| 7024-OHCCK   |            93.85 | Month-to-month |        2 | Electronic check          | Yes     |
| 4626-GYCZP   |            93.85 | Month-to-month |        7 | Electronic check          | Yes     |
| 8149-RSOUN   |            93.85 | Month-to-month |        1 | Electronic check          | Yes     |
| 4424-TKOPW   |            93.85 | Month-to-month |        2 | Electronic check          | Yes     |
| 9912-GVSEQ   |            93.85 | Month-to-month |       26 | Electronic check          | Yes     |
| 3062-ICYZQ   |            93.8  | Month-to-month |       51 | Electronic check          | No      |
| 8914-RBTSB   |            93.8  | Month-to-month |       31 | Electronic check          | Yes     |
| 8178-EYZUO   |            93.7  | Month-to-month |       46 | Electronic check          | Yes     |
| 7402-EYFXX   |            93.6  | Month-to-month |       26 | Electronic check          | No      |
| 0376-OIWME   |            93.6  | Month-to-month |       36 | Electronic check          | No      |
| 9497-QCMMS   |            93.55 | Month-to-month |        1 | Electronic check          | Yes     |
| 9025-AOMKI   |            93.55 | Month-to-month |        6 | Bank transfer (automatic) | Yes     |
| 9189-JWSHV   |            93.55 | Month-to-month |       24 | Electronic check          | Yes     |
| 0674-DGMAQ   |            93.5  | Month-to-month |       32 | Electronic check          | No      |
| 1731-TVIUK   |            93.5  | Month-to-month |        4 | Electronic check          | Yes     |
| 2985-FMWYF   |            93.5  | Month-to-month |       23 | Electronic check          | No      |
| 0236-HFWSV   |            93.35 | Month-to-month |       15 | Electronic check          | Yes     |
| 7422-WNBTY   |            93.35 | Month-to-month |       33 | Electronic check          | No      |
| 6300-BWMJX   |            93.35 | Month-to-month |       59 | Electronic check          | No      |
| 6521-YYTYI   |            93.3  | Month-to-month |        1 | Electronic check          | Yes     |
| 4250-WAROZ   |            93.25 | Month-to-month |       60 | Electronic check          | No      |
| 8290-YWKHZ   |            93.2  | Month-to-month |       32 | Electronic check          | Yes     |
| 2840-XANRC   |            93.15 | Month-to-month |       24 | Electronic check          | Yes     |
| 5141-ZUVBH   |            93    | Month-to-month |        9 | Bank transfer (automatic) | No      |
| 2371-JQHZZ   |            93    | Month-to-month |       24 | Electronic check          | No      |
| 7483-IQWIB   |            92.95 | Month-to-month |       37 | Electronic check          | No      |
| 6986-IXNDM   |            92.9  | Month-to-month |       14 | Electronic check          | No      |
| 1930-WNXSB   |            92.85 | Month-to-month |       58 | Electronic check          | No      |
| 6198-RTPMF   |            92.6  | Month-to-month |       17 | Electronic check          | No      |
| 6100-QQHEB   |            92.55 | Month-to-month |       17 | Electronic check          | Yes     |
| 3162-ZJZFU   |            92.55 | Month-to-month |       53 | Electronic check          | No      |
| 7668-XCFYV   |            92.55 | Month-to-month |       17 | Electronic check          | No      |
| 2462-XIIJB   |            92.5  | Month-to-month |        5 | Electronic check          | Yes     |
| 5747-PMBSQ   |            92.5  | Month-to-month |       10 | Mailed check              | Yes     |
| 3990-QYKBE   |            92.5  | Month-to-month |       37 | Electronic check          | Yes     |
| 4879-GZLFH   |            92.15 | Month-to-month |       42 | Electronic check          | No      |
| 4145-UQXUQ   |            92.1  | Month-to-month |        8 | Electronic check          | Yes     |
| 3318-NMQXL   |            92    | Month-to-month |        3 | Electronic check          | No      |
| 5442-UTCVD   |            91.85 | Month-to-month |        3 | Electronic check          | Yes     |
| 4558-FANTW   |            91.85 | Month-to-month |       17 | Electronic check          | Yes     |
| 0595-ITUDF   |            91.8  | Month-to-month |       64 | Electronic check          | No      |
| 9940-HPQPG   |            91.75 | Month-to-month |        9 | Bank transfer (automatic) | Yes     |
| 3186-BAXNB   |            91.7  | Month-to-month |        1 | Electronic check          | Yes     |
| 5712-AHQNN   |            91.65 | Month-to-month |       43 | Electronic check          | No      |
| 6892-EZDTG   |            91.65 | Month-to-month |        4 | Electronic check          | Yes     |
| 6692-UDPJC   |            91.65 | Month-to-month |       14 | Electronic check          | Yes     |
| 0093-EXYQL   |            91.55 | Month-to-month |       40 | Electronic check          | No      |
| 4001-TSBTV   |            91.55 | Month-to-month |       58 | Electronic check          | No      |
| 4583-PARNH   |            91.55 | Month-to-month |       16 | Electronic check          | No      |
| 9402-ORRAH   |            91.5  | Month-to-month |       15 | Electronic check          | No      |
| 5095-AESKG   |            91.5  | Month-to-month |        3 | Credit card (automatic)   | Yes     |
| 4927-WWOOZ   |            91.45 | Month-to-month |        2 | Electronic check          | No      |
| 9546-CQJSU   |            91.4  | Month-to-month |        2 | Electronic check          | Yes     |
| 8414-MYSHR   |            91.4  | Month-to-month |        5 | Electronic check          | Yes     |
| 3988-RQIXO   |            91.3  | Month-to-month |        1 | Electronic check          | Yes     |
| 3398-FSHON   |            91.3  | Month-to-month |       12 | Electronic check          | Yes     |
| 6712-OAWRH   |            91.25 | Month-to-month |       26 | Electronic check          | Yes     |
| 8849-AYPTR   |            91.25 | Month-to-month |       33 | Electronic check          | No      |
| 5091-HFAZW   |            91.15 | Month-to-month |        2 | Electronic check          | No      |
| 9576-SYUHJ   |            91.15 | Month-to-month |       37 | Electronic check          | No      |
| 8714-EUHJO   |            91.15 | Month-to-month |       31 | Electronic check          | Yes     |
| 2672-HUYVI   |            91.1  | Month-to-month |        6 | Electronic check          | Yes     |
| 6818-DJXAA   |            91.1  | Month-to-month |       10 | Electronic check          | No      |
| 1195-OIYEJ   |            91.1  | Month-to-month |       13 | Electronic check          | Yes     |
| 5222-IMUKT   |            91.05 | Month-to-month |       32 | Electronic check          | No      |
| 1389-CXMLU   |            91.05 | Month-to-month |        3 | Electronic check          | Yes     |
| 2472-OVKUP   |            91    | Month-to-month |        6 | Electronic check          | Yes     |
| 1379-FRVEB   |            91    | Month-to-month |       15 | Electronic check          | No      |
| 5213-TWWJU   |            91    | Month-to-month |       28 | Electronic check          | No      |
| 8189-XRIKE   |            90.95 | Month-to-month |       32 | Electronic check          | No      |
| 5167-ZFFMM   |            90.85 | Month-to-month |        1 | Credit card (automatic)   | Yes     |
| 2988-GBIVW   |            90.85 | Month-to-month |       70 | Electronic check          | No      |
| 5281-BUZGT   |            90.85 | Month-to-month |       36 | Electronic check          | Yes     |
| 9725-SCPZG   |            90.85 | Month-to-month |        1 | Electronic check          | Yes     |
| 8189-HBVRW   |            90.8  | Month-to-month |       53 | Electronic check          | No      |
| 9172-JITSM   |            90.8  | Month-to-month |       26 | Electronic check          | Yes     |
| 7330-WZLNC   |            90.8  | Month-to-month |        5 | Electronic check          | Yes     |
| 1891-UAWWU   |            90.8  | Month-to-month |       20 | Electronic check          | Yes     |
| 9846-GKXAS   |            90.8  | Month-to-month |        9 | Bank transfer (automatic) | Yes     |
| 4137-BTIKL   |            90.75 | Month-to-month |        2 | Mailed check              | No      |
| 8622-ZLFKO   |            90.75 | Month-to-month |        6 | Electronic check          | No      |
| 2725-KXXWT   |            90.75 | Month-to-month |        1 | Electronic check          | Yes     |
| 5692-ICXLW   |            90.7  | Month-to-month |       31 | Electronic check          | No      |
| 9281-OFDMF   |            90.7  | Month-to-month |       39 | Electronic check          | No      |
| 0432-CAJZV   |            90.7  | Month-to-month |        3 | Mailed check              | No      |
| 0577-WHMEV   |            90.7  | Month-to-month |       16 | Electronic check          | No      |
| 6908-VVYHM   |            90.65 | Month-to-month |       65 | Electronic check          | No      |
| 2495-KZNFB   |            90.65 | Month-to-month |       33 | Electronic check          | No      |
| 5339-PXDVH   |            90.65 | Month-to-month |        4 | Electronic check          | No      |
| 0376-YMCJC   |            90.6  | Month-to-month |       23 | Electronic check          | Yes     |
| 7928-VJYAB   |            90.6  | Month-to-month |       11 | Electronic check          | No      |
| 5797-APWZC   |            90.6  | Month-to-month |        1 | Electronic check          | Yes     |
| 4325-NFSKC   |            90.6  | Month-to-month |       19 | Electronic check          | Yes     |
| 8775-LHDJH   |            90.6  | Month-to-month |        1 | Electronic check          | Yes     |
| 7294-TMAOP   |            90.55 | Month-to-month |        1 | Electronic check          | Yes     |
| 7274-RTAPZ   |            90.55 | Month-to-month |        1 | Electronic check          | Yes     |
| 1020-JPQOW   |            90.55 | Month-to-month |       56 | Electronic check          | No      |
| 7156-MHUGY   |            90.5  | Month-to-month |       13 | Electronic check          | Yes     |
| 1579-KLYDT   |            90.45 | Month-to-month |        7 | Electronic check          | Yes     |
| 6507-ZJSUR   |            90.45 | Month-to-month |       23 | Electronic check          | No      |
| 4918-FYJNT   |            90.45 | Month-to-month |       55 | Electronic check          | No      |
| 8266-VBFQL   |            90.4  | Month-to-month |        4 | Electronic check          | No      |
| 2034-GDRCN   |            90.4  | Month-to-month |        2 | Electronic check          | Yes     |
| 0258-NOKBL   |            90.4  | Month-to-month |        3 | Electronic check          | No      |
| 0139-IVFJG   |            90.35 | Month-to-month |        2 | Electronic check          | No      |
| 9469-WEJBT   |            90.35 | Month-to-month |       37 | Electronic check          | No      |
| 4873-ILOLJ   |            90.35 | Month-to-month |       24 | Electronic check          | Yes     |
| 2252-ISRNH   |            90.35 | One year       |        9 | Electronic check          | No      |
| 8212-DJRCH   |            90.35 | Month-to-month |        5 | Mailed check              | No      |
| 8012-SOUDQ   |            90.25 | Month-to-month |       43 | Electronic check          | No      |
| 6032-KRXXO   |            90.25 | Month-to-month |       30 | Electronic check          | Yes     |
| 4813-HQMGZ   |            90.25 | Month-to-month |        8 | Electronic check          | No      |
| 6319-IEJWJ   |            90.2  | Month-to-month |       20 | Electronic check          | Yes     |
| 7321-PKUYW   |            90.15 | Month-to-month |       11 | Electronic check          | Yes     |
| 9524-EGPJC   |            90.1  | Month-to-month |       18 | Electronic check          | Yes     |
| 8780-IXSTS   |            90.1  | Month-to-month |        6 | Electronic check          | Yes     |
| 1941-HOSAM   |            90.1  | Month-to-month |        1 | Electronic check          | No      |
| 6969-MVBAI   |            90.1  | Month-to-month |        9 | Electronic check          | No      |
| 4183-MYFRB   |            90.05 | Month-to-month |       21 | Electronic check          | No      |
| 6267-DCFFZ   |            90.05 | Month-to-month |       30 | Electronic check          | No      |
| 8058-DMYRU   |            90.05 | Month-to-month |       54 | Electronic check          | No      |
| 4228-ZGYUW   |            90.05 | Month-to-month |        4 | Electronic check          | Yes     |
| 3154-CFSZG   |            90.05 | Month-to-month |       47 | Electronic check          | No      |
| 3703-VAVCL   |            90    | Month-to-month |        2 | Credit card (automatic)   | Yes     |
| 2207-QPJED   |            90    | Month-to-month |       37 | Electronic check          | No      |
| 7270-BDIOA   |            90    | Month-to-month |       22 | Electronic check          | Yes     |
| 2322-VCZHZ   |            90    | Month-to-month |       23 | Electronic check          | No      |
| 9436-ZBZCT   |            89.95 | Month-to-month |       14 | Electronic check          | Yes     |
| 1302-UHBDD   |            89.95 | Month-to-month |       20 | Electronic check          | No      |
| 8182-BJDSI   |            89.95 | Month-to-month |       28 | Electronic check          | Yes     |
| 1891-FZYSA   |            89.95 | Month-to-month |       69 | Electronic check          | Yes     |
| 3027-ZTDHO   |            89.9  | Month-to-month |        1 | Electronic check          | Yes     |
| 3640-PHQXK   |            89.9  | Month-to-month |       31 | Electronic check          | Yes     |
| 3071-VBYPO   |            89.85 | Month-to-month |        3 | Electronic check          | No      |
| 7529-ZDFXI   |            89.85 | Month-to-month |       57 | Electronic check          | No      |
