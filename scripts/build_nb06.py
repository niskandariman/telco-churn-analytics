"""Build notebooks/06_business_application.ipynb — scoring, revenue-at-risk, segmentation, retention."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nbbuild import build_notebook, SETUP

ROOT = Path(__file__).resolve().parents[1]

SETUP6 = SETUP + """
import json

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.models.scoring import (
    add_priority_score, add_value_tier, revenue_at_risk, score_customers,
    segment_summary, validate_scores,
)

sns.set_theme(style="whitegrid")
df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "telco_features.csv")
meta = json.loads((PROJECT_ROOT / "models" / "model_metadata.json").read_text())
final_model = joblib.load(PROJECT_ROOT / "models" / "final_model.joblib")
REPORTS = PROJECT_ROOT / "reports"
DASH = PROJECT_ROOT / "dashboard"
REPORTS.mkdir(exist_ok=True)
DASH.mkdir(exist_ok=True)
"""

cells = [
    ("md", "# 06 — Business Application\n\n"
     "Applies the final model to **every customer** (Phases 8-11 of the PRD):\n\n"
     "1. Churn risk scoring with documented thresholds\n"
     "2. Estimated revenue at risk (clearly labeled estimates)\n"
     "3. Business segmentation (risk x value)\n"
     "4. Prioritized retention list\n\n"
     "The dashboard-ready exports for Power BI are also produced here."),
    ("code", SETUP6),
    ("md", "## 1. Score all customers\n\nThresholds come from notebook 04 (out-of-fold training behaviour): HIGH >= 0.55 (F1-maximizing), MEDIUM >= 0.35 (F2-maximizing broad-capture layer)."),
    ("code", "scores = score_customers(df, final_model, meta['high_threshold'], meta['medium_threshold'])\nchecks = validate_scores(scores, df)\nprint('validation:', checks)\nprint(f'rows: {len(scores)} (dataset: {len(df)})')\nscores = add_value_tier(df, scores)\nprint('\\nrisk level distribution:')\nprint(scores['risk_level'].value_counts())\nprint('\\navg probability by risk level:')\nprint(scores.groupby('risk_level')['churn_probability'].agg(['mean', 'min', 'max']).round(3))"),
    ("code", "scores.to_csv(REPORTS / 'churn_risk_scores.csv', index=False)\nfig, ax = plt.subplots(figsize=(7, 4))\nsns.histplot(data=scores, x='churn_probability', hue='risk_level', hue_order=['Low', 'Medium', 'High'],\n             bins=40, multiple='stack', palette=['#5cb85c', '#f0ad4e', '#d9534f'], ax=ax)\nax.set(title='Churn probability distribution with risk thresholds', xlabel='predicted churn probability')\nfor t in [meta['medium_threshold'], meta['high_threshold']]:\n    ax.axvline(t, color='black', ls='--', lw=1)\nfig.savefig(REPORTS / 'figures' / 'risk_distribution.png', dpi=150, bbox_inches='tight')\nplt.show()\nprint('saved reports/churn_risk_scores.csv')"),
    ("md", "## 2. Estimated revenue at risk\n\n> **This is an ESTIMATE, not a prediction of actual losses.** Predicted churn is not guaranteed churn. Two views are given:\n>\n> - **Run-rate exposure**: total monthly revenue billed to High-risk customers — the upper bound if every one of them churned.\n> - **Probability-weighted exposure**: sum of (probability x monthly charge) — the model's confidence-weighted exposure, the fairer headline number.\n>\n> The annualized figure simply multiplies monthly exposure by 12, i.e. it assumes one full year of billing at the current run-rate and no retention actions. Real exposure depends on retention effectiveness and churn timing."),
    ("code", "rar = revenue_at_risk(scores)\nfor k, v in rar.items():\n    print(f'{k}: {v:,.0f}' if isinstance(v, (int, float)) else f'{k}: {v}')\n\nsummary_rows = {\n    'metric': ['High-risk customers', 'Monthly revenue of High-risk customers (run-rate exposure estimate, upper bound)',\n               'Annualized exposure estimate (x12, assumes 1 year at current run-rate, no intervention)',\n               'Probability-weighted monthly exposure (headline estimate)',\n               'High-risk AND high-value (top-quartile) customers',\n               'Monthly revenue of High-risk AND high-value customers (estimate)'],\n    'estimate': [f\"{rar['high_risk_customers']:,}\", f\"${rar['monthly_revenue_high_risk']:,.0f}\",\n                 f\"${rar['annualized_exposure_high_risk_x12']:,.0f}\",\n                 f\"${rar['probability_weighted_monthly_exposure']:,.0f}\",\n                 f\"{rar['high_risk_high_value_customers']:,}\",\n                 f\"${rar['monthly_revenue_high_risk_high_value']:,.0f}\"],\n}\nimport pandas as pd\npd.DataFrame(summary_rows).to_csv(REPORTS / 'revenue_at_risk_summary.csv', index=False)\nprint('\\nsaved reports/revenue_at_risk_summary.csv')"),
    ("md", "## 3. Business segments (risk x value)\n\nFour actionable segments; the top-priority one is **High risk + High value** — the customers the retention team should contact first."),
    ("code", "seg = segment_summary(scores)\nprint(seg.round(3).to_string(index=False))\nseg.to_csv(REPORTS / 'business_segments.csv', index=False)\n\nfig, ax = plt.subplots(figsize=(7, 4))\nseg_pivot = scores.pivot_table(index='risk_level', columns='value_tier', values='MonthlyCharges', aggfunc='sum')\nseg_pivot = seg_pivot.reindex(['High', 'Medium', 'Low']).reindex(columns=['High value', 'Standard value'])\nseg_pivot.plot(kind='bar', ax=ax, color=['#d9534f', '#5cb85c'])\nax.set(title='Monthly revenue by risk level and value tier', ylabel='monthly revenue ($)', xlabel='risk level')\nplt.xticks(rotation=0)\nfig.savefig(REPORTS / 'figures' / 'revenue_by_segment.png', dpi=150, bbox_inches='tight')\nplt.show()"),
    ("md", "## 4. Who should we contact first? — retention prioritization\n\n**Methodology:** priority score = churn probability x monthly revenue (expected monthly revenue exposure). Sorting "
     "by probability alone would surface cheap customers; sorting by revenue alone would surface safe ones. The product "
     "targets the customers whose expected loss is largest. Ties in business practice are broken by the high-value/high-risk "
     "segment; the score is a ranking tool, not a financial forecast."),
    ("code", "priority = add_priority_score(scores)\npriority_out = priority[['customerID', 'churn_probability', 'risk_level', 'MonthlyCharges', 'value_tier', 'priority_score']].copy()\npriority_out.to_csv(REPORTS / 'retention_priority_list.csv', index=False)\n\nprint('Top 20 retention priorities:')\nprint(priority_out.head(20).round(3).to_string(index=False))\nprint('\\nTop 200 priorities: monthly revenue covered =', f\"${priority.head(200)['MonthlyCharges'].sum():,.0f}\")\n\nhigh_value_high_risk = priority[(priority['risk_level'] == 'High') & (priority['value_tier'] == 'High value')]\nhvhr = high_value_high_risk[['customerID', 'churn_probability', 'risk_level', 'MonthlyCharges', 'value_tier', 'priority_score']]\nhvhr.to_csv(REPORTS / 'high_value_high_risk_customers.csv', index=False)\nprint(f'\\nhigh-risk + high-value list saved: {len(hvhr)} customers, ${hvhr[\"MonthlyCharges\"].sum():,.0f}/mo')"),
    ("md", "## 5. Profile of the high-risk population\n\nWhat actually characterizes High-risk customers? (Model-based; associations, not causes.)"),
    ("code", "high = scores[scores['risk_level'] == 'High'].index\ndf_high = df.loc[scores.loc[high, 'customerID'].index]\n\nprofile = {}\nfor col in ['Contract', 'PaymentMethod', 'InternetService', 'tenure_band', 'OnlineSecurity']:\n    t = df_high[col].value_counts(normalize=True).round(3) * 100\n    profile[col] = t\nfor col, t in profile.items():\n    print(f'\\n{col} (share of {len(df_high):,} High-risk customers):')\n    print(t.to_string())"),
    ("code", "# Dashboard-ready exports (Phase 12)\nreport = df.merge(scores[['customerID', 'churn_probability', 'risk_level', 'value_tier']], on='customerID')\n\nreport[['customerID', 'Contract', 'tenure', 'PaymentMethod', 'InternetService', 'MonthlyCharges', 'TotalCharges',\n        'Churn', 'churn_probability', 'risk_level', 'value_tier']].to_csv(DASH / 'risk_scores.csv', index=False)\n\nkpis = {\n    'kpi': ['total_customers', 'churn_rate_pct', 'total_monthly_revenue', 'avg_monthly_charges',\n            'high_risk_customers', 'estimated_monthly_revenue_at_risk',\n            'estimated_annualized_revenue_at_risk'],\n    'value': [len(df), round(100 * (df['Churn'] == 'Yes').mean(), 2),\n              round(df['MonthlyCharges'].sum(), 2), round(df['MonthlyCharges'].mean(), 2),\n              rar['high_risk_customers'], round(rar['probability_weighted_monthly_exposure'], 2),\n              round(rar['probability_weighted_monthly_exposure'] * 12, 2)],\n}\npd.DataFrame(kpis).to_csv(DASH / 'kpi_summary.csv', index=False)\n\nfor col, fname in [('Contract', 'churn_by_contract.csv'), ('tenure_band', 'churn_by_tenure_band.csv'),\n                   ('PaymentMethod', 'churn_by_payment.csv'), ('InternetService', 'churn_by_internet.csv')]:\n    t = report.groupby(col).agg(customers=('customerID', 'count'),\n                                churners=('Churn', lambda s: (s == 'Yes').sum()),\n                                monthly_revenue=('MonthlyCharges', 'sum'))\n    t['churn_rate_pct'] = (100 * t['churners'] / t['customers']).round(2)\n    t.to_csv(DASH / fname)\n\nseg_export = seg.copy()\nseg_export.to_csv(DASH / 'business_segments.csv', index=False)\npriority_out.head(200).to_csv(DASH / 'retention_priority_top200.csv', index=False)\n\nfeatures = pd.read_csv(REPORTS / 'top_model_features.csv')\nfeatures.head(15).to_csv(DASH / 'top_model_features.csv', index=False)\n\nprint('dashboard exports:', sorted(p.name for p in DASH.glob('*.csv')))"),
    ("md", "## Summary of decisions in this phase\n\n- **Risk thresholds:** inherited from notebook 04 (HIGH=0.55 F1-max; MEDIUM=0.35 F2-max) — documented and reproducible.\n- **Value definition:** top quartile of `MonthlyCharges` (current revenue run-rate). Alternative (historical `TotalCharges`) rejected because forward-looking exposure matters for retention.\n- **Priority score:** probability x monthly revenue, because retention capacity is finite and expected loss — not raw probability — is what the team should rank on.\n- **Revenue at risk** is reported as two estimates (run-rate upper bound and probability-weighted headline) with assumptions stated; predicted churn is never equated to lost revenue."),
]

if __name__ == "__main__":
    build_notebook(ROOT / "notebooks" / "06_business_application.ipynb", cells)
    print("built notebooks/06_business_application.ipynb")
