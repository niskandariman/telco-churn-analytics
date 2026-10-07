# Power BI Dashboard Specification

This repository does **not** contain a `.pbix` file: PBIX is a proprietary binary
format that cannot be generated legitimately outside Power BI Desktop. Instead
this folder contains everything needed to build the dashboard in Power BI
Desktop in ~30 minutes: clean CSV datasets, KPI definitions, a data model, and
page-by-page instructions.

## Provided datasets (all CSV, UTF-8, Power BI-ready)

| File | Grain | Key columns |
|---|---|---|
| `risk_scores.csv` | one row per customer (7,043) | customerID, Contract, tenure, PaymentMethod, InternetService, MonthlyCharges, TotalCharges, Churn, churn_probability, risk_level, value_tier |
| `kpi_summary.csv` | one row per KPI | kpi, value |
| `churn_by_contract.csv` | one row per contract type | Contract, customers, churners, monthly_revenue, churn_rate_pct |
| `churn_by_tenure_band.csv` | one row per tenure band | tenure_band, customers, churners, monthly_revenue, churn_rate_pct |
| `churn_by_payment.csv` | one row per payment method | PaymentMethod, customers, churners, monthly_revenue, churn_rate_pct |
| `churn_by_internet.csv` | one row per internet type | InternetService, customers, churners, monthly_revenue, churn_rate_pct |
| `business_segments.csv` | risk_level x value_tier | risk_level, value_tier, customers, monthly_revenue, avg_churn_probability, share_of_customers, share_of_monthly_revenue |
| `retention_priority_top200.csv` | top 200 retention priorities | customerID, churn_probability, risk_level, MonthlyCharges, value_tier, priority_score |
| `top_model_features.csv` | one row per model feature | feature name, standardized coefficient |

## KPI definitions (Page 1 source: `kpi_summary.csv`)

| KPI | Definition | Value (computed) |
|---|---|---|
| Total Customers | row count of all customers | 7,043 |
| Churn Rate | share of customers with Churn = Yes | 26.54% |
| Total Monthly Revenue | sum of MonthlyCharges | $456,116.90 |
| Average Monthly Charges | mean of MonthlyCharges | $64.76 |
| High-Risk Customers | count of risk_level = High | 2,503 |
| Estimated Monthly Revenue at Risk (probability-weighted) | sum(churn_probability x MonthlyCharges over High-risk) | $146,705 |
| Estimated Annualized Revenue at Risk | monthly estimate x 12 | $1,760,460 |

**Labeling rule:** the revenue-at-risk KPIs must carry the word "Estimated" in
the card title — predicted churn is not guaranteed lost revenue.

## Data model

Import `risk_scores.csv` as the single fact table. The four `churn_by_*` files
and `business_segments.csv` are pre-aggregated lookup/visual tables — no
relationships are required (each is standalone). If you prefer a star schema,
create dimension tables from the distinct values of Contract / PaymentMethod /
InternetService / tenure_band and relate them to the fact table on the matching
column (one-to-many, single direction).

Slicers should come from the fact table columns so all pages filter consistently:
`Contract`, `PaymentMethod`, `InternetService`, `risk_level`, `value_tier`, `tenure`.

## Page 1 — Executive Overview

- 6 KPI cards: Total Customers, Churn Rate, Total Monthly Revenue, Avg Monthly
  Charges, High-Risk Customers, Estimated Revenue at Risk (monthly + annualized
  as a subtitle).
- Clustered bar: customer count and monthly revenue by risk_level (from fact table).
- Slicers: Contract, PaymentMethod.

## Page 2 — Churn Analysis

- Bar chart: churn_rate_pct by Contract (`churn_by_contract.csv`) — shows
  month-to-month 42.7% vs two-year 2.8%.
- Column chart: churn_rate_pct by tenure_band (`churn_by_tenure_band.csv`) —
  first-year concentration.
- Bar chart: churn_rate_pct by PaymentMethod (`churn_by_payment.csv`).
- Stacked column: churners vs retained by InternetService (`churn_by_internet.csv`).
- Slicers: none extra (inherit from page 1 if using sync slicers).

## Page 3 — ML Churn Risk

- Histogram: churn_probability distribution (fact table, bin size 0.05).
- Donut: customers by risk_level.
- Matrix: risk_level x value_tier with customers and monthly_revenue
  (`business_segments.csv`).
- Bar chart: top 15 model features by |standardized coefficient|
  (`top_model_features.csv`); title should note "predictive signal, not causal".
- Table: `retention_priority_top200.csv` (customerID, churn_probability,
  risk_level, MonthlyCharges, priority_score), sorted by priority_score desc.

## Page 4 — Revenue & Retention

- Stacked bar: monthly_revenue by risk_level split by value_tier.
- KPI cards: Estimated Monthly / Annualized Revenue at Risk; High-risk +
  High-value customer count (781) and their monthly revenue ($76,651).
- Table: top 200 retention priorities (same table as page 3, focused columns).

## Design notes

- Business clarity over visual complexity: no more than ~6 visuals per page.
- Consistent color language: High risk = red (#D9534F), Medium = amber
  (#F0AD4E), Low = green (#5CB85C) across every page.
- Every revenue-at-risk visual includes "Estimated" in its title.
- Currency formatting: $#,0; percentages: 0.0%.
