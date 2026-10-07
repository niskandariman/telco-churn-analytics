"""Build notebooks/01_data_cleaning.ipynb."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nbbuild import build_notebook

ROOT = Path(__file__).resolve().parents[1]
from nbbuild import SETUP

SETUP += """
import pandas as pd

from src.data.clean import (
    profile_dataset, clean_telco, validate_cleaned, save_processed, load_raw,
)

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 30)
"""

cells = [
    ("md", "# 01 — Data Cleaning\n\n"
     "Objective: inspect the raw Telco churn dataset thoroughly, fix genuine data-quality issues, and produce a "
     "cleaned dataset in `data/processed/`. The raw file under `data/raw/` is never modified.\n\n"
     "All reusable cleaning logic lives in `src/data/clean.py`; this notebook applies it, reports the evidence, and "
     "documents every decision."),
    ("code", SETUP),
    ("code", "df = load_raw()\ndf.head()"),
    ("md", "## 1. Dataset profile\n\nShape, dtypes, missing values, blank strings, whitespace, duplicates, categorical domains, numeric ranges."),
    ("code", "profile = profile_dataset(df)\nprint('shape:', profile['shape'])\nprint('\\ndtypes:')\nfor col, dtype in profile['dtypes'].items():\n    print(f'  {col:<18} {dtype}')"),
    ("code", "print('missing values (excluding TotalCharges blanks):')\nmissing = {k: v for k, v in profile['missing_by_column'].items() if v > 0}\nprint(missing if missing else '  none')\nprint('\\nduplicate rows:', profile['duplicate_rows'])\nprint('duplicate customerIDs:', profile['duplicate_customer_ids'])\nprint('\\nblank strings per column:')\nprint({k: v for k, v in profile['blank_string_counts'].items() if v > 0})\nprint('\\ncolumns with leading/trailing whitespace:')\nprint({k: v for k, v in profile['whitespace_hits'].items() if v > 0} or '  none')"),
    ("code", "print('unexpected categorical values:', profile['unexpected_category_values'] or 'none')\nprint('\\nTotalCharges non-numeric values:', profile['total_charges_non_numeric'])\nprint('  tenure of those rows:', profile['total_charges_non_numeric_tenure'])\nprint('  Churn of those rows:', profile['total_charges_non_numeric_churn'])"),
    ("md", "**Finding:** the only genuine quality issue is `TotalCharges` — stored as text, with 11 blank strings. "
     "No duplicate rows, no duplicate IDs, no missing values elsewhere, no whitespace, and every categorical column "
     "matches its expected domain."),
    ("md", "## 2. Numeric ranges & outliers"),
    ("code", "df[['tenure', 'MonthlyCharges']].describe()"),
    ("code", "import numpy as np\n\ntc = pd.to_numeric(df['TotalCharges'], errors='coerce')\nprint(tc.describe())\nprint('\\nTotalCharges vs MonthlyCharges * tenure consistency (should be close for linear billing):')\nratio = (tc / (df['MonthlyCharges'] * df['tenure'].clip(lower=1))).dropna()\nprint(ratio.describe()[['min', '25%', '50%', '75%', 'max']])"),
    ("md", "`tenure` is 0–72 months, `MonthlyCharges` 18.25–118.75 USD, `TotalCharges` 18.8–8684.8 USD — all plausible "
     "ranges. `TotalCharges` is not always `MonthlyCharges × tenure` (price changes over time), which is expected. "
     "No impossible outliers; extreme values are legitimate long-tenure customers."),
    ("md", "## 3. The `TotalCharges` decision\n\n11 blank values, all with `tenure = 0`. These are brand-new customers with no completed billing cycle. Options considered:\n\n"
     "| Option | Verdict |\n|---|---|\n| Drop the 11 rows | Loses real customers; tenure=0 new customers are a legitimate population |\n| Impute median/mean | Fabricates billing that never happened; would overstate revenue |\n| **Set to 0.0** | Factually correct: no invoice has been issued yet, so total charged to date is genuinely zero |\n\nChosen: **0.0** — this is a factual value, not a statistical imputation. It is documented everywhere `TotalCharges` is used."),
    ("md", "## 4. Apply cleaning"),
    ("code", "cleaned, log = clean_telco(df)\nfor key, value in log.items():\n    print(f'{key}: {value}')"),
    ("md", "## 5. Validate & save"),
    ("code", "checks = validate_cleaned(cleaned)\nfor name, ok in checks.items():\n    print(f'{name}: {ok}')"),
    ("code", "out = save_processed(cleaned)\nprint('saved:', out)\nprint('final shape:', cleaned.shape)\nprint('\\nfinal dtypes:')\nprint(cleaned.dtypes)\nprint('\\nfinal missing values:', int(cleaned.isna().sum().sum()))\ncleaned.head()"),
    ("md", "## Cleaning summary\n\n- **Issues found:** `TotalCharges` stored as text with 11 blank strings (all `tenure=0`, all `Churn=No`). No duplicates, no other missing values, no whitespace issues, no unexpected categories, no invalid numeric ranges.\n"
     "- **Transformations:** defensive whitespace trim on string columns; `TotalCharges` → float64 with the 11 blanks set to 0.0 (factual zero billing, not imputation); `SeniorCitizen`/`tenure` normalized to int.\n"
     "- **Final dataset:** 7,043 rows × 21 columns, zero missing values, unique `customerID`.\n"
     "- **Decision log:** blank `TotalCharges` = 0.0 because no billing has occurred yet for tenure-0 customers (alternatives: drop rows, median imputation — rejected for reasons above).\n"
     "- Raw file untouched; cleaned copy saved to `data/processed/telco_cleaned.csv`."),
]

if __name__ == "__main__":
    build_notebook(ROOT / "notebooks" / "01_data_cleaning.ipynb", cells)
    print("built notebooks/01_data_cleaning.ipynb")
