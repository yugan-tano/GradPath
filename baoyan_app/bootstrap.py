from __future__ import annotations

from .db import init_db, seed_questions, seed_tasks
from .repositories import ensure_program_display_order, normalize_program_results
from .scene import ensure_scene_entities


def bootstrap() -> None:
    init_db()
    ensure_scene_entities()
    normalize_program_results()
    ensure_program_display_order()
    seed_tasks()
    seed_questions()
