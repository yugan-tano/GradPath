"""申博场景业务钩子。

引擎保持通用；这里承载申博特有的业务逻辑：资料分类、套磁聚合、总览统计、
导师清理级联、启动归一化。
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from engine.db import connect
from engine.dataroot import source_dir
from engine.utils import now_text, relative_text, rows_to_dicts


# ---------------------------------------------------------------------------
# 文件分类
# ---------------------------------------------------------------------------

def classify_file(path: Path) -> dict:
    rel = relative_text(path)
    parts = path.relative_to(source_dir().parent).parts
    folder = str(Path(*parts[:-1])) if len(parts) > 1 else ""
    joined = "/".join(parts)
    ext = path.suffix.lower()

    category, stage, kind = "参考", "通用", "参考资料"
    if "套磁信" in joined:
        category, stage, kind = "套磁", "套磁", "套磁信"
    elif "论文" in joined:
        category, stage, kind = "套磁", "套磁", "导师论文"
    elif "面试" in joined or "自我介绍" in path.name:
        category, stage, kind = "面试", "面试", "面试材料"
    elif any(key in path.name for key in ["简历", "成绩", "证明", "证书", "研究计划"]):
        category, stage, kind = "基本材料", "通用", "基础材料"

    return {
        "category": category,
        "stage": stage,
        "kind": kind,
        "folder": folder,
        "relative_path": rel,
        "related_professor": infer_related_professor(path, kind),
        "related_program": "",
    }


def clean_professor_name(value: str) -> str:
    name = Path(value).stem
    name = re.sub(r"^套磁信[\s\-_—－]*", "", name)
    return name.strip(" \t\r\n-_—－")


def infer_related_professor(path: Path, kind: str) -> str:
    if kind == "套磁信":
        name = clean_professor_name(path.name)
        blocked = {"套磁信", "模板", "申请书", "自我介绍"}
        return "" if name in blocked or any(word in name for word in blocked) else name
    return ""


# ---------------------------------------------------------------------------
# 套磁聚合
# ---------------------------------------------------------------------------

def contact_workspace() -> dict:
    with connect() as conn:
        professors = rows_to_dicts(
            conn.execute("select * from professors where status != '已归档' order by display_order asc, name asc").fetchall()
        )
        resources = rows_to_dicts(
            conn.execute(
                "select * from materials where missing = 0 and (category = '套磁' or related_professor != '') order by related_professor = '', related_professor asc, resource_kind asc, mtime desc"
            ).fetchall()
        )
    for row in resources:
        row["actions"] = _material_actions(row)
    by_prof: dict[str, dict] = {}
    for prof in professors:
        key = (prof["name"] or "").strip()
        by_prof[key] = {**prof, "letters": [], "related": []}
    unassigned = {"items": []}
    for item in resources:
        target = (item["related_professor"] or "").strip()
        if target and target not in by_prof:
            by_prof[target] = {
                "id": None, "name": target, "school": "", "college": "", "direction": "",
                "email": "", "homepage": "", "status": "待补充", "note": "由文件名自动识别，尚未建立导师记录。",
                "letters": [], "related": [],
            }
        if target:
            bucket = "letters" if item["resource_kind"] == "套磁信" else "related"
            by_prof[target][bucket].append(item)
        else:
            unassigned["items"].append(item)
    professors = sorted(by_prof.values(), key=lambda row: (row.get("display_order") or 100000, row.get("name") or ""))
    return {"professors": professors, "unassigned": unassigned}


# ---------------------------------------------------------------------------
# 总览统计
# ---------------------------------------------------------------------------

CONTACTED = {"已发送", "已回复", "约面试", "面试通过", "无回复", "拒绝"}
REPLIED = {"已回复", "约面试", "面试通过"}
ADMITTED = {"拟录取", "已录取"}


def summary() -> dict:
    with connect() as conn:
        total_schools = _count(conn, "select count(*) as n from schools")
        total_apps = _count(conn, "select count(*) as n from applications")
        admitted = _count(conn, f"select count(*) as n from applications where status in ({_ph(len(ADMITTED))})", tuple(ADMITTED))
        professors = rows_to_dicts(conn.execute("select * from professors where status != '已归档'").fetchall())
        sent = sum(1 for p in professors if p.get("status") in CONTACTED)
        replied = sum(1 for p in professors if p.get("status") in REPLIED)
        tasks_open = _count(conn, "select count(*) as n from tasks where status != '已完成'")
        school_status = rows_to_dicts(conn.execute("select status as name, count(*) as count from schools group by status order by count desc").fetchall())
        professor_status = _breakdown(professors)

    def _pct(part, whole):
        return round(part / whole * 100, 1) if whole else 0

    metrics = [
        {"label": "目标院校", "labelEn": "Schools", "value": str(total_schools), "score": _pct(total_schools, max(total_schools, 1))},
        {"label": "申请", "labelEn": "Applications", "value": f"{admitted}/{total_apps}", "score": _pct(admitted, total_apps)},
        {"label": "套磁回复", "labelEn": "Replies", "value": f"{replied}/{sent}", "score": _pct(replied, sent)},
        {"label": "待办", "labelEn": "Open tasks", "value": str(tasks_open), "score": max(0, 100 - tasks_open * 8)},
    ]
    charts = [
        {"title": "院校状态", "titleEn": "School status", "rows": school_status, "jump": "schools", "jumpLabel": "管理院校", "jumpLabelEn": "Manage"},
        {"title": "导师状态", "titleEn": "Professor status", "rows": professor_status, "jump": "contact", "jumpLabel": "前往套磁", "jumpLabelEn": "Contact"},
    ]
    return {"metrics": metrics, "charts": charts}


def _count(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()["n"]


def _ph(n):
    return ",".join(["?"] * n)


def _breakdown(rows):
    counts = Counter((row.get("status") or "未填写").strip() or "未填写" for row in rows)
    return [{"name": name, "count": count} for name, count in counts.most_common()]


# ---------------------------------------------------------------------------
# 材料动作 / 级联删除 / 启动归一化
# ---------------------------------------------------------------------------

def _material_actions(row):
    ext = (row.get("ext") or "").lower()
    can_preview = ext in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".md", ".csv"}
    return {"canPreview": can_preview, "openUrl": f"/api/materials/{row['id']}/open", "viewUrl": f"/files/{row['id']}/view"}


def material_actions(row):
    return _material_actions(row)


def after_delete(table: str, row_id: int, row: dict | None) -> None:
    if table == "professors" and row:
        with connect() as conn:
            conn.execute("update materials set related_professor = '' where related_professor = ?", (row.get("name", ""),))


def bootstrap() -> None:
    with connect() as conn:
        rows = conn.execute("select id, display_order from professors where status != '已归档' order by display_order asc, id asc").fetchall()
        for index, row in enumerate(rows, start=1):
            if row["display_order"] != index:
                conn.execute("update professors set display_order = ? where id = ?", (index, row["id"]))
