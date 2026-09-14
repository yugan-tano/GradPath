from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime
from pathlib import Path


def app_root() -> Path:
    """The code root (where ``scenes/``, ``web/`` and the package live)."""
    return Path(__file__).resolve().parents[1]


def _app_data_dir() -> Path:
    """OS-specific app data dir that survives code reinstallation."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "gradpath"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "gradpath"


# The anchor file records where the user's data actually lives, so the app can
# find it after a migration. It sits in the app-data dir, not the code root.
ANCHOR_PATH = _app_data_dir() / "data_root.json"

# Directories that belong to the user's data (as opposed to code).
#   data/        SQLite (app.db), backups, avatar, state/*.json
#   保研准备/      the user's scanned materials
DATA_SUBDIRS = ["data", "保研准备"]

_cache: dict = {"root": None, "mtime": None}

_migrating = False
_migrating_lock = threading.Lock()


def _read_anchor() -> dict:
    if not ANCHOR_PATH.exists():
        return {}
    try:
        return json.loads(ANCHOR_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def current_data_root() -> Path:
    """Resolve the current data root, caching by the anchor file's mtime."""
    try:
        mtime = ANCHOR_PATH.stat().st_mtime if ANCHOR_PATH.exists() else -1.0
    except OSError:
        mtime = -1.0
    if mtime == _cache["mtime"] and _cache["root"] is not None:
        return _cache["root"]
    _cache["mtime"] = mtime
    anchor = _read_anchor()
    raw = anchor.get("data_root")
    if raw:
        candidate = Path(raw)
        if candidate.is_dir():
            _cache["root"] = candidate
            return candidate
    _cache["root"] = app_root()
    return _cache["root"]


def data_dir() -> Path:
    return current_data_root() / "data"


def source_dir() -> Path:
    return current_data_root() / "保研准备"


def state_dir() -> Path:
    return data_dir() / "state"


def db_path() -> Path:
    return data_dir() / "app.db"


def ensure_dirs() -> None:
    data_dir().mkdir(parents=True, exist_ok=True)
    state_dir().mkdir(parents=True, exist_ok=True)


def writes_paused() -> bool:
    with _migrating_lock:
        return _migrating


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(dirpath: Path) -> dict[str, str]:
    """Return {relative_path: md5} for every file under dirpath."""
    manifest: dict[str, str] = {}
    if not dirpath.exists():
        return manifest
    for path in dirpath.rglob("*"):
        if path.is_file():
            manifest[path.relative_to(dirpath).as_posix()] = _md5(path)
    return manifest


def _write_anchor(anchor: dict) -> None:
    ANCHOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = ANCHOR_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(anchor, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ANCHOR_PATH)  # atomic on the same filesystem


def root_info() -> dict:
    anchor = _read_anchor()
    return {
        "root": str(current_data_root()),
        "history": anchor.get("history") or [],
    }


def migrate(new_root: str) -> dict:
    """Move the data root using the KeePin-style six-step protocol.

    1. pause writes (``writes_paused`` flag, checked by the HTTP handler)
    2. snapshot the current data dirs (path -> md5)
    3. create and validate the new location (probe write)
    4. copy data dirs and verify the manifest matches
    5. atomically switch the anchor file
    6. leave the old directory in place as a rollback copy
    """
    target = Path(str(new_root or "").strip()).expanduser().resolve()
    if not str(target):
        raise ValueError("数据目录不能为空")
    current = current_data_root()
    if target == current:
        return root_info()

    global _migrating
    with _migrating_lock:
        _migrating = True
    try:
        # 2. snapshot current data before touching anything
        manifests = {name: _snapshot(current / name) for name in DATA_SUBDIRS}

        # 3. create & validate the new location
        try:
            target.mkdir(parents=True, exist_ok=True)
            probe = target / ".dataroot-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            raise ValueError(f"无法写入新数据目录：{exc}")

        # 4. copy data dirs
        import shutil

        for name in DATA_SUBDIRS:
            src = current / name
            dst = target / name
            if dst.exists():
                shutil.rmtree(dst)
            if src.exists():
                shutil.copytree(src, dst)
            else:
                dst.mkdir(parents=True, exist_ok=True)

        # verify each copied dir matches its source manifest
        for name in DATA_SUBDIRS:
            if _snapshot(target / name) != manifests[name]:
                for sub in DATA_SUBDIRS:
                    leftover = target / sub
                    if leftover.exists():
                        shutil.rmtree(leftover)
                raise ValueError(f"迁移校验失败：{name} 内容不一致，已回滚，原目录未改动")

        # 5. atomic anchor switch
        anchor = _read_anchor()
        history = anchor.get("history") or []
        history.insert(
            0,
            {
                "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from": str(current),
                "to": str(target),
            },
        )
        _write_anchor({"data_root": str(target), "history": history[:10]})

        _cache["mtime"] = None
        _cache["root"] = None
    finally:
        with _migrating_lock:
            _migrating = False
    return root_info()


def rollback() -> dict:
    """Point the anchor back to the most recent previous root.

    Files are never deleted, so the previous root is still intact on disk.
    """
    anchor = _read_anchor()
    history = anchor.get("history") or []
    if not history:
        raise ValueError("没有可回滚的旧目录")
    previous = history[0]
    _write_anchor({"data_root": previous["from"], "history": history[1:]})
    _cache["mtime"] = None
    _cache["root"] = None
    return root_info()
