"""Feature engineering for the Telco churn project.

Every feature here is computable from a customer's account state *before*
churn occurs - no target information is used. The engineered dataset is
written to data/processed/telco_features.csv by notebook 03.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ADDON_COLS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]

TENURE_BANDS = [0, 6, 12, 24, 48, 72]
TENURE_LABELS = ["0-6 mo", "7-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"]

ENGINEERED_FEATURES = [
    "tenure_band",
    "addon_count",
    "has_addon_services",
    "service_breadth",
    "avg_monthly_to_date",
    "auto_payment",
    "fiber_no_protection",
]

# Rationale for each engineered feature (documented in notebook 03):
# tenure_band: churn risk is concentrated in the first year (EDA); a binned
#   version lets linear models capture the strongly non-linear tenure effect.
# addon_count / has_addon_services: customers with more add-on services churn
#   markedly less (EDA); breadth of the bundle is a stickiness signal.
# service_breadth: total services owned (phone + internet + add-ons).
# avg_monthly_to_date: TotalCharges / tenure = average effective monthly charge
#   over the customer's lifetime. For tenure=0 customers no billing exists, so
#   the value is defined as 0.0 (documented, not imputed).
# auto_payment: automatic payments (bank transfer / credit card) are associated
#   with far lower churn than manual methods in EDA.
# fiber_no_protection: fiber-optic users without OnlineSecurity/DeviceProtection
#   combine the two strongest EDA churn signals in one segment.


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the cleaned dataset with engineered features added."""
    out = df.copy()

    out["tenure_band"] = pd.cut(
        out["tenure"], bins=TENURE_BANDS, labels=TENURE_LABELS,
        right=True, include_lowest=True,
    ).astype(str)

    out["addon_count"] = (out[ADDON_COLS] == "Yes").sum(axis=1).astype(int)
    out["has_addon_services"] = (out["addon_count"] > 0).astype(int)

    out["service_breadth"] = (
        (out["PhoneService"] == "Yes").astype(int)
        + (out["InternetService"] != "No").astype(int)
        + out["addon_count"]
    )

    safe_tenure = out["tenure"].where(out["tenure"] > 0)
    out["avg_monthly_to_date"] = (out["TotalCharges"] / safe_tenure).fillna(0.0).round(2)

    out["auto_payment"] = out["PaymentMethod"].str.contains("automatic").astype(int)

    out["fiber_no_protection"] = (
        (out["InternetService"] == "Fiber optic")
        & (out["OnlineSecurity"] == "No")
        & (out["DeviceProtection"] == "No")
    ).astype(int)

    return out


def save_features(df: pd.DataFrame, name: str = "telco_features.csv"):
    from src.data.clean import PROCESSED_DIR

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / name
    df.to_csv(out, index=False)
    return out
