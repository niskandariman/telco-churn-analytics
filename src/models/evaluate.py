"""Evaluation utilities: cross-validation, held-out test metrics, threshold analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

RANDOM_STATE = 42
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)


def cv_scores(model, X, y, scoring=None) -> dict:
    """5-fold stratified CV on training data; returns mean of each metric."""
    scoring = scoring or ["accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]
    res = cross_validate(model, X, y, cv=CV, scoring=scoring, n_jobs=-1)
    return {f"cv_{k.replace('_score', '')}": float(v.mean()) for k, v in res.items() if k.startswith("test_")}


def classification_metrics(y_true, y_prob, threshold: float = 0.5) -> dict:
    """Full metric set at a given decision threshold plus probability metrics."""
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def threshold_analysis(y_true, y_prob, thresholds=None) -> pd.DataFrame:
    """Precision/recall/F1/flagged-share at candidate probability thresholds.

    Used to justify risk-level cutoffs from validation behaviour instead of
    picking arbitrary values.
    """
    if thresholds is None:
        thresholds = np.round(np.arange(0.05, 0.96, 0.05), 2)
    rows = []
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        p = precision_score(y_true, y_pred, zero_division=0)
        r = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        # F2 (beta=2) weights recall twice as much as precision - used for the
        # "broad capture" Medium-risk cutoff where interventions are cheap.
        f2 = 5 * p * r / (4 * p + r) if (4 * p + r) > 0 else 0.0
        rows.append({
            "threshold": t,
            "precision": p,
            "recall": r,
            "f1": f1,
            "f2": f2,
            "share_flagged": float(y_pred.mean()),
            "flagged_customers": int(y_pred.sum()),
        })
    return pd.DataFrame(rows)
