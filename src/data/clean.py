"""Data loading and cleaning utilities for the Telco churn project.

The raw dataset under ``data/raw/`` is immutable: every function here returns a
new DataFrame and never writes to the raw directory. Cleaned outputs are
written to ``data/processed/`` by the caller (notebook 01).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

EXPECTED_COLUMNS = [
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents",
    "tenure", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling",
    "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn",
]

CATEGORICAL_DOMAINS = {
    "gender": {"Female", "Male"},
    "Partner": {"Yes", "No"},
    "Dependents": {"Yes", "No"},
    "PhoneService": {"Yes", "No"},
    "MultipleLines": {"Yes", "No", "No phone service"},
    "InternetService": {"DSL", "Fiber optic", "No"},
    "OnlineSecurity": {"Yes", "No", "No internet service"},
    "OnlineBackup": {"Yes", "No", "No internet service"},
    "DeviceProtection": {"Yes", "No", "No internet service"},
    "TechSupport": {"Yes", "No", "No internet service"},
    "StreamingTV": {"Yes", "No", "No internet service"},
    "StreamingMovies": {"Yes", "No", "No internet service"},
    "Contract": {"Month-to-month", "One year", "Two year"},
    "PaperlessBilling": {"Yes", "No"},
    "PaymentMethod": {
        "Bank transfer (automatic)", "Credit card (automatic)",
        "Electronic check", "Mailed check",
    },
    "Churn": {"Yes", "No"},
}


def load_raw(path: Path | str = RAW_PATH) -> pd.DataFrame:
    """Load the immutable raw CSV."""
    return pd.read_csv(path)


def profile_dataset(df: pd.DataFrame) -> dict:
    """Compute the data-quality profile used by the cleaning notebook."""
    string_cols = df.select_dtypes(include=["object", "string"]).columns
    numeric_cols = df.select_dtypes(include=["number"]).columns
    total_charges_num = pd.to_numeric(df["TotalCharges"], errors="coerce")

    profile = {
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_by_column": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_customer_ids": int(df["customerID"].duplicated().sum()),
        "whitespace_hits": {
            c: int(df[c].astype(str).str.contains(r"^\s|\s$", regex=True).sum())
            for c in string_cols
        },
        "blank_string_counts": {
            c: int((df[c].astype(str).str.strip() == "").sum()) for c in string_cols
        },
        "total_charges_non_numeric": int(total_charges_num.isna().sum()),
        "total_charges_non_numeric_tenure": df.loc[
            total_charges_num.isna(), "tenure"
        ].tolist(),
        "total_charges_non_numeric_churn": df.loc[
            total_charges_num.isna(), "Churn"
        ].tolist(),
        "unexpected_category_values": {
            c: sorted(set(df[c].dropna()) - domain)
            for c, domain in CATEGORICAL_DOMAINS.items()
            if set(df[c].dropna()) - domain
        },
        "numeric_summary": df[numeric_cols].describe().to_dict(),
        "total_charges_numeric_summary": total_charges_num.describe().to_dict(),
    }
    return profile


def clean_telco(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw Telco dataset.

    Returns the cleaned DataFrame and a log of every decision/transform so the
    cleaning notebook can report exactly what happened. The raw data is never
    modified (all operations are non-inplace on a copy).

    Decisions:
    * String columns are defensively stripped of surrounding whitespace.
    * ``TotalCharges`` is converted to float. The 11 blank values all belong to
      ``tenure == 0`` customers who have not been billed yet, so their true
      total charged to date is 0 - they are set to 0.0 rather than imputed or
      dropped (documented in notebook 01 and DATA_DICTIONARY.md).
    """
    log: dict = {}
    df = df.copy()

    # 1. Defensive whitespace trim on string columns.
    string_cols = df.select_dtypes(include=["object", "string"]).columns
    for c in string_cols:
        df[c] = df[c].str.strip()
    log["stripped_columns"] = list(string_cols)

    # 2. Integrity checks (duplicates).
    log["duplicate_rows_removed"] = int(df.duplicated().sum())
    df = df.drop_duplicates()
    log["duplicate_customer_ids"] = int(df["customerID"].duplicated().sum())

    # 3. TotalCharges -> numeric.
    raw_tc = df["TotalCharges"]
    tc_num = pd.to_numeric(raw_tc, errors="coerce")
    bad_mask = tc_num.isna()
    log["total_charges_blanks"] = int(bad_mask.sum())
    log["total_charges_blank_tenure_values"] = sorted(
        df.loc[bad_mask, "tenure"].unique().tolist()
    )
    log["total_charges_blank_all_tenure_zero"] = bool(
        (df.loc[bad_mask, "tenure"] == 0).all()
    )
    log["total_charges_blank_churn_values"] = df.loc[bad_mask, "Churn"].unique().tolist()
    log["total_charges_treatment"] = (
        "Blank values set to 0.0: all belong to tenure=0 customers who have "
        "not yet been billed, so zero is their true total charged to date "
        "(not a statistical imputation)."
    )
    df["TotalCharges"] = tc_num.fillna(0.0)

    # 4. Type normalization (SeniorCitizen is already int64 0/1).
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(int)
    df["tenure"] = df["tenure"].astype(int)

    return df, log


def validate_cleaned(df: pd.DataFrame) -> dict:
    """Post-cleaning assertions; raises if any check fails."""
    checks = {
        "shape_is_7043x21": df.shape == (7043, 21),
        "no_missing_values": bool(df.isna().sum().sum() == 0),
        "no_duplicate_customer_ids": bool(df["customerID"].is_unique),
        "total_charges_numeric": bool(pd.api.types.is_float_dtype(df["TotalCharges"])),
        "total_charges_non_negative": bool((df["TotalCharges"] >= 0).all()),
        "tenure_range_0_72": bool(df["tenure"].between(0, 72).all()),
        "monthly_charges_positive": bool((df["MonthlyCharges"] > 0).all()),
        "churn_binary": bool(set(df["Churn"].unique()) == {"Yes", "No"}),
        "no_unexpected_categories": all(
            set(df[c].unique()) == domain for c, domain in CATEGORICAL_DOMAINS.items()
        ),
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise ValueError(f"Validation failed: {failed}")
    return checks


def save_processed(df: pd.DataFrame, name: str = "telco_cleaned.csv") -> Path:
    """Write a cleaned dataset to data/processed/ and return its path."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / name
    df.to_csv(out, index=False)
    return out
