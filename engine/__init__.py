"""GradPath engine — generic local-first SOP workbench.

Scene-specific business logic lives in ``scenes/<id>/hooks.py``; this package
holds only reusable capabilities: data root, scene loading, entity CRUD,
checklists, the SOP stage engine, file indexing, settings, and the HTTP server.
"""

__all__ = ["server"]
