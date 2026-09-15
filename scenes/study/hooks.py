"""学习场景业务钩子。

引擎保持通用；这里承载学习特有的业务逻辑：资料分类、总览统计。
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
    if "教材" in joined or "课本" in joined or "textbook" in joined:
        category = "教材"
    elif "课件" in joined or "ppt" in joined or "slide" in joined or "讲义" in joined:
        category = "课件"
    elif "笔记" in joined or "note" in joined:
        category = "笔记"
    elif "作业" in joined or "hw" in joined or "homework" in joined:
        category = "作业"
    elif "考试" in joined or "试卷" in joined or "exam" in joined or "真题" in joined:
        category = "考试"
    elif "论文" in joined or "paper" in joined:
        category = "论文"
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


def _grade_point(score: float) -> float:
    """Map a 0-100 score to a 4.0-scale grade point (common Chinese scale)."""
    if score >= 90:
        return 4.0
    if score >= 85:
        return 3.7
    if score >= 82:
        return 3.3
    if score >= 78:
        return 3.0
    if score >= 75:
        return 2.7
    if score >= 72:
        return 2.3
    if score >= 68:
        return 2.0
    if score >= 64:
        return 1.5
    if score >= 60:
        return 1.0
    return 0.0


GRADE_MAP = [
    {"range": "90 - 100", "gp": 4.0},
    {"range": "85 - 89", "gp": 3.7},
    {"range": "82 - 84", "gp": 3.3},
    {"range": "78 - 81", "gp": 3.0},
    {"range": "75 - 77", "gp": 2.7},
    {"range": "72 - 74", "gp": 2.3},
    {"range": "68 - 71", "gp": 2.0},
    {"range": "64 - 67", "gp": 1.5},
    {"range": "60 - 63", "gp": 1.0},
    {"range": "0 - 59", "gp": 0.0},
]


def _weighted(rows: list[dict]) -> dict:
    """Weighted GPA / average over graded courses (score > 0)."""
    total_credits = sum(float(row.get("credits") or 0) for row in rows)
    graded = [row for row in rows if float(row.get("score") or 0) > 0]
    graded_credits = sum(float(row.get("credits") or 0) for row in graded)
    gpa = sum(float(row.get("credits") or 0) * _grade_point(float(row["score"])) for row in graded)
    avg_score = sum(float(row.get("credits") or 0) * float(row["score"]) for row in graded)
    if graded_credits:
        gpa = round(gpa / graded_credits, 3)
        avg_score = round(avg_score / graded_credits, 1)
    else:
        gpa = avg_score = 0.0
    return {
        "courses": len(rows),
        "credits": total_credits,
        "graded": len(graded),
        "gradedCredits": round(graded_credits, 1),
        "gpa": gpa,
        "avgScore": avg_score,
    }


def stats() -> dict:
    with connect() as conn:
        rows = rows_to_dicts(conn.execute("select * from courses").fetchall())

    overall = _weighted(rows)

    by_semester: dict[str, list[dict]] = {}
    for row in rows:
        semester = (row.get("semester") or "").strip() or "未填写"
        by_semester.setdefault(semester, []).append(row)
    semesters = []
    for semester, course_rows in by_semester.items():
        w = _weighted(course_rows)
        semesters.append(
            {
                "semester": semester,
                "courses": w["courses"],
                "credits": w["credits"],
                "graded": w["graded"],
                "gpa": w["gpa"],
                "avgScore": w["avgScore"],
            }
        )
    # 按学期名排序，未填写排最后
    semesters.sort(key=lambda item: (item["semester"] == "未填写", item["semester"]))

    def _score(part, whole):
        return round(part / whole * 100, 1) if whole else 0

    metrics = [
        {"label": "课程数", "labelEn": "Courses", "value": str(overall["courses"]), "score": _score(overall["graded"], overall["courses"])},
        {"label": "总学分", "labelEn": "Total credits", "value": str(round(overall["credits"], 1)), "score": 100},
        {"label": "加权绩点", "labelEn": "Weighted GPA", "value": f"{overall['gpa']:.2f}", "score": _score(overall["gpa"], 4.0)},
        {"label": "加权均分", "labelEn": "Weighted average", "value": f"{overall['avgScore']:.1f}", "score": overall["avgScore"]},
        {"label": "已出成绩", "labelEn": "Graded", "value": f"{overall['graded']}/{overall['courses']}", "score": _score(overall["graded"], overall["courses"])},
    ]
    return {"metrics": metrics, "gradeMap": GRADE_MAP, "semesters": semesters}


def summary() -> dict:
    with connect() as conn:
        total_courses = _count(conn, "select count(*) as n from courses")
        done_courses = _count(conn, "select count(*) as n from courses where status = '已结课'")
        exams_open = _count(conn, "select count(*) as n from exams where status != '已完成'")
        avg_score = conn.execute("select coalesce(avg(score), 0) as a from courses where score > 0").fetchone()["a"]
        tasks_open = _count(conn, "select count(*) as n from tasks where status != '已完成'")
        course_status = rows_to_dicts(conn.execute("select status as name, count(*) as count from courses group by status order by count desc").fetchall())
        exam_status = rows_to_dicts(conn.execute("select status as name, count(*) as count from exams group by status order by count desc").fetchall())

    metrics = [
        {"label": "课程", "labelEn": "Courses", "value": str(total_courses), "score": round(done_courses / total_courses * 100, 1) if total_courses else 0},
        {"label": "已结课", "labelEn": "Done", "value": str(done_courses), "score": round(done_courses / total_courses * 100, 1) if total_courses else 0},
        {"label": "待办考试", "labelEn": "Open exams", "value": str(exams_open), "score": max(0, 100 - exams_open * 10)},
        {"label": "平均成绩", "labelEn": "Avg score", "value": f"{avg_score:.1f}", "score": round(float(avg_score), 1)},
        {"label": "待办", "labelEn": "Open tasks", "value": str(tasks_open), "score": max(0, 100 - tasks_open * 8)},
    ]
    charts = [
        {"title": "课程状态", "titleEn": "Course status", "rows": course_status, "jump": "courses", "jumpLabel": "管理课程", "jumpLabelEn": "Manage"},
        {"title": "考试状态", "titleEn": "Exam status", "rows": exam_status, "jump": "exams", "jumpLabel": "管理考试", "jumpLabelEn": "Manage"},
    ]
    return {"metrics": metrics, "charts": charts}
