"""Cross-entity link store.

Links let any record reference any other record (optionally across scenes):
e.g. a project links to papers/materials/tasks, a policy links to a school, or
a study course links to a research project. They live in one shared SQLite DB
per data root (``data/links.db``) so references can span scene packages, and
they power the aggregation ("项目聚合") page without schema changes.
"""

from __future__ import annotations

from collections import defaultdict

from .db import connect_links, connect_scene
from .scene import active_scene_id, entities, entity_title_field, list_scenes, load_scene
from .utils import now_text


def init_links() -> None:
    with connect_links() as conn:
        conn.execute(
            """
            create table if not exists links (
                id integer primary key autoincrement,
                source_scene text not null,
                source_entity text not null,
                source_id integer not null,
                target_scene text not null,
                target_entity text not null,
                target_id integer not null,
                label text not null default '',
                created_at text not null
            )
            """
        )
        conn.execute("create index if not exists idx_links_source on links(source_scene, source_entity, source_id)")
        conn.execute("create index if not exists idx_links_target on links(target_scene, target_entity, target_id)")


def _record_title(scene_id: str, entity_key: str, row_id: int, scene_conns: dict) -> str:
    try:
        cfg = load_scene(scene_id)
        title_field = entity_title_field(entity_key, cfg)
    except (FileNotFoundError, ValueError):
        return f"#{row_id}"
    conn = scene_conns.get(scene_id)
    if conn is None:
        conn = connect_scene(scene_id)
        scene_conns[scene_id] = conn
    try:
        row = conn.execute(f"select * from {entity_key} where id = ?", (int(row_id),)).fetchone()
    except Exception:
        return f"#{row_id}"
    if row is None:
        return f"#{row_id}（已删除）"
    value = dict(row).get(title_field, "")
    return str(value) if value not in (None, "") else f"#{row_id}"


def _close(scene_conns: dict) -> None:
    for conn in scene_conns.values():
        try:
            conn.close()
        except Exception:
            pass


def _resolve(rows, side: str) -> list[dict]:
    scene_conns: dict = {}
    result = []
    for raw in rows:
        row = dict(raw)
        if side == "target":
            r_scene, r_entity, r_id = row["target_scene"], row["target_entity"], row["target_id"]
        else:
            r_scene, r_entity, r_id = row["source_scene"], row["source_entity"], row["source_id"]
        result.append(
            {
                "id": row["id"],
                "scene": r_scene,
                "entity": r_entity,
                "rowId": r_id,
                "name": _record_title(r_scene, r_entity, r_id, scene_conns),
                "label": row["label"],
                "sourceScene": row["source_scene"],
                "sourceEntity": row["source_entity"],
                "sourceId": row["source_id"],
                "targetScene": row["target_scene"],
                "targetEntity": row["target_entity"],
                "targetId": row["target_id"],
            }
        )
    _close(scene_conns)
    return result


def set_links(scene: str, entity: str, row_id: int, links: list[dict]) -> dict:
    links = links or []
    now = now_text()
    with connect_links() as conn:
        conn.execute(
            "delete from links where source_scene = ? and source_entity = ? and source_id = ?",
            (scene, entity, int(row_id)),
        )
        saved = 0
        for link in links:
            target_scene = str(link.get("scene") or scene).strip() or scene
            target_entity = str(link.get("entity") or "").strip()
            target_id = link.get("id")
            label = str(link.get("label") or "").strip()
            if not target_entity or target_id is None:
                continue
            conn.execute(
                "insert into links (source_scene, source_entity, source_id, target_scene, target_entity, target_id, label, created_at) values (?,?,?,?,?,?,?,?)",
                (scene, entity, int(row_id), target_scene, target_entity, int(target_id), label, now),
            )
            saved += 1
    return {"ok": True, "count": saved}


def get_outgoing(scene: str, entity: str, row_id: int) -> list[dict]:
    with connect_links() as conn:
        rows = conn.execute(
            "select * from links where source_scene = ? and source_entity = ? and source_id = ? order by id asc",
            (scene, entity, int(row_id)),
        ).fetchall()
    return _resolve(rows, side="target")


def get_incoming(scene: str, entity: str, row_id: int) -> list[dict]:
    with connect_links() as conn:
        rows = conn.execute(
            "select * from links where target_scene = ? and target_entity = ? and target_id = ? order by id asc",
            (scene, entity, int(row_id)),
        ).fetchall()
    return _resolve(rows, side="source")


def remove_record_links(scene: str, entity: str, row_id: int) -> dict:
    with connect_links() as conn:
        conn.execute(
            "delete from links where (source_scene = ? and source_entity = ? and source_id = ?) or (target_scene = ? and target_entity = ? and target_id = ?)",
            (scene, entity, int(row_id), scene, entity, int(row_id)),
        )
    return {"ok": True}


def linkable_entities() -> list[dict]:
    """All entities across all scenes that can be linked to (target picker)."""
    result = []
    for info in list_scenes():
        sid = info["id"]
        try:
            cfg = load_scene(sid)
        except (OSError, ValueError):
            continue
        for key, ecfg in entities(cfg).items():
            result.append(
                {
                    "scene": sid,
                    "sceneName": cfg.get("name", sid),
                    "sceneNameEn": cfg.get("nameEn", ""),
                    "entity": key,
                    "label": ecfg.get("label", key),
                }
            )
    return result


def link_options(scene_id: str, entity_key: str) -> dict:
    """Records of a linkable entity, as {id, name} for a dropdown."""
    try:
        cfg = load_scene(scene_id)
        title_field = entity_title_field(entity_key, cfg)
    except (FileNotFoundError, ValueError):
        return {"items": []}
    order = (entities(cfg).get(entity_key) or {}).get("order") or "id desc"
    with connect_scene(scene_id) as conn:
        try:
            rows = conn.execute(f"select id, {title_field} as name from {entity_key} order by {order}").fetchall()
        except Exception:
            return {"items": []}
    items = []
    for raw in rows:
        row = dict(raw)
        name = str(row.get("name") or "").strip() or f"#{row['id']}"
        items.append({"id": row["id"], "name": name})
    return {"items": items}


def link_board(entity_key: str) -> dict:
    """Aggregation board: every record of ``entity_key`` (active scene) plus the
    items linked to it, grouped by their source entity. Powers the 项目聚合页."""
    scene_id = active_scene_id()
    cfg = load_scene(scene_id)
    title_field = entity_title_field(entity_key, cfg)
    order = (entities(cfg).get(entity_key) or {}).get("order") or "id desc"
    with connect_scene(scene_id) as conn:
        try:
            rows = conn.execute(f"select * from {entity_key} order by {order}").fetchall()
        except Exception:
            return {"items": []}
    records = [dict(r) for r in rows]

    with connect_links() as conn:
        link_rows = conn.execute(
            "select * from links where target_scene = ? and target_entity = ? order by id asc",
            (scene_id, entity_key),
        ).fetchall()
    by_target: dict[int, list[dict]] = defaultdict(list)
    for raw in link_rows:
        lr = dict(raw)
        by_target[lr["target_id"]].append(lr)

    scene_conns: dict = {}
    board = []
    for rec in records:
        rid = rec["id"]
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for link in by_target.get(rid, []):
            groups[(link["source_scene"], link["source_entity"])].append(
                {
                    "rowId": link["source_id"],
                    "name": _record_title(link["source_scene"], link["source_entity"], link["source_id"], scene_conns),
                    "label": link["label"],
                }
            )
        group_list = []
        for (g_scene, g_entity), items in groups.items():
            try:
                g_cfg = load_scene(g_scene)
            except (OSError, ValueError):
                g_cfg = {}
            group_list.append(
                {
                    "scene": g_scene,
                    "sceneName": g_cfg.get("name", g_scene),
                    "sceneNameEn": g_cfg.get("nameEn", ""),
                    "entity": g_entity,
                    "label": (entities(g_cfg).get(g_entity) or {}).get("label", g_entity),
                    "count": len(items),
                    "items": items,
                }
            )
        board.append(
            {
                "id": rid,
                "name": str(rec.get(title_field) or "").strip() or f"#{rid}",
                "row": rec,
                "total": len(by_target.get(rid, [])),
                "groups": group_list,
            }
        )
    _close(scene_conns)
    return {"items": board}
