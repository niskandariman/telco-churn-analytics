"""Churn risk scoring, revenue-at-risk estimation, segmentation and retention prioritization.

All outputs are estimates built from the model's probabilities; predicted churn
is never treated as guaranteed lost revenue (documented in notebook 06).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Value definition: current monthly revenue run-rate. The top quartile of
# MonthlyCharges is treated as "high value" (forward-looking revenue exposure).
VALUE_QUANTILES = 4


def score_customers(df: pd.DataFrame, model, high_threshold: float,
                    medium_threshold: float) -> pd.DataFrame:
    """Score every customer with the final model and assign risk levels.

    Risk rules (documented in notebook 04):
      High   : probability >= high_threshold   (F1-maximizing cutoff)
      Medium : medium_threshold <= p < high    (F2-maximizing broad-capture cutoff)
      Low    : p < medium_threshold
    """
    probs = model.predict_proba(
        df.drop(columns=["customerID", "Churn", "churn_flag"], errors="ignore")
    )[:, 1]
    scores = pd.DataFrame({
        "customerID": df["customerID"].values,
        "churn_probability": probs,
    })
    scores["risk_level"] = np.select(
        [scores["churn_probability"] >= high_threshold,
         scores["churn_probability"] >= medium_threshold],
        ["High", "Medium"],
        default="Low",
    )
    return scores


def validate_scores(scores: pd.DataFrame, df: pd.DataFrame) -> dict:
    checks = {
        "one_row_per_customer": len(scores) == len(df)
        and scores["customerID"].is_unique,
        "probability_in_0_1": bool(scores["churn_probability"].between(0, 1).all()),
        "risk_levels_valid": bool(set(scores["risk_level"].unique()) <= {"High", "Medium", "Low"}),
        "no_missing": bool(scores.notna().all().all()),
    }
    if not all(checks.values()):
        raise ValueError(f"score validation failed: {checks}")
    return checks


def add_value_tier(df: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Join value quartiles (1 = lowest, 4 = highest) onto the score table."""
    quartile = pd.qcut(df["MonthlyCharges"], q=VALUE_QUANTILES, labels=[1, 2, 3, 4]).astype(int)
    out = scores.merge(
        pd.DataFrame({
            "customerID": df["customerID"],
            "MonthlyCharges": df["MonthlyCharges"].values,
            "value_quartile": quartile,
        }),
        on="customerID",
    )
    out["value_tier"] = np.where(out["value_quartile"] == 4, "High value", "Standard value")
    return out


def revenue_at_risk(scored: pd.DataFrame) -> dict:
    """Estimated revenue exposure among High-risk customers.

    Two estimates, both clearly labeled:
      - run-rate exposure: monthly revenue of all High-risk customers (upper bound;
        assumes every high-risk customer is lost).
      - probability-weighted exposure: sum(p_i * monthly_i) - reflects the model's
        confidence and is the fairer headline estimate.
    """
    high = scored[scored["risk_level"] == "High"]
    return {
        "high_risk_customers": int(len(high)),
        "monthly_revenue_high_risk": float(high["MonthlyCharges"].sum()),
        "annualized_exposure_high_risk_x12": float(high["MonthlyCharges"].sum() * 12),
        "probability_weighted_monthly_exposure": float(
            (high["churn_probability"] * high["MonthlyCharges"]).sum()
        ),
        "high_risk_high_value_customers": int((high["value_quartile"] == 4).sum()),
        "monthly_revenue_high_risk_high_value": float(
            high.loc[high["value_quartile"] == 4, "MonthlyCharges"].sum()
        ),
    }


def add_priority_score(scored: pd.DataFrame) -> pd.DataFrame:
    """Retention priority = churn probability x monthly revenue.

    Rationale: expected monthly revenue exposure if the customer churns. A
    high-probability low-value customer and a moderate-probability high-value
    customer can rank similarly - which matches how a retention team should
    spend its time. Not a causal or financial-precision measure; a ranking tool.
    """
    out = scored.copy()
    out["priority_score"] = out["churn_probability"] * out["MonthlyCharges"]
    return out.sort_values("priority_score", ascending=False).reset_index(drop=True)


def segment_summary(scored: pd.DataFrame) -> pd.DataFrame:
    """Business segments: risk level x value tier, quantified."""
    seg = scored.groupby(["risk_level", "value_tier"]).agg(
        customers=("customerID", "count"),
        monthly_revenue=("MonthlyCharges", "sum"),
        avg_churn_probability=("churn_probability", "mean"),
    ).reset_index()
    seg["share_of_customers"] = seg["customers"] / seg["customers"].sum()
    seg["share_of_monthly_revenue"] = seg["monthly_revenue"] / seg["monthly_revenue"].sum()
    return seg
