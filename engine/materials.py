"""Generic file-index engine.

Scans a scene's material directory, indexes files into the scene's ``materials``
entity, and supports upload/browse/delete. Classification rules (which category,
stage, related professor a file belongs to) are scene-specific and provided by
``scenes/<id>/hooks.py`` via the ``classify_file`` hook.
"""

from __future__ import annotations

import io
import os
import shutil
import sqlite3
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path

from .config import MAX_UPLOAD_BYTES
from .dataroot import source_dir
from .db import connect
from .hooks import call
from .utils import is_safe_data_path, now_text, relative_text, rows_to_dicts


IGNORED_DIRECTORY_NAMES = {
    ".agents", ".cache", ".codex", ".git", ".next", ".nuxt", ".pnpm-store",
    ".pytest_cache", ".turbo", ".venv", ".wrangler", "__pycache__", "node_modules", "venv",
}
IGNORED_FILE_SUFFIXES = {".tmp", ".crdownload", ".part"}


def is_ignored_material_path(path: Path) -> bool:
    try:
        relative_parts = path.relative_to(source_dir()).parts
    except ValueError:
        return True
    return any(part.lower() in IGNORED_DIRECTORY_NAMES for part in relative_parts)


def purge_ignored_material_rows(conn: sqlite3.Connection) -> int:
    rows = conn.execute("select id, path from materials").fetchall()
    ignored_ids = [(row["id"],) for row in rows if is_ignored_material_path(Path(row["path"]))]
    if ignored_ids:
        conn.executemany("delete from materials where id = ?", ignored_ids)
    return len(ignored_ids)


def sanitize_material_paths(conn: sqlite3.Connection) -> None:
    """Hide stale rows copied from another machine or an older project path."""
    rows = conn.execute("select id, path from materials where missing = 0").fetchall()
    for row in rows:
        path = Path(row["path"])
        if not is_safe_data_path(path) or not path.exists():
            conn.execute("update materials set missing = 1, updated_at = ? where id = ?", (now_text(), row["id"]))


def classify_material(path: Path) -> dict:
    """Classify via the scene hook; fall back to a minimal default."""
    result = call("classify_file", path)
    if result:
        return result
    return {
        "category": "参考",
        "stage": "通用",
        "kind": "参考资料",
        "folder": str(path.parent.relative_to(source_dir().parent)) if source_dir().parent in path.parents else "",
        "relative_path": relative_text(path),
        "related_professor": "",
        "related_program": "",
    }


def scan_materials() -> dict:
    with connect() as conn:
        purged = purge_ignored_material_rows(conn)
        sanitize_material_paths(conn)

    if not source_dir().exists():
        with connect() as conn:
            missing = conn.execute("select count(*) as n from materials where missing = 1").fetchone()["n"]
        return {"inserted": 0, "updated": 0, "missing": missing, "purged": purged}

    inserted = 0
    updated = 0
    with connect() as conn:
        conn.execute("update materials set missing = 1 where path like ?", (str(source_dir()) + "%",))
        for root, directory_names, file_names in os.walk(source_dir()):
            directory_names[:] = [name for name in directory_names if name.lower() not in IGNORED_DIRECTORY_NAMES]
            for file_name in file_names:
                path = Path(root) / file_name
                if path.suffix.lower() in IGNORED_FILE_SUFFIXES or path.name.startswith("~$"):
                    continue
                stat = path.stat()
                info = classify_material(path)
                row = conn.execute("select * from materials where path = ?", (str(path),)).fetchone()
                if row:
                    conn.execute(
                        """
                        update materials
                        set name = ?, category = ?, stage = ?, ext = ?, size = ?, mtime = ?,
                            relative_path = ?, folder = ?, resource_kind = ?,
                            related_professor = ?, related_program = ?, missing = 0, updated_at = ?
                        where path = ?
                        """,
                        (
                            path.name, info.get("category", "参考"), info.get("stage", "通用"),
                            path.suffix.lower(), stat.st_size,
                            datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                            info.get("relative_path", relative_text(path)), info.get("folder", ""),
                            info.get("kind", "参考资料"), info.get("related_professor", ""),
                            info.get("related_program", ""), now_text(), str(path),
                        ),
                    )
                    updated += 1
                else:
                    conn.execute(
                        """
                        insert into materials
                        (name, category, stage, path, ext, size, mtime, note, pinned,
                         relative_path, folder, resource_kind, related_professor, related_program, missing,
                         created_at, updated_at)
                        values (?, ?, ?, ?, ?, ?, ?, '', 0, ?, ?, ?, ?, ?, 0, ?, ?)
                        """,
                        (
                            path.name, info.get("category", "参考"), info.get("stage", "通用"),
                            str(path), path.suffix.lower(), stat.st_size,
                            datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                            info.get("relative_path", relative_text(path)), info.get("folder", ""),
                            info.get("kind", "参考资料"), info.get("related_professor", ""),
                            info.get("related_program", ""), now_text(), now_text(),
                        ),
                    )
                    inserted += 1
        call("after_scan", conn)
        missing = conn.execute("select count(*) as n from materials where missing = 1").fetchone()["n"]
    return {"inserted": inserted, "updated": updated, "missing": missing, "purged": purged}


def get_material(row_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute("select * from materials where id = ?", (row_id,)).fetchone()


def material_actions(row: dict) -> dict:
    hook_actions = call("material_actions", row)
    if hook_actions:
        return hook_actions
    ext = (row.get("ext") or "").lower()
    can_preview = ext in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".md", ".csv"}
    return {"canPreview": can_preview, "openUrl": f"/api/materials/{row['id']}/open", "viewUrl": f"/files/{row['id']}/view"}


def resource_groups() -> dict:
    hook_result = call("resource_groups")
    if hook_result:
        return hook_result
    with connect() as conn:
        rows = rows_to_dicts(
            conn.execute("select * from materials where missing = 0 order by category asc, folder asc, name asc").fetchall()
        )
    groups: dict[str, dict] = {}
    for row in rows:
        row["actions"] = material_actions(row)
        groups.setdefault(row["category"], {"name": row["category"], "count": 0, "items": []})
        groups[row["category"]]["count"] += 1
        groups[row["category"]]["items"].append(row)
    return {"byCategory": list(groups.values()), "byFolder": []}


def resource_directory(relative_path: str = "", query: str = "", limit: int = 200) -> dict:
    limit = max(1, min(int(limit or 200), 300))
    query = str(query or "").strip()
    if query:
        search_columns = ["name", "relative_path", "category", "resource_kind", "related_professor", "related_program", "note"]
        where = " or ".join(f"{column} like ?" for column in search_columns)
        params = [f"%{query}%"] * len(search_columns)
        with connect() as conn:
            rows = rows_to_dicts(
                conn.execute(
                    f"select * from materials where missing = 0 and ({where}) order by pinned desc, mtime desc, id desc limit ?",
                    [*params, limit],
                ).fetchall()
            )
        items = []
        for row in rows:
            if is_ignored_material_path(Path(row["path"])):
                continue
            row["actions"] = material_actions(row)
            items.append(row)
        return {"mode": "search", "query": query, "items": items, "limit": limit, "truncated": len(rows) >= limit}

    relative = Path(str(relative_path or "").replace("/", os.sep))
    current = (source_dir() / relative).resolve()
    if not is_safe_data_path(current) or (current != source_dir() and source_dir() not in current.parents):
        raise ValueError("资源目录路径不正确")
    if not current.exists() or not current.is_dir():
        raise FileNotFoundError("资源目录不存在")

    directories = []
    for child in sorted((item for item in current.iterdir() if item.is_dir()), key=lambda item: item.name.casefold()):
        if is_ignored_material_path(child):
            continue
        visible_children = 0
        try:
            for entry in os.scandir(child):
                entry_path = Path(entry.path)
                if is_ignored_material_path(entry_path) or entry.name.startswith("~$"):
                    continue
                visible_children += 1
        except OSError:
            pass
        directories.append(
            {
                "name": child.name,
                "relativePath": child.relative_to(source_dir()).as_posix(),
                "path": str(child),
                "childCount": visible_children,
            }
        )

    folder_key = str(current.relative_to(source_dir().parent))
    with connect() as conn:
        rows = rows_to_dicts(
            conn.execute(
                "select * from materials where missing = 0 and folder = ? order by pinned desc, name asc",
                (folder_key,),
            ).fetchall()
        )
    files = []
    for row in rows:
        if is_ignored_material_path(Path(row["path"])):
            continue
        row["actions"] = material_actions(row)
        files.append(row)

    parts = list(relative.parts) if str(relative) not in {"", "."} else []
    breadcrumbs = [{"name": source_dir().name, "relativePath": ""}]
    breadcrumbs.extend(
        {"name": part, "relativePath": Path(*parts[: index + 1]).as_posix()}
        for index, part in enumerate(parts)
    )
    return {
        "mode": "directory",
        "relativePath": "" if current == source_dir() else current.relative_to(source_dir()).as_posix(),
        "path": str(current),
        "breadcrumbs": breadcrumbs,
        "directories": directories,
        "files": files,
    }


def delete_material_file(row_id: int) -> dict:
    row = get_material(row_id)
    if row is None:
        raise FileNotFoundError("材料不存在")
    path = Path(row["path"])
    if not is_safe_data_path(path) or not path.exists() or not path.is_file():
        raise FileNotFoundError("文件不存在或不在项目目录内")
    path.unlink()
    with connect() as conn:
        conn.execute("update materials set missing = 1, updated_at = ? where id = ?", (now_text(), row_id))
    return {"ok": True, "deleted": str(path)}


class UploadedField:
    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self.file = io.BytesIO(data)


def parse_upload(handler, field_name: str) -> UploadedField:
    content_type = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type:
        raise ValueError("请使用文件上传表单")
    size = int(handler.headers.get("Content-Length", "0") or "0")
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("上传文件过大")
    body = handler.rfile.read(size)
    msg = BytesParser(policy=policy.default).parsebytes(
        b"Content-Type: " + content_type.encode("utf-8") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    )
    parts = msg.iter_parts() if msg.is_multipart() else [msg]
    for part in parts:
        name = part.get_param("name", header="content-disposition")
        if name != field_name:
            continue
        filename = part.get_filename() or ""
        data = part.get_payload(decode=True) or b""
        return UploadedField(filename, data)
    raise ValueError("没有选择文件")


def upload_material(handler) -> dict:
    field = parse_upload(handler, "file")
    upload_dir = source_dir() / "网页添加"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(field.filename).name
    target = upload_dir / safe_name
    if target.exists():
        target = upload_dir / f"{target.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{target.suffix}"
    with target.open("wb") as f:
        shutil.copyfileobj(field.file, f)
    return {"path": str(target), **scan_materials()}
