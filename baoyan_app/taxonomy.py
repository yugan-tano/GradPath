from __future__ import annotations

# NOTE: UI-facing enums (categories, stages, statuses, priorities, topics)
# now live in scenes/<id>/scene.json as inline field options. This module
# keeps only material-classification helpers and the analytics grouping sets
# used by the dashboard, which are business logic rather than entity config.

RESOURCE_STAGE_BY_CATEGORY = {
    "基本材料": "通用",
    "套磁": "套磁",
    "院校": "夏令营",
    "项目": "科研",
    "面试": "面试",
    "参考": "通用",
}

# 总览统计口径（推免场景业务逻辑）
PROGRAM_APPLIED_STATUSES = {"报名", "入营", "参营", "优营", "通过", "未通过", "入营放弃", "优营放弃", "鸽了", "被鸽了"}
PROGRAM_ADMITTED_STATUSES = {"入营", "参营", "优营", "通过", "入营放弃", "优营放弃"}
PROGRAM_EXCELLENT_STATUSES = {"优营", "通过"}
PROGRAM_NEGATIVE_STATUSES = {"未通过", "入营放弃", "优营放弃", "放弃报名", "鸽了", "被鸽了"}

CONTACTED_PROFESSOR_STATUSES = {"已发送", "官回", "养鱼", "已回复", "约面试", "面试通过", "无回复", "默拒", "拒绝"}
REPLIED_PROFESSOR_STATUSES = {"官回", "养鱼", "已回复", "约面试", "面试通过", "拒绝", "暂缓"}


def normalize_category(value: str) -> str:
    mapping = {
        "申请材料": "基本材料",
        "基础材料": "基本材料",
        "套磁资源": "套磁",
        "导师论文": "套磁",
        "择校参考": "院校",
        "夏令营材料": "院校",
        "科研项目": "项目",
        "项目材料": "项目",
        "面试材料": "面试",
        "参考资料": "参考",
        "其他": "参考",
    }
    return mapping.get(value or "", value or "参考")


def default_stage_for_category(category: str) -> str:
    return RESOURCE_STAGE_BY_CATEGORY.get(category, "通用")
