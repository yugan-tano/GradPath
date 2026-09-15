from __future__ import annotations

from .db import init_db
from .hooks import call
from .scene import ensure_scene_entities, scene_seeds
from .utils import now_text


def _apply_seeds() -> None:
    """Seed rows declared in the scene's ``seeds`` block (idempotent by count)."""
    from .db import connect

    seeds = scene_seeds()
    if not seeds:
        return
    with connect() as conn:
        for entity_key, rows in seeds.items():
            if conn.execute(f"select count(*) as n from {entity_key}").fetchone()["n"]:
                continue
            for row in rows:
                keys = list(row.keys())
                values = [row[k] for k in keys]
                conn.execute(
                    f"insert into {entity_key} ({', '.join(keys + ['created_at', 'updated_at'])}) values ({', '.join(['?'] * (len(keys) + 2))})",
                    values + [now_text(), now_text()],
                )


def bootstrap() -> None:
    init_db()
    ensure_scene_entities()
    _apply_seeds()
    call("bootstrap")
