"""Model pipelines and preprocessing for the Telco churn project.

All preprocessing lives inside scikit-learn Pipelines so that imputers,
scalers and encoders are fitted on training data only - never on the full
dataset. customerID is never passed to the model; it is used only as an index.
"""

from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

RANDOM_STATE = 42

BASE_NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]
BASE_CATEGORICAL = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]

ENGINEERED_NUMERIC = ["addon_count", "service_breadth", "avg_monthly_to_date",
                      "auto_payment", "fiber_no_protection", "has_addon_services"]
ENGINEERED_CATEGORICAL = ["tenure_band"]

FEATURE_SETS = {
    "base": (BASE_NUMERIC, BASE_CATEGORICAL),
    "base+engineered": (
        BASE_NUMERIC + ENGINEERED_NUMERIC,
        BASE_CATEGORICAL + ENGINEERED_CATEGORICAL,
    ),
}


def build_preprocessor(num_features: list[str], cat_features: list[str]) -> ColumnTransformer:
    """Preprocessing: scale numerics (needed by LR), one-hot categoricals."""
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("num", numeric, num_features),
        ("cat", categorical, cat_features),
    ], verbose_feature_names_out=True)


def build_model(name: str, imbalance: str = "none", random_state: int = RANDOM_STATE,
                scale_pos_weight: float | None = None):
    """Return an unfitted estimator for a given model family.

    imbalance:
      - "none": no correction
      - "class_weight": class_weight='balanced' (LR/RF)
      - "scale_pos_weight": XGBoost scale_pos_weight (default n_neg / n_pos)
    """
    if name == "logistic_regression":
        kwargs = {"class_weight": "balanced"} if imbalance == "class_weight" else {}
        return LogisticRegression(max_iter=2000, random_state=random_state, **kwargs)
    if name == "random_forest":
        kwargs = {"class_weight": "balanced"} if imbalance == "class_weight" else {}
        return RandomForestClassifier(
            n_estimators=300, random_state=random_state, n_jobs=-1, **kwargs)
    if name == "xgboost":
        spw = scale_pos_weight if imbalance == "scale_pos_weight" else None
        kwargs = {"scale_pos_weight": spw} if spw is not None else {}
        return XGBClassifier(
            n_estimators=300, learning_rate=0.1, max_depth=6,
            eval_metric="logloss", tree_method="hist",
            random_state=random_state, n_jobs=-1, **kwargs)
    raise ValueError(f"unknown model: {name}")


def build_pipeline(name: str, num_features: list[str], cat_features: list[str],
                   imbalance: str = "none", random_state: int = RANDOM_STATE,
                   scale_pos_weight: float | None = None) -> Pipeline:
    return Pipeline([
        ("preprocessor", build_preprocessor(num_features, cat_features)),
        ("model", build_model(name, imbalance, random_state, scale_pos_weight)),
    ])


def build_smote_pipeline(name: str, num_features: list[str], cat_features: list[str],
                         random_state: int = RANDOM_STATE):
    """Pipeline with SMOTE applied to the (preprocessed) training data only.

    Using an imblearn Pipeline means SMOTE runs inside every CV fold on the
    training portion of that fold - never on validation/test data.
    """
    from imblearn.over_sampling import SMOTE
    from imblearn.pipeline import Pipeline as ImbPipeline

    return ImbPipeline([
        ("preprocessor", build_preprocessor(num_features, cat_features)),
        ("smote", SMOTE(random_state=random_state)),
        ("model", build_model(name, "none", random_state)),
    ])


def feature_names_from_pipeline(pipe: Pipeline) -> np.ndarray:
    """Output feature names of the fitted preprocessor."""
    return pipe.named_steps["preprocessor"].get_feature_names_out()
