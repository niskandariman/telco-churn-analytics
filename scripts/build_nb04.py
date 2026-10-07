"""Build notebooks/04_machine_learning.ipynb."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nbbuild import build_notebook, SETUP

ROOT = Path(__file__).resolve().parents[1]

SETUP4 = SETUP + """
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt

from src.models.pipeline import (
    FEATURE_SETS, build_pipeline, build_smote_pipeline, feature_names_from_pipeline,
)
from src.models.evaluate import CV, classification_metrics, cv_scores, threshold_analysis

df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "telco_features.csv")
y = (df["Churn"] == "Yes").astype(int)  # verified values: Yes/No -> 1/0
# churn_flag is the encoded target - never a feature (it exists in the CSV only
# as an analysis convenience from notebook 03).
X = df.drop(columns=["customerID", "Churn", "churn_flag"])

RANDOM_STATE = 42
NUM_F, CAT_F = FEATURE_SETS["base+engineered"]

# Stratified split with a fixed seed; the test set stays untouched until final evaluation.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
print(f"train: {X_train.shape}, test: {X_test.shape}")
print(f"churn rate  train: {y_train.mean():.4f}  test: {y_test.mean():.4f}")

MODELS = ["logistic_regression", "random_forest", "xgboost"]
SPW = (y_train == 0).sum() / (y_train == 1).sum()
print(f"scale_pos_weight (n_neg/n_pos): {SPW:.2f}")
"""

cells = [
    ("md", "# 04 — Machine Learning\n\n"
     "Binary classification of `Churn` (Yes=1, No=0). Pipeline: class-imbalance comparison and model comparison via "
     "5-fold stratified CV **on the training set only**, hyperparameter tuning on the training set, and a single final "
     "unbiased evaluation on the held-out test set. `customerID` is excluded from features. All preprocessing lives "
     "inside the pipeline (fitted on training folds only)."),
    ("code", SETUP4),
    ("md", "## 1. Class imbalance — strategy comparison\n\nThe dataset is imbalanced (~26.5% churners). Three defensible strategies are compared on the "
     "training set: no correction, cost-sensitive weighting (`class_weight='balanced'` / `scale_pos_weight`), and SMOTE "
     "(inside an imblearn pipeline, so it is applied **only to training folds** — never to validation or test data)."),
    ("code", "from src.models.evaluate import CV as cv_split\nfrom sklearn.model_selection import cross_validate\n\nSCORING = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'average_precision']\n\ndef imb_pipeline(model_name, strategy):\n    if strategy == 'none':\n        return build_pipeline(model_name, NUM_F, CAT_F)\n    if strategy == 'weight':\n        return build_pipeline(model_name, NUM_F, CAT_F, imbalance='class_weight' if model_name != 'xgboost' else 'scale_pos_weight', scale_pos_weight=SPW)\n    if strategy == 'smote':\n        return build_smote_pipeline(model_name, NUM_F, CAT_F)\n    raise ValueError(strategy)\n\nrows = []\nfor model_name in MODELS:\n    for strategy in ['none', 'weight', 'smote']:\n        pipe = imb_pipeline(model_name, strategy)\n        res = cross_validate(pipe, X_train, y_train, cv=cv_split, scoring=SCORING, n_jobs=-1)\n        rows.append({\n            'model': model_name, 'strategy': strategy,\n            'recall': res['test_recall'].mean(),\n            'precision': res['test_precision'].mean(),\n            'f1': res['test_f1'].mean(),\n            'roc_auc': res['test_roc_auc'].mean(),\n            'pr_auc': res['test_average_precision'].mean(),\n        })\nimbalance_table = pd.DataFrame(rows)\nprint(imbalance_table.round(4).to_string(index=False))"),
    ("md", "## 2. Imbalance decision\n\nSelection criterion: **F1** as the balanced headline (recall matters for churn, but precision drives intervention cost), "
     "with ROC-AUC/PR-AUC as ranking-quality sanity checks."),
    ("code", "best_row = imbalance_table.sort_values('f1', ascending=False).iloc[0]\nBEST_MODEL, BEST_STRATEGY = best_row['model'], best_row['strategy']\nprint(imbalance_table.round(4).to_string(index=False))\nprint(f'\\nselected: {BEST_MODEL} + {BEST_STRATEGY} (cv F1={best_row[\"f1\"]:.4f})')"),
    ("md", "## 3. Model comparison (selected imbalance strategy)\n\nLogistic Regression = interpretable baseline, Random Forest = nonlinear tree ensemble, XGBoost = gradient boosting. "
     "No assumption about the winner in advance."),
    ("code", "rows = []\nfor model_name in MODELS:\n    pipe = imb_pipeline(model_name, BEST_STRATEGY)\n    scores = cv_scores(pipe, X_train, y_train)\n    rows.append({'model': model_name, **scores})\ncomparison = pd.DataFrame(rows).set_index('model')\nprint(comparison.round(4).to_string())\n\n(PROJECT_ROOT / 'reports').mkdir(exist_ok=True)\ncomparison.round(4).to_csv(PROJECT_ROOT / 'reports' / 'model_comparison_cv.csv')"),
    ("md", "## 4. Hyperparameter tuning (training data only)\n\nRandomizedSearchCV with 5-fold stratified CV on the training set, scored by F1. The test set is not involved."),
    ("code", "from sklearn.model_selection import RandomizedSearchCV\nfrom scipy.stats import randint, uniform\n\nif BEST_MODEL == 'xgboost':\n    base = imb_pipeline('xgboost', BEST_STRATEGY)\n    space = {\n        'model__n_estimators': randint(150, 500),\n        'model__learning_rate': uniform(0.02, 0.18),\n        'model__max_depth': randint(3, 8),\n        'model__subsample': uniform(0.7, 0.3),\n        'model__colsample_bytree': uniform(0.7, 0.3),\n        'model__min_child_weight': randint(1, 6),\n        'model__gamma': uniform(0, 0.4),\n    }\nelif BEST_MODEL == 'random_forest':\n    base = imb_pipeline('random_forest', BEST_STRATEGY)\n    space = {\n        'model__n_estimators': randint(200, 600),\n        'model__max_depth': randint(4, 16),\n        'model__min_samples_leaf': randint(1, 8),\n        'model__max_features': ['sqrt', 'log2'],\n    }\nelse:\n    base = imb_pipeline('logistic_regression', BEST_STRATEGY)\n    space = {\n        'model__C': uniform(0.01, 3.0),\n        'model__solver': ['lbfgs', 'liblinear'],\n    }\n\nsearch = RandomizedSearchCV(\n    base, space, n_iter=25, cv=cv_split, scoring='f1',\n    random_state=RANDOM_STATE, n_jobs=-1, refit=True,\n)\nsearch.fit(X_train, y_train)\nprint('best CV F1:', round(search.best_score_, 4))\nprint('best params:', search.best_params_)"),
    ("md", "## 5. Final unbiased evaluation on the test set (used once)\n\nMetrics: accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix. Accuracy alone is never the decision metric."),
    ("code", "final_model = search.best_estimator_\ny_prob_test = final_model.predict_proba(X_test)[:, 1]\ntest_metrics = classification_metrics(y_test, y_prob_test, threshold=0.5)\nfor k, v in test_metrics.items():\n    print(f'{k}: {v}')\n\n(PROJECT_ROOT / 'reports' / 'final_test_metrics.json').write_text(json.dumps({k: v for k, v in test_metrics.items()}, indent=2))"),
    ("code", "cm = np.array(test_metrics['confusion_matrix'])\nlabels = ['No churn (0)', 'Churn (1)']\nfig, ax = plt.subplots(figsize=(4.5, 4))\nConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=ax, cmap='Blues', colorbar=False)\nax.set_title('Test-set confusion matrix (threshold 0.5)')\nfig.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'confusion_matrix_test.png', dpi=150, bbox_inches='tight')\nplt.show()\n\ntn, fp, fn, tp = cm.ravel()\nprint(f'True positives  ({tp}): churners correctly flagged -> retention outreach reaches them.')\nprint(f'False negatives ({fn}): missed churners -> retention opportunity lost (the costliest error for the business).')\nprint(f'False positives ({fp}): would have stayed but flagged -> unnecessary intervention cost (offer/discount).')\nprint(f'True negatives  ({tn}): correctly excluded -> no wasted outreach.')"),
    ("md", "## 6. Threshold analysis on out-of-fold training probabilities\n\nThe decision threshold (0.5 by default) is not necessarily the best operating point. Out-of-fold probabilities from "
     "CV on the **training set** are used to see precision/recall/F1 across candidate thresholds. This analysis also "
     "justifies the risk-level cutoffs used for customer scoring (Phase 8)."),
    ("code", "oof_prob = cross_val_predict(final_model, X_train, y_train, cv=cv_split, method='predict_proba', n_jobs=-1)[:, 1]\nth = threshold_analysis(y_train, oof_prob)\nprint(th.round(3).to_string(index=False))\nth.round(3).to_csv(PROJECT_ROOT / 'reports' / 'threshold_analysis.csv', index=False)"),
    ("code", "# Threshold selection (both rules are computed from OOF training behaviour, not chosen arbitrarily):\n# HIGH  = probability cutoff maximizing F1 -> the balanced operating point for proactive, costlier retention outreach.\n# MEDIUM = cutoff maximizing F2 (recall weighted 2x) among cutoffs below High -> a broad capture layer for cheap\n#          interventions (emails/notifications), where tolerating lower precision buys more recall.\nhigh_threshold = float(th.loc[th['f1'].idxmax(), 'threshold'])\nbelow_high = th[th['threshold'] < high_threshold]\nmedium_threshold = float(below_high.loc[below_high['f2'].idxmax(), 'threshold']) if len(below_high) else high_threshold\nprint(f'HIGH risk threshold:  {high_threshold:.2f}  (OOF precision={th.loc[th['f1'].idxmax(), 'precision']:.3f}, recall={th.loc[th['f1'].idxmax(), 'recall']:.3f})')\nprint(f'MEDIUM risk threshold: {medium_threshold:.2f}')\n\nfig, ax = plt.subplots(figsize=(7, 4))\nax.plot(th['threshold'], th['precision'], label='precision')\nax.plot(th['threshold'], th['recall'], label='recall')\nax.plot(th['threshold'], th['f1'], label='F1')\nax.plot(th['threshold'], th['f2'], label='F2')\nax.axvline(high_threshold, color='red', ls='--', label=f'High cut ({high_threshold:.2f})')\nax.axvline(medium_threshold, color='orange', ls='--', label=f'Medium cut ({medium_threshold:.2f})')\nax.set(xlabel='probability threshold', ylabel='score', title='Precision / recall / F1 vs threshold (OOF training probabilities)')\nax.legend()\nfig.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'threshold_analysis.png', dpi=150, bbox_inches='tight')\nplt.show()"),
    ("md", "## 7. Save the final model + metadata"),
    ("code", "models_dir = PROJECT_ROOT / 'models'\nmodels_dir.mkdir(exist_ok=True)\njoblib.dump(final_model, models_dir / 'final_model.joblib')\n\nmeta = {\n    'model': BEST_MODEL,\n    'imbalance_strategy': BEST_STRATEGY,\n    'best_params': {k: (v.item() if hasattr(v, 'item') else v) for k, v in search.best_params_.items()},\n    'cv_f1_train': float(search.best_score_),\n    'test_metrics': {k: v for k, v in test_metrics.items()},\n    'high_threshold': high_threshold,\n    'medium_threshold': medium_threshold,\n    'random_state': RANDOM_STATE,\n    'features': NUM_F + CAT_F,\n}\n(models_dir / 'model_metadata.json').write_text(json.dumps(meta, indent=2, default=str))\nprint('saved models/final_model.joblib and models/model_metadata.json')\nprint('selected final model:', BEST_MODEL, '+', BEST_STRATEGY)"),
    ("md", "## Model selection rationale\n\n"
     "- The imbalance strategy and model family were chosen by 5-fold CV **on the training set** using F1 as the headline metric, with the business reading of the confusion matrix (a missed churner costs a retention opportunity; a false positive costs one unnecessary intervention). Weighted Logistic Regression won on F1 *and* is the most interpretable family, which suits per-customer retention conversations.\n"
     "- The test set was evaluated exactly once, after tuning, so reported test metrics are unbiased.\n"
     "- Final thresholds are data-driven: HIGH = F1-maximizing cutoff; MEDIUM = F2-maximizing (recall-weighted) cutoff below High — both derived from out-of-fold training probabilities rather than arbitrary choices."),
]

if __name__ == "__main__":
    build_notebook(ROOT / "notebooks" / "04_machine_learning.ipynb", cells)
    print("built notebooks/04_machine_learning.ipynb")
