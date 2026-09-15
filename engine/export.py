"""Data export: CSV / Markdown for individual entities, plus a combined report.

Driven entirely by the scene config (``columns`` + ``order``), so adding a new
scene or entity requires no code changes here.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from .db import connect
from .scene import entity_columns, entity_keys, entity_order
from .utils import rows_to_dicts


def _rows(entity_key: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            f"select * from {entity_key} order by {entity_order(entity_key)}"
        ).fetchall()
    return rows_to_dicts(rows)


def _columns(entity_key: str) -> list[list[str]]:
    return entity_columns(entity_key)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def export_csv(entity_key: str) -> tuple[str, str, str]:
    """Return ``(filename, body, content_type)`` for a CSV export."""
    columns = _columns(entity_key)
    keys = [c[0] for c in columns]
    labels = [c[1] for c in columns]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(labels)
    for row in _rows(entity_key):
        writer.writerow([row.get(key, "") for key in keys])
    filename = f"{entity_key}-{_timestamp()}.csv"
    # UTF-8 BOM so Excel opens Chinese headers correctly.
    return filename, "\ufeff" + buf.getvalue(), "text/csv; charset=utf-8"


def _markdown_table(entity_key: str, rows: list[dict]) -> list[str]:
    columns = _columns(entity_key)
    keys = [c[0] for c in columns]
    labels = [c[1] for c in columns]
    lines = ["| " + " | ".join(labels) + " |", "| " + " | ".join(["---"] * len(labels)) + " |"]
    for row in rows:
        cells = [str(row.get(key, "")).replace("|", "\\|").replace("\n", "<br>") for key in keys]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def export_markdown(entity_key: str) -> tuple[str, str, str]:
    rows = _rows(entity_key)
    lines = [f"# {entity_key}", ""] + _markdown_table(entity_key, rows)
    filename = f"{entity_key}-{_timestamp()}.md"
    return filename, "\n".join(lines) + "\n", "text/markdown; charset=utf-8"


def export_report() -> tuple[str, str, str]:
    """A combined Markdown report across every entity in the active scene."""
    parts = [
        "# GradPath 数据报表",
        "",
        f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for key in entity_keys():
        rows = _rows(key)
        parts.append(f"## {key}（{len(rows)} 条）")
        parts.append("")
        if rows:
            parts.extend(_markdown_table(key, rows))
        else:
            parts.append("（无数据）")
        parts.append("")
    filename = f"gradpath-report-{_timestamp()}.md"
    return filename, "\n".join(parts) + "\n", "text/markdown; charset=utf-8"
