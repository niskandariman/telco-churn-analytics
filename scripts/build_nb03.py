"""Build notebooks/03_feature_engineering.ipynb."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nbbuild import build_notebook, SETUP

ROOT = Path(__file__).resolve().parents[1]

SETUP3 = SETUP + """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.data.clean import PROCESSED_DIR, clean_telco, load_raw
from src.features.engineering import add_features, save_features, ENGINEERED_FEATURES, ADDON_COLS

df = add_features(clean_telco(load_raw())[0])
df["churn_flag"] = (df["Churn"] == "Yes").astype(int)
pd.set_option("display.width", 140)
"""

cells = [
    ("md", "# 03 — Feature Engineering\n\n"
     "Goal: create domain features with a documented business rationale, verify they are computable *before* churn "
     "happens (no leakage), and check that they actually add predictive value before adopting them.\n\n"
     "Reusable logic: `src/features/engineering.py`. Preprocessing pipelines: `src/models/pipeline.py`."),
    ("code", SETUP3),
    ("md", "## 1. Engineered features and their rationale\n\n"
     "| Feature | Rationale | Leakage risk |\n|---|---|---|\n"
     "| `tenure_band` | EDA shows churn concentrated in the first months; bins let linear models capture the non-linear tenure effect | None — tenure known at prediction time |\n"
     "| `addon_count` | More add-on services = stickier bundle (EDA: churn falls with add-on count) | None |\n"
     "| `has_addon_services` | Simple binary of the above for interpretable models | None |\n"
     "| `service_breadth` | Total services owned (phone + internet + add-ons) | None |\n"
     "| `avg_monthly_to_date` | `TotalCharges / tenure` = historical average effective monthly charge; captures pricing history | None; tenure=0 defined as 0.0 (no billing yet) |\n"
     "| `auto_payment` | Automatic payments churn far less than electronic check in EDA | None |\n"
     "| `fiber_no_protection` | Combines the two strongest churn signals: fiber optic without security/protection add-ons | None |"),
    ("md", "## 2. Build features and inspect them against churn"),
    ("code", "df[ENGINEERED_FEATURES].head()"),
    ("code", "t = df.groupby('tenure_band', observed=True)['churn_flag'].agg(['count', 'mean']).rename(columns={'count': 'customers', 'mean': 'churn_rate'})\nprint(t.round(3))\n\nfig, ax = plt.subplots(figsize=(7, 3.5))\nax.bar(t.index, t['churn_rate'] * 100, color='#428bca')\nax.set(ylabel='Churn rate (%)', title='Churn rate by engineered tenure band')\nsavefig = ax.figure.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'churn_by_tenure_band_feature.png', dpi=150, bbox_inches='tight')\nplt.show()"),
    ("code", "t = df.groupby('addon_count')['churn_flag'].agg(['count', 'mean']).rename(columns={'count': 'customers', 'mean': 'churn_rate'})\nprint(t.round(3))\n\nfor col in ['has_addon_services', 'auto_payment', 'fiber_no_protection']:\n    t = df.groupby(col)['churn_flag'].agg(['count', 'mean'])\n    print(f'\\n{col}:')\n    print(t.round(3))"),
    ("code", "print('avg_monthly_to_date by churn:')\nprint(df.groupby('Churn')['avg_monthly_to_date'].describe().round(2))\nprint('\\ncorrelation with MonthlyCharges (collinearity check):')\nprint(df[['avg_monthly_to_date', 'MonthlyCharges', 'tenure']].corr().round(3))"),
    ("md", "## 3. Do the engineered features add predictive value?\n\nQuick 5-fold CV on a 30% training subsample (the full, careful comparison happens in notebook 04). Same preprocessing "
     "pipelines as the final models; the only difference is the feature set. `customerID` and `Churn` are never features."),
    ("code", "from sklearn.model_selection import train_test_split\n\nfrom src.models.pipeline import FEATURE_SETS, build_pipeline\nfrom src.models.evaluate import cv_scores\n\ny = df['churn_flag']\nX_all = df.drop(columns=['customerID', 'Churn', 'churn_flag'])\n\n# A fixed stratified subsample keeps this sanity check fast; random_state fixed for reproducibility.\nX_dev, _, y_dev, _ = train_test_split(X_all, y, train_size=0.3, stratify=y, random_state=42)\n\nrows = []\nfor fs_name, (num_f, cat_f) in FEATURE_SETS.items():\n    for model_name in ['logistic_regression', 'xgboost']:\n        pipe = build_pipeline(model_name, num_f, cat_f)\n        scores = cv_scores(pipe, X_dev[ num_f + cat_f], y_dev)\n        rows.append({'feature_set': fs_name, 'model': model_name, **scores})\nablation = pd.DataFrame(rows)\nprint(ablation.round(4).to_string(index=False))"),
    ("md", "## 4. Save the engineered dataset"),
    ("code", "out = save_features(df)\nprint('saved:', out)\nprint('shape:', df.shape)\nprint('new columns:', ENGINEERED_FEATURES)\nprint('missing values:', int(df.isna().sum().sum()))"),
    ("md", "## Decisions\n\n- All 7 engineered features are computable before churn; none uses target information. `avg_monthly_to_date` is defined as 0.0 for tenure=0 customers (no billing exists) — a documented convention, not an imputation.\n- The ablation above decides which feature set the final models use (evidence-based adoption, not automatic inclusion).\n- `customerID` remains an identifier only."),
]

if __name__ == "__main__":
    build_notebook(ROOT / "notebooks" / "03_feature_engineering.ipynb", cells)
    print("built notebooks/03_feature_engineering.ipynb")
