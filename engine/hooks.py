"""Scene hook loader.

The engine stays generic. Scene-specific business logic (file classification,
contact aggregation, dashboard analytics, seed data, normalization) lives in
``scenes/<id>/hooks.py`` and is loaded here by convention. If a hook is absent,
the engine falls back to a sensible no-op.
"""

from __future__ import annotations

import importlib
from functools import lru_cache

from .scene import active_scene_id


@lru_cache(maxsize=None)
def _module(scene_id: str):
    try:
        return importlib.import_module(f"scenes.{scene_id}.hooks")
    except (ImportError, ModuleNotFoundError):
        return None


def call(name: str, *args, **kwargs):
    """Call a scene hook if it exists; return None otherwise."""
    mod = _module(active_scene_id())
    if mod is None:
        return None
    fn = getattr(mod, name, None)
    if fn is None:
        return None
    return fn(*args, **kwargs)
