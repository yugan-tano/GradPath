from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .dataroot import app_root, current_data_root


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]


def is_safe_path(path: Path) -> bool:
    """True only when ``path`` is inside the code root (used for static files)."""
    try:
        resolved = path.resolve()
    except OSError:
        return False
    root = app_root()
    return resolved == root or root in resolved.parents


def is_safe_data_path(path: Path) -> bool:
    """True when ``path`` is inside the data root (used for materials/avatar)."""
    try:
        resolved = path.resolve()
    except OSError:
        return False
    root = current_data_root()
    return resolved == root or root in resolved.parents


def relative_text(path: Path) -> str:
    try:
        return str(path.relative_to(current_data_root()))
    except ValueError:
        return str(path)


def folder_level(folder: str, depth: int = 2) -> str:
    if not folder:
        return "保研准备"
    parts = Path(folder).parts
    return str(Path(*parts[:depth])) if len(parts) >= depth else str(Path(*parts))
