"""Bundle the project's key outputs into one Excel workbook for easy inspection.

Reads only existing report artifacts (no recomputation) so the workbook always
agrees with the notebooks' outputs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PROJECT_ROOT / "reports"
DASH = PROJECT_ROOT / "dashboard"
MODELS = PROJECT_ROOT / "models"


def main() -> None:
    meta = json.loads((MODELS / "model_metadata.json").read_text())
    test = meta["test_metrics"]
    scores = pd.read_csv(REPORTS / "churn_risk_scores.csv")
    kpis = pd.read_csv(DASH / "kpi_summary.csv").set_index("kpi")["value"]

    hvhr = pd.read_csv(REPORTS / "high_value_high_risk_customers.csv")

    executive = pd.DataFrame(
        [
            ("Dataset", "Telco Customer Churn (IBM sample), 7,043 customers x 21 columns"),
            ("Overall churn rate", "26.54% (1,869 of 7,043)"),
            ("Final model", f"{meta['model']} ({meta['imbalance_strategy']} imbalance handling)"),
            ("Test ROC-AUC", f"{test['roc_auc']:.3f}"),
            ("Test recall (churners caught)", f"{test['recall']:.1%}"),
            ("Test precision", f"{test['precision']:.1%}"),
            ("Test F1", f"{test['f1']:.3f}"),
            ("High-risk customers (p >= 0.55)", f"{int((scores['risk_level'] == 'High').sum()):,}"),
            ("Medium-risk customers (0.35 <= p < 0.55)", f"{int((scores['risk_level'] == 'Medium').sum()):,}"),
            ("Low-risk customers (p < 0.35)", f"{int((scores['risk_level'] == 'Low').sum()):,}"),
            ("Estimated monthly revenue at risk (probability-weighted)",
             f"${kpis['estimated_monthly_revenue_at_risk']:,.0f}"),
            ("Estimated annualized revenue at risk (monthly estimate x 12)",
             f"${kpis['estimated_annualized_revenue_at_risk']:,.0f}"),
            ("High-risk + high-value customers",
             f"{len(hvhr):,} (${hvhr['MonthlyCharges'].sum():,.0f} monthly revenue)"),
        ],
        columns=["Item", "Value"],
    )

    threshold_note = pd.DataFrame(
        [
            ("High threshold", meta["high_threshold"], "F1-maximizing cutoff on out-of-fold training probabilities"),
            ("Medium threshold", meta["medium_threshold"], "F2-maximizing (recall-weighted) cutoff below High"),
        ],
        columns=["Parameter", "Value", "Justification"],
    )

    with pd.ExcelWriter(REPORTS / "telco_churn_summary_report.xlsx", engine="openpyxl") as xl:
        executive.to_excel(xl, sheet_name="Executive Summary", index=False)
        pd.read_csv(REPORTS / "model_comparison_cv.csv").to_excel(xl, sheet_name="Model Comparison (CV)", index=False)
        pd.DataFrame([test]).drop(columns=["confusion_matrix"]).round(4).to_excel(
            xl, sheet_name="Final Test Metrics", index=False)
        threshold_note.to_excel(xl, sheet_name="Thresholds", index=False)
        pd.read_csv(REPORTS / "threshold_analysis.csv").to_excel(xl, sheet_name="Threshold Analysis", index=False)
        pd.read_csv(REPORTS / "revenue_at_risk_summary.csv").to_excel(
            xl, sheet_name="Revenue at Risk", index=False)
        pd.read_csv(REPORTS / "business_segments.csv").to_excel(xl, sheet_name="Business Segments", index=False)
        pd.read_csv(REPORTS / "top_model_features.csv").to_excel(xl, sheet_name="Top Model Features", index=False)
        pd.read_csv(DASH / "retention_priority_top200.csv").to_excel(
            xl, sheet_name="Retention Top 200", index=False)
        scores.head(1000).to_excel(xl, sheet_name="Risk Scores (first 1000)", index=False)

        widths = {"Executive Summary": [52, 46]}
        for name, sheet_widths in widths.items():
            ws = xl.sheets[name]
            for i, w in enumerate(sheet_widths, start=1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    print("written:", REPORTS / "telco_churn_summary_report.xlsx")


if __name__ == "__main__":
    main()
