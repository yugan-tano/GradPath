"""推免场景业务钩子。

引擎保持通用；这里承载推免特有的业务逻辑：文件分类、套磁聚合、总览统计、
导师清理级联、状态归一化。新增场景时复制本文件并按需改写即可，引擎无需改动。
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
    elif "项目" in joined:
        category, stage, kind = "项目", "科研", "项目材料"
    elif "夏令营" in joined:
        category, stage, kind = "院校", "夏令营", "夏令营材料"
    elif any(key in path.name for key in ["简历", "成绩", "证明", "证书", "奖状", "四级", "六级"]):
        category, stage, kind = "基本材料", "通用", "基础材料"
    elif ext in {".ppt", ".pptx"} or any(key in path.name for key in ["自我介绍", "面试"]):
        category, stage, kind = "面试", "面试", "面试材料"

    if path.name in {"保研层级.png", "保研高校排行.png", "学科评估.png", "保研.xmind"}:
        category, stage, kind = "院校", "通用", "参考资料"

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
    name = re.sub(r"^[A-Za-z]{2,10}[-_]", "", name)
    return name.strip(" \t\r\n-_—－")


def infer_related_professor(path: Path, kind: str) -> str:
    stem = path.stem
    if kind == "套磁信":
        name = clean_professor_name(path.name)
        blocked = {"套磁信", "模板", "申请书", "自我介绍"}
        return "" if name in blocked or any(word in name for word in blocked) else name
    with connect() as conn:
        names = {row["name"] for row in conn.execute("select name from professors where trim(name) != ''").fetchall()}
    for name in sorted(names, key=len, reverse=True):
        if stem.startswith(name) or f"-{name}" in stem or f"_{name}" in stem:
            return name
    return ""


# ---------------------------------------------------------------------------
# 套磁聚合
# ---------------------------------------------------------------------------

def professor_key(name: str) -> str:
    value = str(name or "").strip().lstrip("-_—－ ").strip()
    for prefix in ["NJUST-", "NJUST_", "NJUST"]:
        if value.startswith(prefix):
            value = value[len(prefix):].lstrip("-_—－ ").strip()
    return value


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
        key = professor_key(prof["name"])
        item = {**prof, "name": key or prof["name"], "letters": [], "related": []}
        by_prof[key] = item
    unassigned = {"items": []}
    for item in resources:
        target = professor_key(item["related_professor"])
        item["related_professor"] = target
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

CONTACTED = {"已发送", "官回", "养鱼", "已回复", "约面试", "面试通过", "无回复", "默拒", "拒绝"}
REPLIED = {"官回", "养鱼", "已回复", "约面试", "面试通过", "拒绝", "暂缓"}
APPLIED = {"报名", "入营", "参营", "优营", "通过", "未通过", "入营放弃", "优营放弃", "鸽了", "被鸽了"}
ADMITTED = {"入营", "参营", "优营", "通过", "入营放弃", "优营放弃"}
EXCELLENT = {"优营", "通过"}
NEGATIVE = {"未通过", "入营放弃", "优营放弃", "放弃报名", "鸽了", "被鸽了"}


def summary() -> dict:
    with connect() as conn:
        total_programs = _count(conn, "select count(*) as n from programs")
        camp_total = _count(conn, "select count(*) as n from programs where stage = '夏令营'")
        camp_applied = _count(conn, f"select count(*) as n from programs where stage = '夏令营' and status in ({_ph(len(APPLIED))})", tuple(APPLIED))
        camp_admitted = _count(conn, f"select count(*) as n from programs where stage = '夏令营' and status in ({_ph(len(ADMITTED))})", tuple(ADMITTED))
        camp_excellent = _count(conn, f"select count(*) as n from programs where stage = '夏令营' and status in ({_ph(len(EXCELLENT))})", tuple(EXCELLENT))
        professors = rows_to_dicts(conn.execute("select * from professors where status != '已归档'").fetchall())
        counts = {
            "materials": _count(conn, "select count(*) as n from materials where missing = 0"),
            "programs": total_programs,
            "professors": len(professors),
            "tasksOpen": _count(conn, "select count(*) as n from tasks where status != '已完成'"),
            "sent": sum(1 for p in professors if p.get("status") in CONTACTED),
            "replied": sum(1 for p in professors if p.get("status") in REPLIED),
            "totalLetters": _count(conn, "select count(*) as n from materials where missing = 0 and resource_kind = '套磁信'"),
            "campInterested": camp_total,
            "campApplied": camp_applied,
            "campAdmitted": camp_admitted,
            "campExcellent": camp_excellent,
            "programNegative": _count(conn, f"select count(*) as n from programs where status in ({_ph(len(NEGATIVE))})", tuple(NEGATIVE)),
        }
        categories = rows_to_dicts(conn.execute("select category, count(*) as count from materials where missing = 0 group by category order by count desc").fetchall())
        resource_kinds = rows_to_dicts(conn.execute("select resource_kind as name, count(*) as count from materials where missing = 0 group by resource_kind order by count desc limit 8").fetchall())
        program_status = rows_to_dicts(conn.execute("select status as name, count(*) as count from programs group by status order by count desc").fetchall())
        professor_status = _breakdown(professors)
        task_breakdown = rows_to_dicts(conn.execute("select status as name, count(*) as count from tasks group by status order by count desc").fetchall())
        recent_materials = rows_to_dicts(conn.execute("select * from materials where missing = 0 order by mtime desc limit 8").fetchall())
        open_tasks = rows_to_dicts(conn.execute("select * from tasks where status != '已完成' order by due_date = '', due_date asc, id desc limit 8").fetchall())
        hot_programs = rows_to_dicts(conn.execute("select * from programs order by display_order asc, id desc limit 8").fetchall())
    for row in recent_materials:
        row["actions"] = _material_actions(row)

    def _pct(part: int, whole: int) -> float:
        return round(part / whole * 100, 1) if whole else 0

    metrics = [
        {"label": "夏令营项目", "labelEn": "Summer camps", "value": str(camp_total), "score": _pct(camp_total, total_programs)},
        {"label": "入营/报名", "labelEn": "Admitted / Applied", "value": f"{camp_admitted}/{camp_applied}", "score": _pct(camp_admitted, camp_applied)},
        {"label": "优营", "labelEn": "Excellent camp", "value": str(camp_excellent), "score": _pct(camp_excellent, camp_applied)},
        {"label": "套磁回复", "labelEn": "Replies", "value": f"{counts['replied']}/{counts['sent']}", "score": _pct(counts["replied"], counts["sent"])},
        {"label": "待办", "labelEn": "Open tasks", "value": str(counts["tasksOpen"]), "score": max(0, 100 - counts["tasksOpen"] * 8)},
    ]
    charts = [
        {"title": "院校状态", "titleEn": "Program status", "rows": program_status, "jump": "programs", "jumpLabel": "管理院校", "jumpLabelEn": "Manage"},
        {"title": "导师状态", "titleEn": "Professor status", "rows": professor_status, "jump": "contact", "jumpLabel": "前往套磁", "jumpLabelEn": "Contact"},
    ]

    return {
        "metrics": metrics,
        "charts": charts,
        "counts": counts,
        "rates": {
            "campApplyRate": round(camp_applied / camp_total * 100, 1) if camp_total else 0,
            "campAdmitRate": round(camp_admitted / camp_applied * 100, 1) if camp_applied else 0,
            "replyRate": round(counts["replied"] / counts["sent"] * 100, 1) if counts["sent"] else 0,
        },
        "categories": categories,
        "resourceKinds": resource_kinds,
        "programStatus": program_status,
        "professorStatus": professor_status,
        "stageBreakdown": rows_to_dicts(conn.execute("select stage as name, count(*) as count from programs group by stage order by count desc").fetchall()),
        "taskBreakdown": task_breakdown,
        "recentMaterials": recent_materials,
        "openTasks": open_tasks,
        "programs": hot_programs,
        "root": str(source_dir()),
        "sourceDir": str(source_dir()),
    }


def _count(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()["n"]


def _ph(n):
    return ",".join(["?"] * n)


def _breakdown(rows):
    counts = Counter((row.get("status") or "未填写").strip() or "未填写" for row in rows)
    return [{"name": name, "count": count} for name, count in counts.most_common()]


# ---------------------------------------------------------------------------
# 材料动作 / 资源分组
# ---------------------------------------------------------------------------

def _material_actions(row):
    ext = (row.get("ext") or "").lower()
    can_preview = ext in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".md", ".csv"}
    return {"canPreview": can_preview, "openUrl": f"/api/materials/{row['id']}/open", "viewUrl": f"/files/{row['id']}/view"}


def material_actions(row):
    return _material_actions(row)


def resource_groups():
    with connect() as conn:
        rows = rows_to_dicts(conn.execute("select * from materials where missing = 0 order by category asc, folder asc, resource_kind asc, name asc").fetchall())
    groups: dict[str, dict] = {}
    folders: dict[str, dict] = {}
    for row in rows:
        row["actions"] = _material_actions(row)
        groups.setdefault(row["category"], {"name": row["category"], "count": 0, "items": []})
        groups[row["category"]]["count"] += 1
        groups[row["category"]]["items"].append(row)
        folder_name = row["folder"] or "未归类"
        folders.setdefault(folder_name, {"name": folder_name, "path": str((source_dir().parent / folder_name).resolve()), "count": 0, "items": []})
        folders[folder_name]["count"] += 1
        folders[folder_name]["items"].append(row)
    return {"byCategory": list(groups.values()), "byFolder": list(folders.values())}


# ---------------------------------------------------------------------------
# 扫描后处理 / 级联删除 / 启动归一化
# ---------------------------------------------------------------------------

def after_scan(conn) -> None:
    _ensure_professors_from_letters(conn)


def _ensure_professors_from_letters(conn) -> int:
    created = 0
    rows = conn.execute(
        "select related_professor, name from materials where missing = 0 and resource_kind = '套磁信' and trim(related_professor) != '' order by mtime asc, id asc"
    ).fetchall()
    existing = {row["name"] for row in conn.execute("select name from professors where trim(name) != ''").fetchall()}
    max_order = conn.execute("select coalesce(max(display_order), 0) as n from professors where status != '已归档'").fetchone()["n"]
    blocked = {"套磁信", "模板", "申请书", "自我介绍"}
    for row in rows:
        name = clean_professor_name(row["related_professor"])
        if not name or name in existing or name in blocked or any(word in name for word in blocked):
            continue
        max_order += 1
        conn.execute(
            "insert into professors (name, status, note, display_order, created_at, updated_at) values (?, '待补充', ?, ?, ?, ?)",
            (name, f"已有关联套磁信：{row['name']}", max_order, now_text(), now_text()),
        )
        existing.add(name)
        created += 1
    return created


def after_delete(table: str, row_id: int, row: dict | None) -> None:
    if table == "professors" and row:
        with connect() as conn:
            conn.execute("update materials set related_professor = '' where related_professor = ?", (row.get("name", ""),))


def bootstrap() -> None:
    with connect() as conn:
        # 归档教授显示顺序重排（推免特有：按非归档活跃重排）
        rows = conn.execute("select id, display_order from professors where status != '已归档' order by display_order asc, id asc").fetchall()
        for index, row in enumerate(rows, start=1):
            if row["display_order"] != index:
                conn.execute("update professors set display_order = ? where id = ?", (index, row["id"]))
