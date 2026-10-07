# Telco Churn Analytics & Prediction

End-to-end data analytics and machine learning case study for a simulated telecom company: identify which customers are likely to churn, why, how much revenue is at risk, and who the retention team should contact first.

All numbers in this README were computed from the actual dataset by the notebooks in this repository. Nothing is fabricated; each figure traces to a notebook output or a report artifact.

## 1. Project overview

- **Dataset:** IBM sample Telco Customer Churn — 7,043 customers × 21 columns (one row per customer)
- **Target:** `Churn` (Yes = 1, No = 0); overall churn rate **26.54%** (1,869 of 7,043)
- **Pipeline:** data cleaning → EDA + statistical testing → SQL analysis → feature engineering → model comparison & tuning → SHAP explainability → risk scoring → revenue-at-risk → retention prioritization → Power BI-ready exports
- **Final model:** class-weighted Logistic Regression — test ROC-AUC **0.843**, recall **78.6%**

## 2. Business problem

The company loses ~26.5% of its customer base (measured monthly) and with it recurring revenue, but had no systematic way to know who will churn, why, or where to spend a limited retention budget. Acquiring a new customer costs far more than retaining one, so the goal is early, targeted intervention.

## 3. Business questions

1. Which customers are most likely to churn?
2. Why are they likely to churn (which factors are associated with risk)?
3. How much revenue is at risk (estimated)?
4. Who should the retention team contact first?
5. How does churn vary by contract, tenure, payment method, services, and value tier?

## 4. Dataset

`data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` (immutable source of truth). Per-column documentation: [DATA_DICTIONARY.md](DATA_DICTIONARY.md). Specification: [PRD.md](PRD.md).

## 5. Data cleaning ([notebook 01](notebooks/01_data_cleaning.ipynb))

Issues found (verified, not assumed):

- **`TotalCharges` stored as text with 11 blank strings** — all 11 belong to `tenure = 0` customers (no completed billing cycle). Set to **0.0** as a factual value, not an imputation; alternatives (dropping rows, median imputation) rejected in the notebook.
- No duplicate rows, unique `customerID`, no other missing values, no whitespace issues, all categorical domains consistent, numeric ranges plausible (tenure 0–72, MonthlyCharges $18.25–$118.75).

Output: `data/processed/telco_cleaned.csv` (7,043 × 21, zero missing). Raw file untouched.

## 6. Exploratory data analysis ([notebook 02](notebooks/02_eda.ipynb))

Headline findings (charts in `reports/figures/`):

| Finding | Evidence |
|---|---|
| Month-to-month contracts are the dominant churn pocket | **42.7%** churn vs **11.3%** (one-year) and **2.8%** (two-year) |
| Churn is concentrated in the first months of life | **52.9%** churn for 0–6-month customers vs **9.5%** for 49–72 months |
| Electronic-check customers churn far more | **45.3%** vs **16.7%** for automatic bank transfer |
| Fiber-optic internet is associated with high churn | **41.9%** vs **19.0%** for DSL |
| Add-on services mark stickier customers | internet customers without OnlineSecurity churn at **41.8%** vs **14.6%** with it (TechSupport: 41.6% vs 15.2%) |
| Churners pay more per month but are early-tenure | mean MonthlyCharges **$74.44 vs $61.27**; mean TotalCharges **$1,532 vs $2,550** |
| Demographics matter little except age | seniors churn at **41.7% vs 23.6%**; gender shows no material difference (26.9% vs 26.2%) |
| Exposure concentrates in month-to-month | month-to-month customers generate **$257,294/mo** — **87%** of all currently-churning monthly revenue |
| High-value customers churn meaningfully | top-quartile spenders (≥ $89.85/mo) churn at **32.7%** while producing **$178,548/mo** |

## 7. Statistical reasoning (notebook 02, §10)

- **Chi-square tests of independence** (categorical vs churn): all tested features significant (p < 0.05) **except gender and PhoneService**. Strongest associations by Cramér's V: Contract (0.41), OnlineSecurity (0.347), TechSupport (0.343), InternetService (0.322).
- **Welch's t-tests** (numeric vs churn): tenure, MonthlyCharges and TotalCharges all differ significantly between churn groups (p < 0.001); Mann-Whitney U on tenure corroborates.
- Interpretation is association-only; nothing here supports causal claims.

## 8. SQL analysis ([sql/](sql/), results: [reports/sql_results.md](reports/sql_results.md))

14 SQLite-compatible statements across 4 scripts: churn overview/KPIs, churn by contract · payment · tenure bands · service usage (with a `RANK()` window function), segmentation and high-value customers (`NTILE` quartiles, CTEs, JOINs back to the customer table), and a rule-based high-risk / revenue-at-risk view. Example output: the rule-based high-risk tier (≥3 risk flags) contains 1,919 customers with a **59.25%** actual churn rate — validating the risk factors EDA found, later superseded by the ML model. Run with `python scripts/run_sql.py`.

## 9. Feature engineering ([notebook 03](notebooks/03_feature_engineering.ipynb), [src/features/engineering.py](src/features/engineering.py))

7 engineered features, each with documented rationale and no target leakage: `tenure_band`, `addon_count`, `has_addon_services`, `service_breadth`, `avg_monthly_to_date` (TotalCharges/tenure; defined 0.0 for tenure = 0), `auto_payment`, `fiber_no_protection`. An ablation check (5-fold CV) justified adoption for the linear model: Logistic Regression F1 **0.601 → 0.618** with engineered features (tree models were flat).

## 10. Machine learning ([notebook 04](notebooks/04_machine_learning.ipynb))

- Stratified 80/20 split, `random_state=42`; all preprocessing inside scikit-learn pipelines (fitted on training folds only); `customerID` and the target excluded from features.
- **Class imbalance** (26.5% churn): compared none / class-weighting / SMOTE (SMOTE only inside imblearn pipelines, i.e. training folds only). Weighting won on CV F1 for every model family.
- **Hyperparameter tuning:** RandomizedSearchCV (25 candidates × 5-fold CV) on the training set; test set evaluated exactly once.

## 11. Model comparison (5-fold CV on training data)

| Model | Recall | Precision | F1 | ROC-AUC |
|---|---|---|---|---|
| **Logistic Regression (weighted)** | **0.795** | 0.520 | **0.629** | **0.847** |
| Random Forest (weighted) | 0.650 | 0.575 | 0.610 | 0.828 |
| XGBoost (weighted) | 0.652 | 0.556 | 0.600 | 0.827 |

## 12. Final model

**Class-weighted Logistic Regression** (C = 0.0123, liblinear). Selected because it won the CV comparison on F1 *and* is the most interpretable family — well suited to per-customer retention conversations. The tree ensembles did not outperform it on this dataset, so the "fancier" model was honestly not chosen.

## 13. Model performance (held-out test set, evaluated once)

| Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| 0.749 | 0.519 | **0.786** | 0.625 | **0.843** | 0.647 |

Confusion matrix (threshold 0.5): 294 true positives, 80 false negatives (missed churners — the costliest business error), 273 false positives (unnecessary interventions), 762 true negatives. The model deliberately trades precision for recall, which matches the economics of retention.

## 14. Explainability ([notebook 05](notebooks/05_explainability.ipynb))

- **Global (coefficients + SHAP):** the strongest predictive signals are `tenure` (protective, −0.49), `Contract_Month-to-month` (+0.48) vs `Contract_Two year` (−0.47), `tenure_band_0-6 mo` (+0.39), `avg_monthly_to_date` (+0.22), fiber-optic internet (+0.21) and high MonthlyCharges (+0.21); OnlineSecurity/TechSupport ownership reduces risk.
- **Individual (SHAP waterfalls):** e.g., the highest-risk held-out customer (p = 0.954, actual churner) is month-to-month, 1-month tenure, fiber, electronic check, no security/support add-ons, $95.10/mo — every factor pushes the same direction.
- All explanations are **predictive associations, not causal effects**.
- Note: class weighting shifts probabilities upward; rankings and risk tiers are valid, but probabilities read best as risk scores.

## 15. Risk scoring ([notebooks/06](notebooks/06_business_application.ipynb), [reports/churn_risk_scores.csv](reports/churn_risk_scores.csv))

Every customer scored once (7,043 rows, validated). Thresholds justified from out-of-fold training behaviour, not arbitrary:

- **High:** p ≥ **0.55** (F1-maximizing cutoff; OOF precision 0.558 / recall 0.746) → **2,503 customers**
- **Medium:** 0.35 ≤ p < 0.55 (F2-maximizing recall-weighted cutoff) → **1,274 customers**
- **Low:** p < 0.35 → **3,266 customers**

## 16. Revenue at risk (ESTIMATES)

> Predicted churn ≠ lost revenue. Figures are estimates under stated assumptions.

| Estimate | Value |
|---|---|
| Monthly revenue billed to High-risk customers (run-rate upper bound) | **$193,567** |
| Annualized run-rate exposure (×12, no intervention assumed) | $2,322,809 |
| **Probability-weighted monthly exposure (headline estimate)** | **$146,705** |
| Annualized probability-weighted estimate (×12) | $1,760,460 |
| High-risk **and** high-value (top-quartile spend) customers | **781**, $76,651/mo |

## 17. Dashboard (Power BI)

A `.pbix` cannot be generated legitimately outside Power BI Desktop, so [dashboard/](dashboard/) provides nine Power BI-ready CSV exports plus [DASHBOARD_SPEC.md](dashboard/DASHBOARD_SPEC.md): KPI definitions, data model, recommended visuals, color language, and page-by-page build instructions (Executive Overview · Churn Analysis · ML Churn Risk · Revenue & Retention).

## 18. Key findings

1. Contract type is the single strongest churn signal (42.7% month-to-month vs 2.8% two-year) and month-to-month customers account for 87% of churning monthly revenue.
2. The first 6 months are the danger window (52.9% churn); risk falls steadily with tenure.
3. Electronic check (45.3%) and fiber-optic internet (41.9%) are actionable watch-list markers.
4. Protective add-ons (OnlineSecurity, TechSupport) halve churn among internet customers.
5. High-value customers churn above average (32.7%) — churn destroys disproportionate revenue in the top quartile.

## 19. Business recommendations

1. **Target the 781 high-risk + high-value customers first** (`reports/retention_priority_list.csv`, ranked by probability × monthly revenue); the top 200 alone cover ~$19.7k/mo of revenue.
2. **Push month-to-month customers onto term contracts** at renewal moments — the strongest lever the data shows.
3. **Run an onboarding/first-90-days program** — churn is heavily front-loaded.
4. **Migrate electronic-check customers to automatic payment** and investigate the fiber-optic experience (price/performance mismatch: fiber + high monthly charges).
5. **Bundle OnlineSecurity/TechSupport** into internet offers — associated with roughly half the churn rate.

*(These are association-based recommendations; measuring true causal impact requires A/B testing — see Future improvements.)*

## 20. Limitations

- Single-month snapshot: no usage trends, complaints, or temporal behavior; drivers are correlational.
- Public sample data (IBM Telco); figures are illustrative, not a real company's.
- Class weighting biases predicted probabilities upward (ranking unaffected); calibrate with `CalibratedClassifierCV` if literal probabilities are needed.
- Revenue-at-risk assumes one year at current run-rate and no retention effect.
- 0.52 precision at the operating point means roughly half of flagged customers would not have churned — the cost of catching 78.6% of true churners.

## 21. Future improvements

Time-series churn modeling with monthly behavioral data · uplift modeling to measure retention-offer causality (prediction → causal targeting) · cost-sensitive optimization with real intervention costs · A/B testing of retention campaigns · automated retraining pipeline with drift monitoring.

## 22. Project architecture

```
telco-churn-analytics/
├── data/raw/               # immutable source CSV
├── data/processed/         # cleaned + engineered datasets
├── notebooks/              # 01 cleaning · 02 EDA+stats · 03 features · 04 ML · 05 explainability · 06 business application
├── src/                    # data · features · models (pipeline, evaluate, scoring) · visualization
├── sql/                    # 4 SQLite-compatible analysis scripts
├── scripts/                # notebook builders, SQL runner, report bundler, validation
├── models/                 # final_model.joblib + model_metadata.json
├── dashboard/              # Power BI-ready CSVs + DASHBOARD_SPEC.md
├── reports/                # scores, revenue-at-risk, segments, figures, Excel summary
├── PRD.md · DATA_DICTIONARY.md · requirements.txt · .gitignore
```

## 23. How to reproduce

```bash
pip install -r requirements.txt

# end-to-end (notebooks must run in order)
py -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_cleaning.ipynb
py -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb
py -m jupyter nbconvert --to notebook --execute --inplace notebooks/03_feature_engineering.ipynb
py -m jupyter nbconvert --to notebook --execute --inplace notebooks/04_machine_learning.ipynb
py -m jupyter nbconvert --to notebook --execute --inplace notebooks/05_explainability.ipynb
py -m jupyter nbconvert --to notebook --execute --inplace notebooks/06_business_application.ipynb

python scripts/run_sql.py            # SQL analysis -> reports/sql_results.md
python scripts/make_report_bundle.py # Excel summary -> reports/
python scripts/validate_project.py   # full validation suite
```

Fixed `random_state=42` everywhere randomness occurs; Python 3.14, pandas 3.0, scikit-learn 1.9, XGBoost 3.4, SHAP 0.52.

## 24. Technologies used

Python · pandas · NumPy · Matplotlib · Seaborn · SciPy · scikit-learn · imbalanced-learn · XGBoost · SHAP · Jupyter · SQL (SQLite) · Power BI (spec + datasets) · joblib
