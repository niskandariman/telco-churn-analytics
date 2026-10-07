# PRD — Telco Churn Analytics & Prediction

## 1. Project Overview

An end-to-end analytics and machine learning case study simulating a real-world telecom churn project. The project combines traditional Data Analytics (EDA, SQL, dashboarding) with Machine Learning (classification, explainability, risk scoring) to answer one central question: which customers are most likely to churn, why, how much revenue is at risk, and who should the business prioritize for retention?

**Status:** Implemented end-to-end. Results and artifacts: see `README.md`, `notebooks/`, `reports/`, `models/`, `dashboard/`.

## 2. Business Context

We simulate a telecom company ("the business") that wants to reduce customer churn and improve retention. Acquiring a new customer is widely understood to cost significantly more than retaining an existing one, so the business wants a data-driven way to identify at-risk customers early enough to intervene with targeted retention actions.

This is a portfolio project: it should read as a realistic business case study, not a Kaggle exercise.

## 3. Business Problem

The company loses customers and, with them, recurring revenue. Today it has no systematic way to know:

- which customers are likely to leave,
- why they are likely to leave,
- how much revenue is exposed,
- or whom to contact first with limited retention budget.

## 4. Business Questions

1. Which customers are most likely to churn?
2. Why are they likely to churn (driving factors, per segment and per customer)?
3. How much revenue may be at risk (monthly and annualized estimate)?
4. Which customers should the business prioritize for retention (high risk + high value)?
5. What is the overall churn rate, and how does it vary by contract, tenure, payment method, services, and demographics?
6. Which segments combine high revenue with high churn risk?

## 5. Project Objectives

Demonstrate, with working artifacts and honest documentation:

1. Data cleaning
2. Exploratory Data Analysis
3. SQL analysis
4. Statistical reasoning
5. Feature engineering
6. Machine learning
7. Model evaluation
8. Model comparison
9. Model explainability
10. Customer churn risk scoring
11. Revenue-at-risk analysis
12. Data visualization
13. Business insights
14. Business recommendations
15. Professional documentation

## 6. Stakeholders

| Stakeholder | Interest |
|---|---|
| Chief Revenue / Commercial Officer | Churn rate trend, revenue at risk, retention ROI |
| Customer Retention / Marketing team | Prioritized call lists, segment-level churn drivers |
| Customer Success / Support | Service-related churn signals (e.g., tech support gaps) |
| Finance | Revenue exposure estimates, intervention cost framing |
| Data / Analytics team | Reproducible pipeline, model quality, documentation |

## 7. Dataset Description

- **File:** `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` (IBM sample Telco dataset; raw file is immutable and is the single source of truth)
- **Size:** 7,043 rows × 21 columns (verified against the actual file)
- **Grain:** one row per customer
- **Target:** `Churn` (values verified: `No` = 5,174, `Yes` = 1,869 → ~26.5% churn rate)
- Full per-column detail: see `DATA_DICTIONARY.md`

Key columns: `customerID` (identifier), demographics (`gender`, `SeniorCitizen`, `Partner`, `Dependents`), account (`tenure`, `Contract`, `PaymentMethod`, `PaperlessBilling`, `MonthlyCharges`, `TotalCharges`), services (`PhoneService`, `MultipleLines`, `InternetService`, and add-on services), and `Churn`.

## 8. Data Quality Requirements

The cleaning phase must *investigate* (not pre-assume) and document findings:

- Missing values
- Blank strings
- Whitespace
- Duplicate rows and duplicate customer IDs
- Incorrect data types
- Invalid values
- Outliers where appropriate
- Inconsistent categorical values

**Verified during Phase 0 (real observations, not assumptions):**

- `TotalCharges` is stored as text/object; 11 values are blank strings (`" "`). All 11 belong to customers with `tenure = 0` (new customers, no billing history yet), all currently labeled `Churn = No`. No other non-numeric values.
- No duplicate rows; `customerID` is unique across all 7,043 rows.
- Categorical domains are consistent (e.g., `Yes`/`No`/`No internet service`); no case or whitespace inconsistencies observed beyond the blank `TotalCharges`.
- `SeniorCitizen` is already 0/1 numeric (not Yes/No).
- No other missing values detected by standard parsing.

## 9. Data Cleaning Requirements

- Convert `TotalCharges` to numeric; the 11 blank values correspond to `tenure = 0` customers and must be handled explicitly and transparently (candidate options: leave as 0 with a documented rationale since no billing has occurred, or impute; decision and reasoning must be documented in the cleaning notebook — do not invent the result here).
- Trim whitespace on string columns defensively.
- Verify dtypes after conversion.
- Document every transformation in the cleaning notebook; write cleaned output to `data/processed/` only — never modify `data/raw/`.

## 10. Exploratory Data Analysis Requirements

EDA must answer decision-relevant business questions, e.g.:

- What is the overall churn rate?
- Which contract types have the highest churn?
- How does tenure relate to churn?
- Does monthly charge relate to churn?
- Which payment methods have higher churn?
- Which services are associated with churn (e.g., fiber optic vs DSL, add-on security/support services)?
- How does churn vary across customer segments (demographics, service bundles)?
- Which customer groups have the highest retention risk?
- Which segments have high revenue but also high churn?

Rules: no charts for the sake of charts; every analysis should be able to lead to a business decision; findings are written from the actual data only.

## 11. SQL Analysis Requirements

SQL scripts in `sql/` will cover (dialect noted per script; SQLite-friendly by default):

- Overall churn rate, customer counts, revenue metrics
- Churn by contract type, payment method, tenure groups, service usage
- Customer segmentation
- High-value customer identification
- High-risk customer identification
- Revenue-at-risk analysis

Use the right tool for each query — `SELECT`, `WHERE`, `GROUP BY`, `CASE WHEN`, aggregates, CTEs, JOINs, and window functions where they genuinely help. No gratuitous complexity.

## 12. Feature Engineering Requirements

- Derived features explored in the feature-engineering notebook (e.g., tenure groups/bins, service counts, charge-per-tenure ratios, "no add-on services" flags) — each with a documented rationale.
- All engineered features must be computable *before* churn occurs (see leakage rules, §18).
- Encoding: categorical variables encoded appropriately for each model family (one-hot / ordinal as justified).
- Scaling applied where the model requires it (e.g., Logistic Regression), fitted on training data only.

## 13. Machine Learning Requirements

- **Problem:** binary classification. Target `Churn`, encoded Churn = 1, No churn = 0 (actual values verified: `Yes`/`No`; encoding applied in code after verification).
- **Models to compare:**
  1. Logistic Regression — interpretable baseline
  2. Random Forest — nonlinear tree ensemble
  3. XGBoost — gradient boosting
- No assumption that XGBoost wins; the final model is selected on evidence (validation metrics) and business requirements (interpretability needs, scoring behavior).
- Preprocessing must live inside a scikit-learn `Pipeline` to prevent train/test contamination.

## 14. Model Evaluation Strategy

- Stratified train/test split (verified class imbalance: ~26.5% churn), fixed `random_state` for reproducibility.
- Class imbalance investigated explicitly; candidate approaches: `class_weight` / `scale_pos_weight`, and SMOTE (imbalanced-learn). **SMOTE must be applied only to training folds after the split — never to the full dataset before splitting.** The chosen approach is documented with reasoning.
- Metrics (never accuracy alone): Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix.
- Business framing of the confusion matrix:
  - **False Negative** (missed churner): lost retention opportunity → lost revenue; churn problems favor high recall.
  - **False Positive** (flagged but would have stayed): wasted retention offer/cost.
  - **True Positive / True Negative:** correct targeting / correct exclusion.
  - The operating point must balance recall against precision and the real cost of interventions — no blind recall-maximization.
- Hyperparameter tuning (RandomizedSearchCV or GridSearchCV) with proper cross-validation on the training set only; the test set is used once, as the final unbiased evaluation.

## 15. Model Explainability Requirements

- Feature importance (model-native) and SHAP values.
- Global explanation: which features drive churn risk overall.
- Individual explanation: "why does the model think *this* customer is likely to churn?" (per-customer SHAP breakdown).
- **Explicit rule:** predictive importance is correlational. SHAP/feature-importance outputs must never be described as causal effects.

## 16. Churn Risk Scoring

- The final model scores every customer with a churn probability.
- Output table: `customerID | churn_probability | risk_level`.
- Risk levels (High / Medium / Low) assigned via thresholds that are **justified** — derived from model performance (e.g., precision/recall trade-off at candidate cutoffs, validation-set behavior) and/or business considerations (intervention capacity, offer cost) — never arbitrary. Threshold selection and reasoning are documented.

## 17. Revenue-at-Risk Analysis

Estimated metrics, clearly labeled as estimates:

- Number of high-risk customers
- Monthly revenue associated with high-risk customers
- Estimated annualized revenue exposure (with stated assumptions, e.g., average months retained)
- High-risk + high-value customer list (retention priorities)

**Rule:** predicted churn ≠ guaranteed lost revenue. All revenue-at-risk figures are labeled as estimates with assumptions stated.

## 18. Dashboard Requirements (Power BI)

Business clarity over visual complexity. Suggested pages:

- **Page 1 — Executive Overview:** Total Customers, Churn Rate, Total Revenue, Avg Monthly Charges, High-Risk Customers, Estimated Revenue at Risk.
- **Page 2 — Churn Analysis:** churn by contract, tenure, payment method, services, key segments.
- **Page 3 — ML Churn Risk:** churn probability distribution, risk-level distribution, high-risk segments, top model features, high-risk customer table.
- **Page 4 — Revenue & Retention:** revenue by segment, estimated revenue at risk, high-value/high-risk customers, retention priorities.

## 19. Business Insights Requirements

- Insights must be derived from actual analysis results (EDA, SQL, model outputs) — never fabricated or assumed in advance.
- Each insight should state the evidence behind it and the business implication.

## 20. Business Recommendations

- Actionable, prioritized recommendations tied to specific findings (e.g., which segments to target, which service gaps to address), with caveats where evidence is correlational.
- Written only after analysis supports them.

## 21. Technical Stack

- **Python:** pandas, NumPy, Matplotlib, Seaborn, scikit-learn, imbalanced-learn, XGBoost, SHAP, Jupyter
- **SQL:** analytical queries (SQLite-compatible scripts by default)
- **Power BI:** dashboard / KPI reporting
- Also: `openpyxl` for any Excel export needs

## 22. Project Architecture

```
telco-churn-analytics/
├── data/
│   ├── raw/                  # immutable source data
│   └── processed/            # cleaned/engineered outputs
├── notebooks/                # cleaning, EDA, feature engineering, ML, explainability
├── src/
│   ├── data/                 # data loading/cleaning modules
│   ├── features/             # feature engineering modules
│   ├── models/               # training, evaluation, scoring modules
│   └── visualization/        # plotting utilities
├── sql/                      # analytical SQL scripts
├── models/                   # saved trained model artifacts
├── dashboard/                # Power BI files / supporting exports
├── reports/                  # generated reports and risk-score exports
├── README.md
├── PRD.md
├── DATA_DICTIONARY.md
├── requirements.txt
└── .gitignore
```

Flow: `data/raw` → cleaning (src/data + notebook) → `data/processed` → EDA + SQL analysis → feature engineering → model training/evaluation (models saved to `models/`) → risk scoring → `reports/` → Power BI dashboard (`dashboard/`).

## 23. Expected Deliverables

1. Cleaned dataset in `data/processed/` + documented cleaning notebook
2. EDA notebook with business findings and charts
3. SQL analysis scripts with results
4. Feature engineering notebook
5. ML notebook: baseline models, imbalance handling, tuning, evaluation, model comparison
6. Explainability notebook: global + per-customer explanations
7. Churn risk score table + revenue-at-risk analysis in `reports/`
8. Power BI dashboard in `dashboard/`
9. Final README with real results, findings, and recommendations

## 24. Success Criteria

- Raw data untouched; all transformations reproducible via code with a fixed random seed.
- No data leakage; preprocessing fitted on training data only.
- Models evaluated on multiple metrics; final model selected with documented justification.
- Risk thresholds and any imbalance-handling choice are justified in writing.
- Revenue-at-risk clearly labeled as an estimate.
- Every reported metric, chart, and finding traces to actual computed results.
- Dashboard answers the executive questions without training.

## 25. Limitations

- Single-month snapshot: no temporal behavior (usage trends, complaints) available; churn drivers are inferred from point-in-time attributes.
- The dataset is a public sample (IBM Telco), not a real company's data; figures are illustrative.
- Predictions are probabilistic and correlational; the model does not establish causation.
- Revenue-at-risk relies on assumptions (e.g., expected remaining lifetime) and is an estimate only.
- Class imbalance (~1:2.8) limits the practical precision achievable at very high recall.

## 26. Future Improvements

- Time-series churn modeling with monthly behavioral data.
- Uplift modeling to measure retention-offer effectiveness (moving from prediction to causal targeting).
- Cost-sensitive learning using real intervention costs.
- Automated pipeline (orchestration) and model monitoring/drift detection in production.
- A/B testing framework for retention campaigns.
