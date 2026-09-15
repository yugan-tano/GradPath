from __future__ import annotations

import sqlite3

from .dataroot import data_dir, db_path


def connect() -> sqlite3.Connection:
    data_dir().mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    existing = {row["name"] for row in conn.execute(f"pragma table_info({table})")}
    if column not in existing:
        conn.execute(f"alter table {table} add column {column} {ddl}")


def init_db() -> None:
    """Create only the engine's own tables.

    Entity tables (院校/导师/文件/待办/面试题...) are NOT hardcoded here; they
    are declared in ``scenes/<id>/scene.json`` and created by ``scene.py``.
    This is the core of the engine/scene split.
    """
    with connect() as conn:
        conn.executescript(
            """
            create table if not exists settings (
                key text primary key,
                value text not null default '',
                updated_at text not null
            );

            create table if not exists checklist_items (
                id integer primary key autoincrement,
                owner_type text not null default 'global',
                owner_id text not null default '',
                checklist_id text not null,
                title text not null,
                done integer not null default 0,
                sort_order integer not null default 0,
                created_at text not null,
                updated_at text not null
            );

            create table if not exists stage_state (
                scene text not null,
                stage text not null,
                status text not null default 'pending',
                notes text not null default '',
                updated_at text not null,
                primary key (scene, stage)
            );
            """
        )
