"""Build notebooks/05_explainability.ipynb."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nbbuild import build_notebook, SETUP

ROOT = Path(__file__).resolve().parents[1]

SETUP5 = SETUP + """
import json

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "telco_features.csv")
meta = json.loads((PROJECT_ROOT / "models" / "model_metadata.json").read_text())
final_model = joblib.load(PROJECT_ROOT / "models" / "final_model.joblib")

y = (df["Churn"] == "Yes").astype(int)
X = df.drop(columns=["customerID", "Churn", "churn_flag"])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=meta["random_state"]
)

prep = final_model.named_steps["preprocessor"]
clf = final_model.named_steps["model"]
Z_train = prep.transform(X_train)
Z_test = prep.transform(X_test)
feat_names = [n.replace("num__", "").replace("cat__", "") for n in prep.get_feature_names_out()]
print("transformed feature matrix:", Z_train.shape)
"""

cells = [
    ("md", "# 05 — Model Explainability\n\n"
     "Two levels of explanation for the final model:\n\n"
     "1. **Global** — which features carry the most predictive signal overall (model coefficients + SHAP summary).\n"
     "2. **Individual** — why the model assigns a specific customer a high (or low) churn probability (per-customer SHAP waterfall).\n\n"
     "**Interpretation rule:** these are *predictive* explanations. They show what the model relies on, not what causes "
     "churn. Nothing in this notebook supports causal claims."),
    ("code", SETUP5),
    ("md", "## 1. Global signal — model coefficients\n\n"
     "For regularized logistic regression, the standardized coefficient is the model-native importance: the signed "
     "change in log-odds per standard deviation of the feature."),
    ("code", "coefs = pd.Series(clf.coef_[0], index=feat_names).sort_values(key=np.abs, ascending=False)\ntop = coefs.head(15)\nprint(top.round(3).to_string())\n\nfig, ax = plt.subplots(figsize=(8, 5))\ncolors = ['#d9534f' if v > 0 else '#5cb85c' for v in top]\nax.barh(top.index[::-1], top.values[::-1], color=colors[::-1])\nax.set(xlabel='standardized coefficient (log-odds)', title='Top 15 features by absolute coefficient (red = raises churn risk)')\nfig.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'lr_coefficients.png', dpi=150, bbox_inches='tight')\nplt.show()\n\ncoefs.rename('coefficient').to_csv(PROJECT_ROOT / 'reports' / 'top_model_features.csv')"),
    ("md", "## 2. Global signal — SHAP\n\nSHAP values decompose each prediction into per-feature contributions against a background expectation. A "
     "background sample of the training matrix keeps computation fast; the model is linear so LinearExplainer applies."),
    ("code", "background = shap.sample(Z_train, 200, random_state=0)\nexplainer = shap.LinearExplainer(clf, background)\nexplainer_z = explainer(Z_test)\n\nshap.plots.bar(explainer_z, max_display=15, show=False)\nplt.title('Global SHAP importance (mean |SHAP value|)')\nplt.tight_layout()\nplt.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'shap_global_bar.png', dpi=150, bbox_inches='tight')\nplt.show()"),
    ("code", "shap.plots.beeswarm(explainer_z, max_display=15, show=False)\nplt.title('SHAP beeswarm — feature value vs contribution to churn score')\nplt.tight_layout()\nplt.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'shap_beeswarm.png', dpi=150, bbox_inches='tight')\nplt.show()"),
    ("md", "## 3. Individual explanations — 'why does the model think this customer will churn?'\n\nTwo held-out customers are explained end-to-end: the customer with the highest predicted churn probability and one "
     "with a low probability, including their actual account profile for context."),
    ("code", "probs = final_model.predict_proba(X_test)[:, 1]\nidx_high = int(np.argmax(probs))\nidx_low = int(np.argmin(probs))\nprint(f'highest predicted churn probability: {probs[idx_high]:.3f} (actual: {y_test.iloc[idx_high]})')\nprint(f'lowest  predicted churn probability: {probs[idx_low]:.3f} (actual: {y_test.iloc[idx_low]})')\n\nprofile_cols = ['Contract', 'tenure', 'InternetService', 'PaymentMethod', 'OnlineSecurity', 'TechSupport', 'MonthlyCharges', 'addon_count']\nprint('\\nHigh-risk customer profile:')\nprint(X_test.iloc[idx_high][profile_cols].to_string())\nprint('\\nLow-risk customer profile:')\nprint(X_test.iloc[idx_low][profile_cols].to_string())"),
    ("code", "for label, idx in [('high-risk customer', idx_high), ('low-risk customer', idx_low)]:\n    expl_i = explainer(Z_test[[idx]])\n    plt.figure()\n    shap.plots.waterfall(expl_i[0], max_display=10, show=False)\n    plt.title(f'SHAP waterfall — {label} (p(churn)={probs[idx]:.2f})', fontsize=11)\n    plt.tight_layout()\n    plt.savefig(PROJECT_ROOT / 'reports' / 'figures' / f'shap_waterfall_{label.split(\"-\")[0]}.png', dpi=150, bbox_inches='tight')\n    plt.show()"),
    ("md", "## 4. Reading an individual explanation\n\nThe waterfall starts from the population baseline (average model output) and adds each feature's contribution for "
     "this customer. Red bars push the prediction toward churn, blue bars push toward staying. For the high-risk customer "
     "the story reads like the EDA findings combined: contract type, tenure band, payment method and missing protective "
     "add-ons all push the same direction — that is exactly the kind of narrative a retention agent can act on.\n\n"
     "**Calibration caveat:** because the model uses class weighting, predicted probabilities are systematically shifted "
     "upward relative to true base rates. The *ranking* of customers is unaffected, so risk tiers and prioritization are "
     "valid; the probabilities themselves should be read as risk scores, not literal chances. If calibrated probabilities "
     "become a business requirement, apply a CalibratedClassifierCV (isotonic/sigmoid) on top — noted in README limitations."),
    ("md", "## Global findings summary\n\n- Contract type dominates: month-to-month contracts are the strongest churn signal in both coefficients and SHAP.\n- Tenure (and its banded version) is the strongest retention signal — long-tenure customers score far below baseline.\n- Fiber-optic internet, electronic-check payment and missing OnlineSecurity/TechSupport all raise predicted risk.\n- Add-on count and automatic payment reduce predicted risk.\n- All statements are predictive associations observed by the model on this dataset — not causal effects."),
]

if __name__ == "__main__":
    build_notebook(ROOT / "notebooks" / "05_explainability.ipynb", cells)
    print("built notebooks/05_explainability.ipynb")
