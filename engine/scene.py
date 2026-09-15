"""Scene configuration loader.

A scene is a JSON file that declaratively describes an SOP: its entities
(fields + options + state enums), acts/stages, checklists, templates, and
timeline. The engine reads this config to drive CRUD, forms, and lists, so
adding a new scene never requires touching engine code.

Field types (design convention B, frozen minimal set):
  text, textarea, number, date, select, multiselect, checkbox, file
"""

from __future__ import annotations

import json
from pathlib import Path

from .dataroot import app_root

SCENES_DIR = app_root() / "scenes"
DEFAULT_SCENE = "tuimian"

FIELD_TYPES = {"text", "textarea", "number", "date", "select", "multiselect", "checkbox", "file"}

_FIELD_SQL = {
    "text": "text not null default ''",
    "textarea": "text not null default ''",
    "date": "text not null default ''",
    "select": "text not null default ''",
    "multiselect": "text not null default ''",
    "file": "text not null default ''",
    "number": "real not null default 0",
    "checkbox": "integer not null default 0",
}

_cache: dict[str, dict] = {}


def scenes_dir() -> Path:
    return SCENES_DIR


def scene_path(scene_id: str) -> Path:
    return SCENES_DIR / scene_id / "scene.json"


def load_scene(scene_id: str) -> dict:
    if scene_id in _cache:
        return _cache[scene_id]
    path = scene_path(scene_id)
    if not path.exists():
        raise FileNotFoundError(f"场景包不存在：{scene_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    _cache[scene_id] = data
    return data


def active_scene_id() -> str:
    import os

    return os.environ.get("GRADPATH_SCENE", DEFAULT_SCENE)


def active_scene() -> dict:
    return load_scene(active_scene_id())


def entities(scene: dict | None = None) -> dict[str, dict]:
    data = scene or active_scene()
    return data.get("entities", {})


def entity(entity_key: str, scene: dict | None = None) -> dict | None:
    return entities(scene).get(entity_key)


def entity_keys(scene: dict | None = None) -> list[str]:
    return list(entities(scene).keys())


def entity_label(entity_key: str) -> str:
    cfg = entity(entity_key)
    return (cfg or {}).get("label", entity_key)


def entity_fields(entity_key: str) -> list[dict]:
    cfg = entity(entity_key) or {}
    return list(cfg.get("fields", []))


def field_keys(entity_key: str) -> list[str]:
    return [f["key"] for f in entity_fields(entity_key)]


def writable_columns(entity_key: str) -> list[str]:
    cfg = entity(entity_key) or {}
    extra = list(cfg.get("extraWritable", []))
    return list(dict.fromkeys(field_keys(entity_key) + extra))


def search_columns(entity_key: str) -> list[str]:
    cfg = entity(entity_key) or {}
    return list(cfg.get("search") or field_keys(entity_key))


def entity_order(entity_key: str) -> str:
    cfg = entity(entity_key) or {}
    return cfg.get("order") or "id desc"


def entity_columns(entity_key: str) -> list[list[str]]:
    cfg = entity(entity_key) or {}
    columns = cfg.get("columns")
    if columns:
        return [[c[0], c[1]] for c in columns]
    return [[f["key"], f.get("label", f["key"])] for f in entity_fields(entity_key)]


def entity_filter_field(entity_key: str) -> str | None:
    cfg = entity(entity_key) or {}
    return cfg.get("filterField")


def scene_settings(scene: dict | None = None) -> dict:
    """Default settings declared by the scene (branding, theme, etc.)."""
    data = scene or active_scene()
    return data.get("settings", {})


def scene_seeds(scene: dict | None = None) -> dict[str, list[dict]]:
    """Seed rows declared by the scene, keyed by entity."""
    data = scene or active_scene()
    return data.get("seeds", {})


def scene_acts(scene: dict | None = None) -> list[dict]:
    """The act -> stage -> checklist tree for the SOP engine."""
    data = scene or active_scene()
    return data.get("acts", [])


def scene_templates(scene: dict | None = None) -> list[dict]:
    data = scene or active_scene()
    return data.get("templates", [])


def entity_system_columns(entity_key: str) -> dict[str, str]:
    """Engine-managed columns (written by indexing, not by the user form).

    Declared as ``"systemColumns": {"path": "text not null unique", ...}``.
    """
    cfg = entity(entity_key) or {}
    return dict(cfg.get("systemColumns", {}))


def validate_scene(scene: dict) -> list[str]:
    """Return a list of validation errors (empty means valid)."""
    errors: list[str] = []
    for key, cfg in entities(scene).items():
        for field in cfg.get("fields", []):
            ftype = field.get("type", "text")
            if ftype not in FIELD_TYPES:
                errors.append(f"实体 {key} 字段 {field.get('key')} 类型非法：{ftype}")
            if not field.get("key"):
                errors.append(f"实体 {key} 存在缺少 key 的字段")
            if ftype in {"select", "multiselect"} and not field.get("options") and not field.get("optionSource"):
                errors.append(f"实体 {key} 字段 {field.get('key')} 的 select 缺少 options 或 optionSource")
    return errors


def _column_sql(name: str, field: dict | None) -> str:
    if field is None:
        return "integer not null default 0" if name == "display_order" else "text not null default ''"
    ftype = field.get("type", "text")
    return _FIELD_SQL.get(ftype, "text not null default ''")


def ensure_entity_table(conn, entity_key: str) -> None:
    """Create (or migrate) a table for an entity from its field config.

    Idempotent: if the table already exists, any column declared in the scene
    but missing from the table is added via ``alter table``. This is what makes
    "edit JSON -> schema follows" work without losing existing rows.
    """
    existing = {row["name"] for row in conn.execute("pragma table_info(%s)" % entity_key)}
    cfg = entity(entity_key) or {}
    field_defs = {f["key"]: f for f in cfg.get("fields", [])}
    system_cols = entity_system_columns(entity_key)

    if "id" not in existing:
        parts = ["id integer primary key autoincrement"]
        for field in cfg.get("fields", []):
            parts.append(f"{field['key']} {_column_sql(field['key'], field)}")
        for col in cfg.get("extraWritable", []):
            if col not in field_defs:
                parts.append(f"{col} {_column_sql(col, None)}")
        for col, ddl in system_cols.items():
            parts.append(f"{col} {ddl}")
        parts += ["created_at text not null", "updated_at text not null"]
        conn.execute(f"create table if not exists {entity_key} ({', '.join(parts)})")
        return

    for field in cfg.get("fields", []):
        key = field["key"]
        if key not in existing:
            conn.execute(f"alter table {entity_key} add column {key} {_column_sql(key, field)}")
    for col in cfg.get("extraWritable", []):
        if col not in existing:
            conn.execute(f"alter table {entity_key} add column {col} {_column_sql(col, None)}")
    for col, ddl in system_cols.items():
        if col not in existing:
            conn.execute(f"alter table {entity_key} add column {col} {ddl}")


def ensure_scene_entities() -> None:
    from .db import connect

    with connect() as conn:
        for key in entity_keys():
            ensure_entity_table(conn, key)
