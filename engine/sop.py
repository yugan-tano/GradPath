"""SOP stage engine.

A scene declares an ``acts`` tree: act -> stage -> checklists, plus ``enter``/
``exit`` conditions and ``mandatory`` stops. This module evaluates those
declarative conditions against the live database and drives stage transitions.

Condition grammar (design convention C):
    {"all": [cond, ...]}   {"any": [cond, ...]}   {"not": cond}
    atomic predicates:
        {"op": "fieldEmpty", "entity": "professors", "field": "direction"}
        {"op": "fieldEq",    "entity": "professors", "field": "status", "value": "已发送"}
        {"op": "fieldIn",    "entity": "professors", "field": "status", "values": [...]}
        {"op": "count",      "entity": "professors", "filter": {...}, "min": 5}
        {"op": "checklist",  "checklist": "basic_materials", "target": 1.0}
        {"op": "stageDone",  "stage": "materials"}
"""

from __future__ import annotations

from . import checklist
from .db import connect
from .scene import active_scene, scene_acts
from .utils import now_text


def list_acts() -> list[dict]:
    acts = scene_acts()
    states = _stage_states()
    result = []
    for act in acts:
        item = dict(act)
        stages = []
        for stage in act.get("stages", []):
            s = dict(stage)
            s["state"] = states.get(stage["id"], {"status": "pending", "notes": ""})
            enter_ok, enter_reasons = evaluate(stage.get("enter"))
            exit_ok, exit_reasons = evaluate(stage.get("exit"))
            s["enterOk"] = enter_ok
            s["enterReasons"] = enter_reasons
            s["exitOk"] = exit_ok
            s["exitReasons"] = exit_reasons
            stages.append(s)
        item["stages"] = stages
        result.append(item)
    return result


def _stage_states() -> dict[str, dict]:
    scene_id = active_scene().get("id", "")
    with connect() as conn:
        rows = conn.execute("select * from stage_state where scene = ?", (scene_id,)).fetchall()
    return {row["stage"]: {"status": row["status"], "notes": row["notes"]} for row in rows}


def _set_stage_state(stage: str, status: str, notes: str = "") -> None:
    scene_id = active_scene().get("id", "")
    with connect() as conn:
        conn.execute(
            """
            insert into stage_state (scene, stage, status, notes, updated_at)
            values (?, ?, ?, ?, ?)
            on conflict(scene, stage) do update set status = excluded.status, notes = excluded.notes, updated_at = excluded.updated_at
            """,
            (scene_id, stage, status, notes, now_text()),
        )


def evaluate(cond) -> tuple[bool, list[str]]:
    """Evaluate a condition to (satisfied, unmet_reasons)."""
    if not cond:
        return True, []
    if "all" in cond:
        ok, reasons = True, []
        for sub in cond["all"]:
            sub_ok, sub_reasons = evaluate(sub)
            if not sub_ok:
                ok = False
                reasons.extend(sub_reasons)
        return ok, reasons
    if "any" in cond:
        reasons = []
        for sub in cond["any"]:
            sub_ok, sub_reasons = evaluate(sub)
            if sub_ok:
                return True, []
            reasons.extend(sub_reasons)
        return False, [f"以下任一条件未满足：{'; '.join(reasons) or '无'}"]
    if "not" in cond:
        ok, _ = evaluate(cond["not"])
        return (not ok), ([] if not ok else ["否定条件不应满足"])
    return _evaluate_atom(cond)


def _evaluate_atom(cond: dict) -> tuple[bool, list[str]]:
    op = cond.get("op")
    if op == "fieldEmpty":
        return _count_where(cond["entity"], f"{cond['field']} = '' or {cond['field']} is null") == 0, [
            f"存在 {cond['field']} 未填写"
        ]
    if op == "fieldEq":
        value = cond.get("value", "")
        n = _count_where(cond["entity"], f"{cond['field']} = ?", (value,))
        ok = n > 0
        return ok, ([] if ok else [f"没有 {cond['field']} 为「{value}」的记录"])
    if op == "fieldIn":
        values = cond.get("values", [])
        if not values:
            return False, ["values 为空"]
        placeholders = ",".join(["?"] * len(values))
        n = _count_where(cond["entity"], f"{cond['field']} in ({placeholders})", tuple(values))
        ok = n > 0
        return ok, ([] if ok else [f"没有 {cond['field']} 属于 {values}"])
    if op == "count":
        filt = cond.get("filter") or {}
        field = filt.get("field")
        values = filt.get("values") or []
        placeholders = ",".join(["?"] * len(values))
        n = _count_where(cond["entity"], f"{field} in ({placeholders})", tuple(values)) if field else _count_where(cond["entity"], "1=1")
        minimum = cond.get("min", 1)
        ok = n >= minimum
        return ok, ([] if ok else [f"数量 {n} 未达到 {minimum}"])
    if op == "checklist":
        progress = checklist.global_progress(cond.get("checklist", ""))
        target = cond.get("target", 1.0)
        ok = progress >= target
        return ok, ([] if ok else [f"清单进度 {progress:.0%} 未达到 {target:.0%}"])
    if op == "stageDone":
        states = _stage_states()
        ok = states.get(cond.get("stage", ""), {}).get("status") == "done"
        return ok, ([] if ok else [f"阶段「{cond.get('stage')}」尚未完成"])
    raise ValueError(f"未知条件操作：{op}")


def _count_where(entity: str, where: str, params: tuple = ()) -> int:
    with connect() as conn:
        row = conn.execute(f"select count(*) as n from {entity} where {where}", params).fetchone()
    return row["n"] if row else 0


def advance_stage(stage_id: str) -> dict:
    """Move a stage forward. Enforces mandatory exit conditions server-side."""
    stage, act = _find_stage(stage_id)
    if not stage:
        raise KeyError(f"阶段不存在：{stage_id}")
    current = _stage_states().get(stage_id, {}).get("status", "pending")
    if current == "done":
        return {"ok": True, "stage": stage_id, "status": "done", "already": True}

    exit_ok, exit_reasons = evaluate(stage.get("exit"))
    if not exit_ok:
        raise PermissionError("必停点：退出条件未满足 → " + "；".join(exit_reasons))
    enter_ok, enter_reasons = evaluate(stage.get("enter"))
    if not enter_ok:
        raise PermissionError("进入条件未满足 → " + "；".join(enter_reasons))

    _set_stage_state(stage_id, "done")
    # auto-activate the next stage in the same act
    next_stage = _next_stage(stage_id, act)
    if next_stage:
        _set_stage_state(next_stage["id"], "active")
    return {"ok": True, "stage": stage_id, "status": "done", "next": next_stage["id"] if next_stage else None}


def start_stage(stage_id: str) -> dict:
    stage, act = _find_stage(stage_id)
    if not stage:
        raise KeyError(f"阶段不存在：{stage_id}")
    enter_ok, enter_reasons = evaluate(stage.get("enter"))
    if not enter_ok:
        raise PermissionError("进入条件未满足 → " + "；".join(enter_reasons))
    _set_stage_state(stage_id, "active")
    return {"ok": True, "stage": stage_id, "status": "active"}


def reset_stage(stage_id: str) -> dict:
    _set_stage_state(stage_id, "pending", "")
    return {"ok": True, "stage": stage_id, "status": "pending"}


def _find_stage(stage_id: str) -> tuple[dict | None, dict | None]:
    for act in scene_acts():
        for stage in act.get("stages", []):
            if stage.get("id") == stage_id:
                return stage, act
    return None, None


def _next_stage(stage_id: str, act: dict) -> dict | None:
    stages = act.get("stages", [])
    for i, stage in enumerate(stages):
        if stage.get("id") == stage_id and i + 1 < len(stages):
            return stages[i + 1]
    return None
