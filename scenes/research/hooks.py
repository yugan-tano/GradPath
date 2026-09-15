"""科研场景业务钩子。

引擎保持通用；这里承载科研特有的业务逻辑：资料分类、总览统计。
"""

from __future__ import annotations

from pathlib import Path

from engine.db import connect
from engine.dataroot import source_dir
from engine.utils import relative_text, rows_to_dicts


def classify_file(path: Path) -> dict:
    rel = relative_text(path)
    parts = path.relative_to(source_dir().parent).parts
    folder = str(Path(*parts[:-1])) if len(parts) > 1 else ""
    joined = "/".join(parts).lower()
    category = "参考"
    if "文献" in joined or "paper" in joined or "pdf" in joined:
        category = "文献"
    elif "数据" in joined or "data" in joined or "dataset" in joined:
        category = "数据"
    elif "代码" in joined or "code" in joined or "src" in joined:
        category = "代码"
    elif "实验" in joined or "experiment" in joined or "记录" in joined:
        category = "实验记录"
    elif "论文" in joined or "manuscript" in joined or "draft" in joined:
        category = "论文"
    elif "汇报" in joined or "ppt" in joined or "slide" in joined or "组会" in joined:
        category = "汇报"
    return {
        "category": category,
        "stage": "通用",
        "kind": category,
        "folder": folder,
        "relative_path": rel,
        "related_professor": "",
        "related_program": "",
    }


def _count(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()["n"]


def summary() -> dict:
    with connect() as conn:
        total_projects = _count(conn, "select count(*) as n from projects")
        active_projects = _count(conn, "select count(*) as n from projects where status = '进行中'")
        total_papers = _count(conn, "select count(*) as n from papers")
        published = _count(conn, "select count(*) as n from papers where status in ('已录用', '已发表')")
        experiments_open = _count(conn, "select count(*) as n from experiments where status in ('计划中', '进行中')")
        tasks_open = _count(conn, "select count(*) as n from tasks where status != '已完成'")
        project_status = rows_to_dicts(conn.execute("select status as name, count(*) as count from projects group by status order by count desc").fetchall())
        paper_status = rows_to_dicts(conn.execute("select status as name, count(*) as count from papers group by status order by count desc").fetchall())

    metrics = [
        {"label": "项目", "labelEn": "Projects", "value": str(total_projects), "score": round(active_projects / total_projects * 100, 1) if total_projects else 0},
        {"label": "进行中", "labelEn": "Active", "value": str(active_projects), "score": round(active_projects / total_projects * 100, 1) if total_projects else 0},
        {"label": "论文", "labelEn": "Papers", "value": f"{published}/{total_papers}", "score": round(published / total_papers * 100, 1) if total_papers else 0},
        {"label": "待做实验", "labelEn": "Open experiments", "value": str(experiments_open), "score": max(0, 100 - experiments_open * 8)},
        {"label": "待办", "labelEn": "Open tasks", "value": str(tasks_open), "score": max(0, 100 - tasks_open * 8)},
    ]
    charts = [
        {"title": "项目状态", "titleEn": "Project status", "rows": project_status, "jump": "projects", "jumpLabel": "管理项目", "jumpLabelEn": "Manage"},
        {"title": "论文状态", "titleEn": "Paper status", "rows": paper_status, "jump": "papers", "jumpLabel": "管理论文", "jumpLabelEn": "Manage"},
    ]
    return {"metrics": metrics, "charts": charts}
