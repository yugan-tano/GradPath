from __future__ import annotations

import os
from pathlib import Path

from .dataroot import app_root

# Static, code-side paths (never move with the data root).
ROOT = app_root()
WEB_DIR = ROOT / "web"

HOST = "127.0.0.1"
PORT = int(os.environ.get("GRADPATH_PORT", "8848"))
MAX_UPLOAD_BYTES = 80 * 1024 * 1024
MAX_AVATAR_BYTES = 5 * 1024 * 1024
