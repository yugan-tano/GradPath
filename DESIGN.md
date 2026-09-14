# 本地优先通用 SOP 工作台 — 设计文档

> 以 `baoyan_workbench` 为基底，抽出「引擎 + 场景包」分层。本文档记录架构约定与存储分工规则，是所有后续实现步骤的硬约束。

## 1. 目标

- **完全本地**：数据存用户指定目录，不依赖云服务。
- **打开即用**：Python 标准库 + SQLite + 原生前端，零安装/极低安装成本。
- **场景可插拔**：加新场景（推免/科研/申博）只写 JSON 配置，不改引擎代码。
- **照检查照填**：阶段驱动，明确检查项与必停点，不靠用户自己判断"现在该干什么"。

## 2. 架构分层

### 引擎层（代码，加场景不改）

| 能力 | 说明 |
| --- | --- |
| DataRoot 存储 | 数据根目录锚点、六步迁移、回滚、备份 |
| SQLite 连接/迁移 | 建表、增量字段迁移、种子数据 |
| 通用实体 CRUD | 配置驱动的列表/新增/更新/删除/排序 |
| 状态机执行器 | 实体状态枚举与转移（由配置声明） |
| SOP 阶段引擎 | 幕-阶段-检查项树、条件求值、必停点 |
| 清单核对 | 通用可挂载检查项 + 进度计算 |
| 模板渲染 | 字段填空 → 文书生成 |
| 文件索引 | 本地文件扫描、逐层浏览、关联 |
| 时间线 | 截止日期、阶段任务、跨年度节点 |
| 配置驱动前端 | 只支持 8 种字段类型的通用渲染器 |

### 场景包层（配置，只写 JSON）

`scenes/<id>/scene.json` 描述：场景元信息、实体（字段 + 状态机）、幕-阶段树、清单、模板、时间线。加新场景 = 新增目录，不动引擎。

## 3. 存储分工规则（设计约定 A）

> 一句话：**可查询/排序/关联的进 SQLite；需要人读/可版本控制/可手改的进 JSON/Markdown；同一事实绝不存两处。**

| 数据 | 落点 | 理由 |
| --- | --- | --- |
| 实体（院校/导师/材料索引）、待办、清单勾选状态、settings | SQLite | 需查询/排序/关联/统计 |
| 阶段进度、必停点快照、决策日志 | `state/*.json` | 人类可读、可 git 同步、可手改恢复 |
| 文书模板、生成产物 | `*.md` | 文本文件、可版本控制、可外部备份 |
| 数据根目录锚点、迁移记录 | `data_root.json` | 启动时读，人类可读可回滚 |

数据目录结构：

```text
<数据根目录>/
├─ data/
│  ├─ app.db          # SQLite
│  ├─ backups/        # 一键备份
│  ├─ avatar.*        # 头像
│  └─ state/          # 阶段进度/决策日志（JSON）
├─ 保研准备/           # 用户材料文件（资源页扫描根）
└─ ...
```

锚点 `data_root.json` 位于系统应用数据目录（Windows `%LOCALAPPDATA%\gradpath\`，类 Unix `~/.config/gradpath/`），记录当前根目录与迁移历史。默认（无锚点）数据根 = 程序安装目录。

## 4. 字段类型最小集（设计约定 B）

渲染器只支持这 8 种字段类型，场景包不得发明新类型：

`text / textarea / number / date / select / multiselect / checkbox / file`

## 5. 条件表达式语法（设计约定 C，第 4 步冻结）

进入/完成条件用声明式 JSON 表达，组合子 + 原子谓词两层：

```json
{ "all": [cond, ...] }
{ "any": [cond, ...] }
{ "not": cond }
```

原子谓词（`op` 固定集合）：

```json
{ "op": "fieldEmpty", "entity": "professors", "field": "direction" }
{ "op": "fieldEq",    "entity": "professors", "field": "status", "value": "已发送" }
{ "op": "fieldIn",    "entity": "professors", "field": "status", "values": ["已发送","已回复"] }
{ "op": "count",      "entity": "professors", "filter": { "field": "status", "values": ["已发送"] }, "min": 5 }
{ "op": "checklist",  "checklist": "basic_materials", "target": 1.0 }
{ "op": "stageDone",  "stage": "materials" }
{ "op": "deadline",   "timeline": "summer_camp", "cmp": "passed" }
```

求值器是纯函数：输入（当前场景状态 + 条件 JSON）→ 输出（bool + 未满足项说明）。

## 6. 必停点与 stage/task 语义（设计约定 D）

- **必停点 enforcement**：后端是唯一事实源，推进到下一阶段时校验退出条件，不满足则拒绝并返回未满足项说明；前端仅置灰按钮做呈现。
- **task 完成 ≠ stage 完成**：阶段完成只由 `exit` 条件决定，task 是挂在阶段下的引导性待办。
- **清单统一模型**：`checklist_items` 是可挂载任意 owner 的通用表（entity 实例 / stage / scene 全局）。

## 7. 路径可配置与迁移（第 1 步已实现）

见 `baoyan_app/dataroot.py`。六步迁移：暂停写入 → 一致性快照 → 创建并验证新位置 → 迁移并校验 → 原子切换 → 保留回滚副本。回滚仅重指锚点，旧目录保留。
