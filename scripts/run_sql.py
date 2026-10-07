"""Execute the SQL scripts in sql/ against the processed dataset in SQLite.

Loads data/processed/telco_cleaned.csv into an in-memory SQLite database as
table ``telco_cleaned``, runs every statement in every sql/*.sql file, and
writes a single readable report to reports/sql_results.md.

Dialect assumption: SQLite 3.x (standard SQL used throughout; window functions
require SQLite >= 3.25).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "telco_cleaned.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "sql_results.md"


def to_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_no rows_"
    return df.to_markdown(index=False)


def split_statements(text: str) -> list[str]:
    """Split SQL text into statements.

    A statement ends at a line whose non-comment part ends with ';'. This keeps
    semicolons inside comments from producing bogus fragments.
    """
    statements, buf = [], []
    for line in text.splitlines():
        buf.append(line)
        code_part = line.split("--", 1)[0]
        if code_part.rstrip().endswith(";"):
            statements.append("\n".join(buf))
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_statement(cur: sqlite3.Cursor, sql: str) -> pd.DataFrame:
    cur.execute(sql)
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=[d[0] for d in cur.description])


def main() -> None:
    df = pd.read_csv(PROCESSED_CSV)
    con = sqlite3.connect(":memory:")
    df.to_sql("telco_cleaned", con, index=False, if_exists="replace")

    lines = [
        "# SQL Analysis Results",
        "",
        f"Executed against `data/processed/telco_cleaned.csv` ({len(df):,} rows) in SQLite. "
        "Dialect: SQLite 3.x; results identical on any ANSI-compatible engine for the constructs used.",
        "",
    ]

    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        lines += [f"## {sql_file.name}", ""]
        statements = split_statements(sql_file.read_text())
        n = 0
        for statement in statements:
            # Strip full-line comments so the report shows executable SQL only.
            code = "\n".join(
                line for line in statement.splitlines() if not line.strip().startswith("--")
            ).strip()
            if not code:
                continue
            n += 1
            result = run_statement(con.cursor(), code)
            lines += [f"### {sql_file.stem} — statement {n}", "", "```sql", code, "```", ""]
            lines += [to_markdown_table(result), ""]
        print(f"{sql_file.name}: {n} statements executed")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("report written:", REPORT_PATH)


if __name__ == "__main__":
    main()
