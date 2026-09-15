"""Generic checklist engine.

A checklist is a list of checkable items mounted onto an owner:

  * ``owner_type = "global"``        -> workspace-wide checklist (owner_id = checklist id)
  * ``owner_type = "stage"``         -> per-stage checklist (owner_id = stage id)
  * ``owner_type = <entity key>``    -> per-entity-instance (owner_id = row id)

Item templates live in ``scenes/<id>/scene.json`` under ``checklists``; the
engine materialises them into ``checklist_items`` rows on first access so each
owner keeps its own done-state and progress.
"""

from __future__ import annotations

from .db import connect
from .scene import active_scene
from .utils import now_text, rows_to_dicts


def _checklist_config(checklist_id: str) -> dict | None:
    return active_scene().get("checklists", {}).get(checklist_id)


def ensure_checklist(owner_type: str, owner_id: str, checklist_id: str) -> None:
    cfg = _checklist_config(checklist_id)
    if not cfg:
        raise ValueError(f"清单不存在：{checklist_id}")
    with connect() as conn:
        existing = conn.execute(
            "select count(*) as n from checklist_items where owner_type = ? and owner_id = ? and checklist_id = ?",
            (owner_type, owner_id, checklist_id),
        ).fetchone()["n"]
        if existing:
            return
        for index, title in enumerate(cfg.get("items", [])):
            conn.execute(
                """
                insert into checklist_items
                (owner_type, owner_id, checklist_id, title, done, sort_order, created_at, updated_at)
                values (?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (owner_type, owner_id, checklist_id, title, index, now_text(), now_text()),
            )


def ensure_owner_checklists(owner_type: str, owner_id: str) -> None:
    for checklist_id, cfg in active_scene().get("checklists", {}).items():
        if cfg.get("owner") == owner_type:
            # A global checklist is identified by its own id; per-entity/per-stage
            # checklists are identified by their owner id.
            oid = checklist_id if owner_type == "global" else owner_id
            ensure_checklist(owner_type, oid, checklist_id)


def list_checklist(owner_type: str, owner_id: str) -> dict:
    ensure_owner_checklists(owner_type, owner_id)
    with connect() as conn:
        rows = conn.execute(
            "select * from checklist_items where owner_type = ? and owner_id = ? order by sort_order asc, id asc",
            (owner_type, owner_id),
        ).fetchall()
    items = rows_to_dicts(rows)
    total = len(items)
    done = sum(1 for item in items if item["done"])
    return {
        "items": items,
        "total": total,
        "done": done,
        "progress": (done / total) if total else 1.0,
    }


def global_progress(checklist_id: str) -> float:
    """Progress of a workspace-wide checklist (used by SOP exit conditions)."""
    cfg = _checklist_config(checklist_id)
    if not cfg:
        return 0.0
    ensure_checklist("global", checklist_id, checklist_id)
    return list_checklist("global", checklist_id)["progress"]


def set_done(item_id: int, done: bool) -> dict:
    with connect() as conn:
        conn.execute(
            "update checklist_items set done = ?, updated_at = ? where id = ?",
            (1 if done else 0, now_text(), item_id),
        )
        row = conn.execute("select * from checklist_items where id = ?", (item_id,)).fetchone()
    if row is None:
        raise KeyError("检查项不存在")
    return dict(row)


def add_item(owner_type: str, owner_id: str, title: str, checklist_id: str = "custom") -> dict:
    title = (title or "").strip()
    if not title:
        raise ValueError("检查项内容不能为空")
    with connect() as conn:
        max_order = conn.execute(
            "select coalesce(max(sort_order), -1) as n from checklist_items where owner_type = ? and owner_id = ?",
            (owner_type, owner_id),
        ).fetchone()["n"]
        cur = conn.execute(
            """
            insert into checklist_items
            (owner_type, owner_id, checklist_id, title, done, sort_order, created_at, updated_at)
            values (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (owner_type, owner_id, checklist_id, title, int(max_order or 0) + 1, now_text(), now_text()),
        )
        row = conn.execute("select * from checklist_items where id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def delete_item(item_id: int) -> dict:
    with connect() as conn:
        row = conn.execute("select * from checklist_items where id = ?", (item_id,)).fetchone()
        if row is None:
            raise KeyError("检查项不存在")
        conn.execute("delete from checklist_items where id = ?", (item_id,))
    return dict(row)
