# Data Dictionary — Telco Customer Churn

Source file: `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` (7,043 rows × 21 columns; one row per customer).

All information below was verified against the actual dataset. Data types shown are as stored in the raw CSV (pandas parse types).

| # | Column | Raw Type | Kind | Business Meaning | Example Values | Analytical Usage | ML Usage | Potential Transformation | Leakage Notes |
|---|--------|----------|------|------------------|----------------|------------------|----------|--------------------------|---------------|
| 1 | `customerID` | text | Categorical (identifier) | Unique customer identifier, e.g. `7590-VHVEG` | `7590-VHVEG`, `5575-GNVDE` | Row identity; joins and lookups only | **Excluded as a predictive feature** | — | Pure identifier; carries no predictive signal and would cause memorization. Use only as an index/label when scoring. |
| 2 | `gender` | text | Categorical | Customer gender | `Female`, `Male` | Demographic segmentation | Feature (one-hot encode) | Binary encode | Known to be typically weak; keep and let the model/EDA show its value. |
| 3 | `SeniorCitizen` | int64 | Categorical (binary) | Whether the customer is a senior citizen | `0`, `1` | Demographic segmentation | Feature (already numeric) | Keep as 0/1 | None. |
| 4 | `Partner` | text | Categorical (binary) | Whether the customer has a partner | `Yes`, `No` | Household/household-size segmentation | Feature (binary encode) | Yes/No → 1/0 | None. |
| 5 | `Dependents` | text | Categorical (binary) | Whether the customer has dependents | `Yes`, `No` | Household segmentation | Feature (binary encode) | Yes/No → 1/0 | None. |
| 6 | `tenure` | int64 | Numerical (discrete) | Months the customer has stayed with the company | `1`, `34`, `72` (range 0–72) | Loyalty analysis; tenure-band churn curves | Strong candidate feature | Bin into tenure groups (e.g., 0–6, 7–12, …); consider ratio features | None — tenure is known at prediction time. Note: `tenure = 0` (11 rows) are brand-new customers with no billing history. |
| 7 | `PhoneService` | text | Categorical (binary) | Whether the customer has phone service | `Yes`, `No` | Service portfolio analysis | Feature | Yes/No → 1/0 | Highly imbalanced (most customers have it); check near-zero variance. |
| 8 | `MultipleLines` | text | Categorical | Multiple phone lines status | `Yes`, `No`, `No phone service` | Service portfolio analysis | Feature (one-hot or ordinal) | Merge `No phone service` with `No` or one-hot encode | `No phone service` is structurally dependent on `PhoneService`. |
| 9 | `InternetService` | text | Categorical | Internet service type | `DSL`, `Fiber optic`, `No` | Service portfolio analysis; fiber vs DSL churn comparison | Feature (one-hot encode) | One-hot | None. |
| 10 | `OnlineSecurity` | text | Categorical | Online security add-on status | `Yes`, `No`, `No internet service` | Add-on service analysis | Feature | Same treatment as `MultipleLines` | `No internet service` depends on `InternetService`. |
| 11 | `OnlineBackup` | text | Categorical | Online backup add-on status | `Yes`, `No`, `No internet service` | Add-on service analysis | Feature | Same treatment | Same dependency note. |
| 12 | `DeviceProtection` | text | Categorical | Device protection add-on status | `Yes`, `No`, `No internet service` | Add-on service analysis | Feature | Same treatment | Same dependency note. |
| 13 | `TechSupport` | text | Categorical | Tech support add-on status | `Yes`, `No`, `No internet service` | Add-on service analysis; support-gap churn signal | Feature | Same treatment | Same dependency note. |
| 14 | `StreamingTV` | text | Categorical | Streaming TV add-on status | `Yes`, `No`, `No internet service` | Entertainment bundle analysis | Feature | Same treatment | Same dependency note. |
| 15 | `StreamingMovies` | text | Categorical | Streaming movies add-on status | `Yes`, `No`, `No internet service` | Entertainment bundle analysis | Feature | Same treatment | Same dependency note. |
| 16 | `Contract` | text | Categorical | Contract term | `Month-to-month`, `One year`, `Two year` | Contract-type churn analysis | Strong candidate feature | One-hot or ordinal encode (by commitment length) | None. |
| 17 | `PaperlessBilling` | text | Categorical (binary) | Whether the customer uses paperless billing | `Yes`, `No` | Billing-behavior analysis | Feature | Yes/No → 1/0 | None. |
| 18 | `PaymentMethod` | text | Categorical | Payment method | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` | Payment-behavior churn analysis | Feature (one-hot encode) | One-hot; consider grouping auto vs manual | None. |
| 19 | `MonthlyCharges` | float64 | Numerical (continuous) | Monthly charge amount (USD) | `29.85`, `70.35` (range 18.25–118.75) | Revenue analysis; price-sensitivity analysis | Feature | Standardize for scale-sensitive models | None. |
| 20 | `TotalCharges` | **text (object)** | Numerical (continuous) | Total amount charged to date (USD) | `100.2`, `8684.8` | Customer lifetime value; revenue-at-risk | Feature | **Convert to numeric**; 11 blank strings (all `tenure = 0` customers) must be handled explicitly and documented | None — it is the cumulative sum of historical charges, known at prediction time. Stored as text in the raw file; conversion happens in cleaning, output goes to `data/processed/`. |
| 21 | `Churn` | text | Categorical (**target**) | Whether the customer left within the last month | `Yes` (1,869), `No` (5,174) → ~26.5% churn | Target of all churn analysis | **Target only** — encode `Yes` = 1, `No` = 0 | Binary encode after verifying actual values in code | This is the label; never use it (or anything derived from it) as a feature. |

## Verified Data Quality Notes

- `TotalCharges` is stored as text; 11 values are blank (`" "`). All 11 rows have `tenure = 0` (new customers with no completed billing cycle) and `Churn = No`. No other non-numeric entries exist.
- No duplicate rows; `customerID` is unique across all 7,043 rows.
- No missing values in any other column under standard parsing.
- Categorical domains are clean and consistent (no case/whitespace variants observed).
- Class imbalance in the target: ~26.5% churn vs ~73.5% non-churn.
- Service add-on columns share the structural value `No internet service`, which is derived from `InternetService = No` — a known multi-collinearity/encoding consideration, not leakage.
