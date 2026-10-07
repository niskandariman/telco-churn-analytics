"""Tiny helper to build Jupyter notebooks from Python cell sources."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

# Standard setup cell for all notebooks: works whether the notebook is executed
# from the project root or from notebooks/.
SETUP = """\
import sys
from pathlib import Path

_candidates = [Path.cwd(), *Path.cwd().parents]
PROJECT_ROOT = next(p for p in _candidates if (p / "src").exists())
sys.path.insert(0, str(PROJECT_ROOT))
import warnings
warnings.filterwarnings("ignore")
"""


def build_notebook(path: Path | str, cells: list[tuple[str, str]], kernel: str = "python3") -> None:
    """Write a .ipynb from a list of (cell_type, source) tuples."""
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": kernel}
    for kind, src in cells:
        if kind == "md":
            nb.cells.append(nbf.v4.new_markdown_cell(src))
        else:
            nb.cells.append(nbf.v4.new_code_cell(src))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, str(path))
