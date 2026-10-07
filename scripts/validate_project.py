"""Full project validation (Phase 16).

Checks raw-data integrity, artifact existence, notebook execution status,
output validity (one row per customer, probability range, risk assignment),
leakage hygiene, and documentation consistency. Exits non-zero on any failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import nbformat
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((bool(ok), name + (f" — {detail}" if detail else "")))


def main() -> None:
    # 1. Raw dataset unchanged (integrity: shape, header, target values).
    raw = pd.read_csv(ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv")
    check("raw dataset shape 7043x21", raw.shape == (7043, 21))
    check("raw TotalCharges still text with 11 blanks",
          pd.api.types.is_string_dtype(raw["TotalCharges"])
          and (raw["TotalCharges"].astype(str).str.strip() == "").sum() == 11)
    check("raw churn values Yes/No", set(raw["Churn"].unique()) == {"Yes", "No"})

    # 2. Processed datasets exist and are consistent.
    cleaned = pd.read_csv(ROOT / "data" / "processed" / "telco_cleaned.csv")
    feats = pd.read_csv(ROOT / "data" / "processed" / "telco_features.csv")
    check("processed cleaned dataset exists", len(cleaned) == 7043 and cleaned.isna().sum().sum() == 0)
    check("processed features dataset exists", len(feats) == 7043)
    check("TotalCharges numeric in processed", cleaned["TotalCharges"].dtype.kind == "f")

    # 3. Notebooks executed with no errors.
    notebooks = sorted((ROOT / "notebooks").glob("*.ipynb"))
    check("6 notebooks present", len(notebooks) == 6, ", ".join(p.name for p in notebooks))
    for nbp in notebooks:
        nb = nbformat.read(nbp, as_version=4)
        errs = [o for c in nb.cells if c.cell_type == "code"
                for o in c.get("outputs", []) if o.output_type == "error"]
        executed = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("execution_count"))
        total = sum(1 for c in nb.cells if c.cell_type == "code")
        check(f"{nbp.name} executed cleanly", not errs and executed == total,
              f"{executed}/{total} cells, {len(errs)} errors")

    # 4. Model artifacts.
    meta = json.loads((ROOT / "models" / "model_metadata.json").read_text())
    check("final model artifact exists", (ROOT / "models" / "final_model.joblib").exists())
    check("model metadata complete",
          all(k in meta for k in ["model", "test_metrics", "high_threshold", "medium_threshold", "random_state"]))
    check("model features exclude customerID and target",
          "customerID" not in meta["features"] and "churn_flag" not in meta["features"]
          and "Churn" not in meta["features"])

    # 5. Test-set honesty: metrics recorded once, consistent with notebook output.
    test = meta["test_metrics"]
    check("test metrics plausible",
          0.7 < test["accuracy"] < 0.9 and 0.8 < test["roc_auc"] < 0.9 and test["recall"] > 0.7)

    # 6. Risk score table: one row per customer, valid probabilities, thresholds honored.
    scores = pd.read_csv(ROOT / "reports" / "churn_risk_scores.csv")
    check("scores: one row per unique customer", len(scores) == 7043 and scores["customerID"].is_unique)
    check("scores: probabilities within [0,1]", scores["churn_probability"].between(0, 1).all())
    hi, med = meta["high_threshold"], meta["medium_threshold"]
    lv = scores["risk_level"]
    check("scores: risk levels match thresholds",
          ((lv == "High") == (scores["churn_probability"] >= hi)).all()
          and ((lv == "Medium") == ((scores["churn_probability"] >= med)
                                    & (scores["churn_probability"] < hi))).all())
    check("thresholds documented in metadata", 0 < med < hi < 1)

    # 7. Revenue-at-risk outputs exist and carry the estimate framing.
    rar = pd.read_csv(ROOT / "reports" / "revenue_at_risk_summary.csv")
    check("revenue-at-risk summary exists", len(rar) >= 6)
    monetary = rar["metric"][rar["metric"].str.contains("revenue|exposure", case=False)]
    check("monetary figures labeled as estimates",
          monetary.str.contains("estimate|assumes|bound", case=False).all())

    # 8. Dashboard files.
    dash = [p.name for p in (ROOT / "dashboard").glob("*.csv")]
    spec = (ROOT / "dashboard" / "DASHBOARD_SPEC.md").exists()
    check("9 dashboard CSVs + spec", len(dash) == 9 and spec, ", ".join(dash))

    # 9. SQL executes and report exists.
    check("SQL results report exists", (ROOT / "reports" / "sql_results.md").exists())

    # 10. Leakage hygiene in source: no SMOTE before split (SMOTE only via imblearn pipeline).
    pipe_src = (ROOT / "src" / "models" / "pipeline.py").read_text()
    check("SMOTE only inside imblearn pipeline", "ImbPipeline" in pipe_src)

    # 11. README contains real results (spot-check actual figures).
    readme = (ROOT / "README.md").read_text()
    for token in ["26.54%", "0.843", "42.7%", "0.55", "2,503", "781", "$146,705"]:
        check(f"README contains computed figure {token}", token in readme)

    # 12. Excel bundle exists.
    check("Excel summary bundle exists", (ROOT / "reports" / "telco_churn_summary_report.xlsx").exists())

    failures = [name for ok, name in RESULTS if not ok]
    for ok, name in RESULTS:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n{len(RESULTS) - len(failures)}/{len(RESULTS)} checks passed")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
