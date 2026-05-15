# -*- coding: utf-8 -*-
"""Import path bootstrap for the organized submission project.

The original project is organized by problem for readability, while several
modules are shared by all solvers. This helper adds the common and per-problem
code directories to ``sys.path`` in a deterministic order so that scripts can
be executed from the project root or from a subdirectory.
"""

from __future__ import annotations

import sys
from pathlib import Path


CODE_DIRS = [
    "00_common_core/code",
    "00_common_core/run",
    "01_Q1_single_vehicle/code",
    "02_Q2_multi_vehicle_lifo/code",
    "03_Q3_block_flexible/code",
    "04_Q4_validation_audit/code",
]


def find_project_root(start_file: str | Path | None = None) -> Path:
    """Locate the root directory of the organized submission project.

    The check is based on the two stable top-level folders that are required by
    the submitted project layout. A fallback to this file's parent is retained
    so the function remains robust during packaging.
    """
    start = Path(start_file).resolve() if start_file else Path.cwd().resolve()
    candidates = [start] if start.is_dir() else [start.parent]
    candidates.extend(candidates[0].parents)
    for parent in candidates:
        if (parent / "00_common_core").is_dir() and (parent / "01_Q1_single_vehicle").is_dir():
            return parent
    return Path(__file__).resolve().parent


def configure_paths(start_file: str | Path | None = None) -> Path:
    """Add all solver code directories to ``sys.path`` and return the root."""
    root = find_project_root(start_file)
    paths = [root, *[root / rel for rel in CODE_DIRS]]
    for path in reversed(paths):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)
    return root
