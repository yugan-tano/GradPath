from __future__ import annotations

import shutil
from datetime import datetime

from . import scene
from .dataroot import data_dir, db_path
from .db import connect
from .utils import now_text, rows_to_dicts


def _is_ordered(entity_key: str) -> bool:
    return bool((scene.entity(entity_key) or {}).get("ordered"))


def _order_where(entity_key: str) -> str:
    """Optional SQL filter applied when resequencing an ordered entity."""
    return (scene.entity(entity_key) or {}).get("orderFilter") or ""


def resequence(conn, entity_key: str, where: str = "") -> None:
    where_sql = f" where {where}" if where else ""
    rows = conn.execute(
        f"select id, display_order from {entity_key}{where_sql} order by display_order asc, id asc"
    ).fetchall()
    for index, row in enumerate(rows, start=1):
        if row["display_order"] != index:
            conn.execute(f"update {entity_key} set display_order = ? where id = ?", (index, row["id"]))


def list_table(table: str, query: dict) -> dict:
    search = scene.search_columns(table)
    q = (query.get("q") or [""])[0].strip()
    where = ""
    params: list[str] = []
    if q:
        where = " where " + " or ".join([f"{col} like ?" for col in search])
        params = [f"%{q}%"] * len(search)
    raw_limit = (query.get("limit") or [""])[0]
    limit = max(1, min(int(raw_limit), 500)) if str(raw_limit).isdigit() else None
    limit_sql = " limit ?" if limit else ""
    if limit:
        params.append(limit)
    with connect() as conn:
        if _is_ordered(table):
            resequence(conn, table, _order_where(table))
        rows = conn.execute(
            f"select * from {table}{where} order by {scene.entity_order(table)}{limit_sql}", params
        ).fetchall()
    return {"items": rows_to_dicts(rows)}


def create_row(table: str, payload: dict) -> dict:
    columns = scene.writable_columns(table)
    if _is_ordered(table) and not payload.get("display_order"):
        with connect() as conn:
            where = f" where {_order_where(table)}" if _order_where(table) else ""
            max_order = conn.execute(
                f"select coalesce(max(display_order), 0) as n from {table}{where}"
            ).fetchone()["n"]
        payload["display_order"] = int(max_order or 0) + 1
    cols = [col for col in columns if col in payload]
    if not cols:
        raise ValueError("没有可保存的字段")
    with connect() as conn:
        cur = conn.execute(
            f"insert into {table} ({', '.join(cols + ['created_at', 'updated_at'])}) values ({', '.join(['?'] * (len(cols) + 2))})",
            [payload.get(col, "") for col in cols] + [now_text(), now_text()],
        )
        row = conn.execute(f"select * from {table} where id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def update_row(table: str, row_id: int, payload: dict) -> dict:
    columns = scene.writable_columns(table)
    cols = [col for col in columns if col in payload]
    if not cols:
        raise ValueError("没有可更新的字段")
    sets = ", ".join([f"{col} = ?" for col in cols] + ["updated_at = ?"])
    with connect() as conn:
        conn.execute(f"update {table} set {sets} where id = ?", [payload.get(col, "") for col in cols] + [now_text(), row_id])
        row = conn.execute(f"select * from {table} where id = ?", (row_id,)).fetchone()
    if row is None:
        raise KeyError("记录不存在")
    return dict(row)


def delete_row(table: str, row_id: int) -> dict:
    from .scene import active_scene_id

    with connect() as conn:
        row = conn.execute(f"select * from {table} where id = ?", (row_id,)).fetchone()
        conn.execute(f"delete from {table} where id = ?", (row_id,))
    from .hooks import call
    from .links import remove_record_links

    call("after_delete", table, row_id, dict(row) if row else None)
    remove_record_links(active_scene_id(), table, row_id)
    return {"ok": True}


def move_row(table: str, row_id: int, direction: int = 0, target_position: int | None = None) -> dict:
    where = _order_where(table)
    with connect() as conn:
        resequence(conn, table, where)
        current_where = f"id = ?{f' and {where}' if where else ''}"
        current = conn.execute(f"select * from {table} where {current_where}", (row_id,)).fetchone()
        if current is None:
            raise KeyError("记录不存在")
        if target_position is not None:
            return _move_to_position(conn, table, current["id"], int(target_position), where)
        op = ">" if direction > 0 else "<"
        order = "asc" if direction > 0 else "desc"
        target_where = f"display_order {op} ?{f' and {where}' if where else ''}"
        target = conn.execute(
            f"select * from {table} where {target_where} order by display_order {order}, id {order} limit 1",
            (current["display_order"],),
        ).fetchone()
        if target is None:
            return {"ok": True, "moved": False}
        conn.execute(f"update {table} set display_order = ?, updated_at = ? where id = ?", (target["display_order"], now_text(), current["id"]))
        conn.execute(f"update {table} set display_order = ?, updated_at = ? where id = ?", (current["display_order"], now_text(), target["id"]))
    return {"ok": True, "moved": True}


def _move_to_position(conn, table: str, row_id: int, target_position: int, where: str = "") -> dict:
    where_sql = f" where {where}" if where else ""
    rows = conn.execute(f"select id from {table}{where_sql} order by display_order asc, id asc").fetchall()
    ids = [row["id"] for row in rows]
    if row_id not in ids:
        return {"ok": True, "moved": False}
    target_index = max(0, min(int(target_position) - 1, len(ids) - 1))
    ids.remove(row_id)
    ids.insert(target_index, row_id)
    for index, item_id in enumerate(ids, start=1):
        conn.execute(f"update {table} set display_order = ?, updated_at = ? where id = ?", (index, now_text(), item_id))
    return {"ok": True, "moved": True}


def entity_options(entity_key: str) -> list[str]:
    """Resolve a select field's ``optionSource``: distinct values of a referenced
    entity's option field, in that entity's configured order."""
    cfg = scene.entity(entity_key) or {}
    field = cfg.get("optionField") or "name"
    order = cfg.get("order") or "id desc"
    with connect() as conn:
        rows = conn.execute(
            f"select distinct {field} as value from {entity_key} where trim({field}) != '' order by {order}"
        ).fetchall()
    return [row["value"] for row in rows]


def app_options() -> dict:
    """Option sources for every entity referenced by a select field."""
    result: dict[str, list[str]] = {}
    for key, cfg in scene.entities().items():
        if cfg.get("optionField") or any(
            f.get("optionSource") == key for other in scene.entities().values() for f in other.get("fields", [])
        ):
            result[key] = entity_options(key)
    return result


def backup_db() -> dict:
    backup_dir = data_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"app-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    shutil.copy2(db_path(), target)
    return {"path": str(target)}
