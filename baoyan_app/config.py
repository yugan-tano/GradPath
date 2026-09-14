from __future__ import annotations

import os
from pathlib import Path

from .dataroot import app_root

# Static, code-side paths (never move with the data root).
ROOT = app_root()
WEB_DIR = ROOT / "web"

HOST = "127.0.0.1"
PORT = int(os.environ.get("BAOYAN_PORT", "8848"))
MAX_UPLOAD_BYTES = 80 * 1024 * 1024
MAX_AVATAR_BYTES = 5 * 1024 * 1024

DEFAULT_SETTINGS = {
    "brandTitle": "推免准备",
    "workspaceName": "本地私有工作台",
    "avatarText": "推",
    "avatarMode": "text",
    "motto": "金鳞岂是池中物，一遇风云便化龙",
    "theme": "default",
    "schoolColors": "{}",
    "github": "https://github.com/BlairCode/baoyan_workbench",
}
