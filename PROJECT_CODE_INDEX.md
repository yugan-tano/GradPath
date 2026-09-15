# GradPath 代码定位手册

> 更新日期：2026-09-16
> 用途：快速定位项目入口、页面、接口、数据表、函数和样式。本文覆盖项目源码与工程文件；`保研准备/`、`data/`、`处理文件/` 中的个人资料和运行数据只说明目录职责，不逐份解析其内容。
>
> 架构：**引擎（engine/，通用）+ 场景包（scenes/<id>/，配置 + 钩子）**。业务能力不再写死在引擎里，而是由 `scenes/<id>/scene.json` 声明、由 `scenes/<id>/hooks.py` 提供。

## 1. 系统执行链路

```text
start.bat / launcher.ps1 / python app.py
  → engine.server.main()
  → engine.bootstrap.bootstrap()  初始化引擎表、按场景建实体表、写种子数据、调场景钩子
  → ThreadingHTTPServer 提供静态页面和 JSON API
  → background_material_sync() 后台扫描并同步资料索引
  → web/index.html
  → web/js/main.js
  → dashboard / sop / contact / resources / table 页面模块
```

后端使用 Python 标准库 HTTP 服务与 SQLite；前端使用原生 ES Modules、HTML 和 CSS，无前端构建步骤。

## 2. 根目录文件

### `app.py`

- 轻量启动入口，仅导入并调用 `engine.server.main()`。
- 启动、调试服务入口时首先查看此文件和 `engine/server.py`。

### `start.bat`

- Windows 快速启动脚本，执行 `python app.py`。

### `launcher.ps1`

- 校验 Python 环境、自动打开浏览器、写入诊断日志的启动器。
- 环境变量：`GRADPATH_PYTHON`（指定解释器）、`GRADPATH_OPEN_BROWSER`（默认 1，自动开浏览器）。

### `README.md`

- 面向使用者的项目说明，包含功能、截图、启动方式、端口配置、推荐流程、目录结构、技术栈和许可证。

### `DESIGN.md`

- 架构设计与存储分工约定（设计约定 A/B/C/D），是引擎与场景包边界的硬约束。

### `PROJECT_CODE_INDEX.md`

- 本文件。按目录和文件记录代码职责、主要函数、类与修改入口。

### `.gitignore`

- Git 忽略规则，排除数据库、备份、运行缓存、个人资料与临时产物。

### `LICENSE`

- MIT 开源许可证正文。

## 3. 引擎包 `engine/`（通用能力，加场景不改）

### `engine/__init__.py`

- Python 包标识与包级说明；公开模块名 `server`。

### `engine/config.py`

- 集中定义代码根 `ROOT`、Web 目录、监听地址 `HOST`、端口 `PORT`、上传大小限制。
- 端口读取环境变量 `GRADPATH_PORT`（默认 `8848`）。
- 修改端口默认值和上传上限时定位到这里。

### `engine/dataroot.py`

- **数据根（DataRoot）**：数据根目录锚点、解析与缓存。
  - `app_root()`：代码根目录（`scenes/`、`web/`、包所在位置）。
  - `_app_data_dir()`：系统应用数据目录（Windows `%LOCALAPPDATA%\gradpath\`，类 Unix `~/.config/gradpath/`）。
  - `current_data_root()`：解析当前数据根，读锚点 `data_root.json`，无锚点时回退到代码根。
  - `data_dir()` / `source_dir()` / `state_dir()` / `db_path()`：数据子目录与 SQLite 路径。
- 六步迁移 `migrate()`：暂停写入 → 快照 → 创建并验证新位置 → 复制并校验 → 原子切换锚点 → 保留旧目录。`rollback()` 仅重指锚点。
- `writes_paused()`：迁移期间标记，HTTP 处理器据此拒绝写入。
- `root_info()`：当前根目录与迁移历史。

### `engine/db.py`

- `connect()`：创建数据目录、连接 `data/app.db` 并启用字典式行访问。
- `ensure_column()`：为旧数据库补加缺失列。
- `init_db()`：**只创建引擎自身的三张表** `settings`、`checklist_items`、`stage_state`。
- 实体表（院校/导师/文件/待办/面试题）**不在此硬编码**，由 `engine/scene.py` 依据 `scene.json` 创建。这是引擎/场景分离的核心。

### `engine/scene.py`

- 场景配置加载器：从 `scenes/<id>/scene.json` 读取并缓存。
- `active_scene_id()` / `active_scene()`：读取环境变量 `GRADPATH_SCENE`（默认 `tuimian`）并加载场景。
- `entities()` / `entity()` / `entity_keys()` / `entity_fields()` / `field_keys()`：实体与字段访问。
- `writable_columns()` / `search_columns()` / `entity_order()` / `entity_columns()` / `entity_filter_field()`：CRUD 与列表所需元数据。
- `scene_settings()` / `scene_seeds()` / `scene_acts()` / `scene_templates()`：设置默认值、种子数据、幕-阶段树、模板。
- `entity_system_columns()`：引擎管理的系统列（如 `materials.path` 唯一索引）。
- `ensure_entity_table()` / `ensure_scene_entities()`：**按场景配置建表/补列**（幂等，改 JSON 即改 schema，不丢行）。
- `validate_scene()`：字段类型、key、select 选项等校验。

### `engine/entities.py`

- 通用实体 CRUD 与排序（配置驱动，无业务特判）。
- `list_table()`：列表与关键词查询，支持受限 `limit`。
- `create_row()` / `update_row()` / `delete_row()`：通用新增/更新/删除；`delete_row` 派发 `after_delete` 钩子。
- `move_row()` / `resequence()`：`ordered` 实体的上移/下移/移动到指定位置与序号重排。
- `entity_options()` / `app_options()`：`optionSource` 下拉选项解析与聚合。
- `backup_db()`：复制 SQLite 文件到 `data/backups/`。

### `engine/hooks.py`

- 场景钩子加载器：按约定动态加载 `scenes/<id>/hooks.py`。
- `call(name, *args, **kwargs)`：调用指定钩子；场景未提供时返回 `None`（引擎回退到默认行为）。

### `engine/sop.py`

- SOP 阶段引擎：幕 → 阶段 → 检查项树 + 条件求值 + 必停点。
- `list_acts()`：返回幕-阶段树，附带每个阶段的 `state`（pending/active/done）、`enterOk`/`exitOk` 与未满足原因。
- `evaluate(cond)`：声明式条件求值器，支持 `all`/`any`/`not` 组合子与原子谓词（`fieldEmpty`/`fieldEq`/`fieldIn`/`count`/`checklist`/`stageDone`）。
- `advance_stage()` / `start_stage()` / `reset_stage()`：阶段流转，**服务端强校验退出/进入条件**。
- `_stage_states()` / `_set_stage_state()`：阶段状态读写（落在 `stage_state` 表）。

### `engine/checklist.py`

- 通用清单引擎：检查项可挂载到任意 owner。
  - `owner_type = "global"` → 工作台全局清单（`owner_id` = 清单 id）。
  - `owner_type = "stage"` → 阶段清单（`owner_id` = 阶段 id）。
  - `owner_type = <实体 key>` → 实体实例清单（`owner_id` = 行 id）。
- 清单模板在 `scene.json` 的 `checklists` 块；首次访问时物化为 `checklist_items` 行。
- `ensure_checklist()` / `ensure_owner_checklists()` / `list_checklist()` / `global_progress()` / `set_done()` / `add_item()` / `delete_item()`。

### `engine/materials.py`

- 通用文件索引引擎：扫描场景资料目录，把文件索引进 `materials` 实体，支持上传/浏览/删除。
- 分类规则（归类/阶段/关联导师）由 `classify_file` 场景钩子提供，引擎回退到最小默认。
- `scan_materials()` / `sanitize_material_paths()` / `purge_ignored_material_rows()`：扫描、清理越界路径与误收录依赖文件。
- `resource_directory()`：资源页逐层目录接口（普通浏览只返回当前层，搜索最多 300 条）。
- `get_material()` / `material_actions()` / `resource_groups()`：单条读取、预览操作、分组。
- `parse_upload()` / `upload_material()`：用 `email` 标准库解析 multipart 上传（替代已移除的 `cgi`），保存到 `保研准备/网页添加/`。
- `delete_material_file()`：删除真实文件并把索引标为缺失。

### `engine/settings.py`

- `default_settings()`：默认设置来自场景 `scene.json` 的 `settings` 块，不再硬编码。
- `read_settings()` / `update_settings()`：读取/校验并保存设置与学校配色。
- `save_avatar()` / `avatar_response()` / `avatar_path()`：头像保存、响应与路径。

### `engine/server.py`

- `send_json()`：发送 UTF-8 JSON 响应。
- `read_body()`：读取 JSON 请求体。
- `Handler`：HTTP 请求处理类。
  - `do_GET()`：`summary`/`contact-workspace`（走场景钩子）、`sop`、`checklist`、`options`、`scene`、`settings`、`dataroot`、通用列表、文件预览和静态文件。
  - `do_POST()`：迁移/回滚、扫描、上传、备份、头像、SOP 阶段流转、排序和通用新增。
  - `do_PATCH()`：设置、清单勾选、通用记录更新。
  - `do_DELETE()`：真实文件、清单项、通用记录删除。
- `_hook_or_400()`：调用场景钩子，场景未提供时返回 400。
- `main()` / `create_server()`：启动摘要、端口回退、后台同步、多线程服务。
- `background_material_sync()`：后台扫描资料并输出同步摘要。

### `engine/utils.py`

- `now_text()` / `rows_to_dicts()` / `relative_text()` / `folder_level()`：通用工具。
- `is_safe_path()`：限制路径位于代码根内（静态文件）。
- `is_safe_data_path()`：限制路径位于数据根内（材料/头像）。

## 4. 场景包 `scenes/`

### `scenes/__init__.py` / `scenes/tuimian/__init__.py`

- 场景包标识。

### `scenes/tuimian/scene.json`

- 推免场景的声明式配置：`settings`（品牌/主题默认值）、`entities`（五个实体字段 + 系统列 + 排序/搜索/筛选）、`seeds`（默认待办与面试题）、`checklists`（面试三清单）、`acts`（推免面试 SOP 幕-阶段树）。
- 加新场景 = 新建 `scenes/<id>/` 目录并写 `scene.json`，不改引擎。

### `scenes/tuimian/hooks.py`

- 推免场景的业务钩子，承载所有推免特有逻辑：
  - `classify_file()` / `infer_related_professor()` / `clean_professor_name()`：文件分类与导师关联。
  - `contact_workspace()`：套磁页聚合（导师合并、套磁信/论文分组、未归类资源）。
  - `summary()`：总览统计（数量、比例、状态分布、近期内容）。
  - `resource_groups()` / `material_actions()`：分组与预览操作。
  - `after_scan()` / `after_delete()` / `bootstrap()`：扫描后补建导师、删除级联、启动归一化。

## 5. 前端 `web/`

### `web/index.html`

- 单页应用 HTML 壳：顶栏（品牌 + 搜索 + 操作）、横向导航、Toast、主内容容器、通用编辑弹窗、文件弹窗和设置弹窗。
- 设置项（品牌、头像、首页文字、主题）和脚本/样式入口都在这里。

### `web/style.css`

- 全站样式和主题变量。
- 文件开头 `:root`：默认“青野暖阳”配色（青绿 + 琥珀）；后续 `body[data-theme=...]`：其他可选主题。
- 主要样式区：顶栏/横向导航、面板/表格、院校列表、徽章/按钮、套磁表格与学校配色、逐层资源浏览、文件图标、总览数据卡与饼图、SOP 阶段看板、弹窗和响应式布局。

### `web/app.js`

- 兼容入口，仅导入 `web/js/main.js`。

## 6. 前端核心模块 `web/js/`

### `web/js/main.js`

- 前端总入口和页面路由。
- `render()`：根据 `state.page` 调用对应页面渲染器（dashboard / sop / contact / resources / 通用 table）。
- `bindCommonActions()`：统一绑定跳转、打开文件/文件夹、删除和资料编辑。
- `scanMaterials()` / `backupData()`：触发资料扫描与数据库备份。
- 文件末尾绑定侧栏按钮、搜索防抖和全局自定义事件，加载设置并首次渲染。

### `web/js/api.js`

- `api()`：JSON Fetch 封装，统一响应解析与错误处理。
- `uploadForm()`：multipart 表单上传封装。

### `web/js/state.js`

- `state`：当前页面、搜索词、缓存数据、资源路径、选项、设置和场景等共享状态。
- `pages`：侧栏七个页面的 ID、中文标题和图标文字（含「面试 SOP」）。

### `web/js/scene.js`

- `ensureScene()`：请求 `/api/scene` 并缓存到 `state.scene`。
- `entity(page)`：按页面取对应实体配置（字段、列、选项）。

### `web/js/status-colors.js`

- `STATUS_COLORS`：院校、导师、待办等状态的固定语义配色表。
- `statusColor()` / `statusStyle()`：状态颜色解析与徽章 CSS 变量生成。

### `web/js/ui.js`

- 通用界面组件和弹窗逻辑：`toast`、`loadSettings`/`applySettings`、`renderNav`、`renderBadge`、`openEditor`/`renderField`/`collectForm`、`openSettings` 等。

### `web/js/files.js`

- 文件图标、文件列表/单条 UI、打开文件/目录、删除文件。

### `web/js/utils.js`

- `$()`、`escapeHtml()`、`fileSize()`、`percent()`、`shortText()`。

## 7. 页面模块 `web/js/pages/`

### `web/js/pages/dashboard.js`

- `renderDashboard()`：请求 `/api/summary`，渲染指标卡、文件搜索、院校/套磁状态饼图和首页文字。

### `web/js/pages/sop.js`

- `renderSop()`：请求 `/api/sop`，渲染面试 SOP 阶段看板（阶段卡片、进入/退出条件、检查清单、开始/完成/重置按钮）。
- `loadChecklist()` / `bindChecklistItems()`：加载并绑定各阶段清单勾选。
- `bindSopActions()` / `callSop()`：阶段开始/推进/重置操作。

### `web/js/pages/contact.js`

- `renderContact()`：请求 `/api/contact-workspace`，应用学校/状态/关键词筛选并渲染套磁表格。
- 学校配色、筛选器、导师行渲染、未归类提示、导师写操作等。

### `web/js/pages/resources.js`

- `renderResources()`：请求 `/api/resources`，渲染面包屑、子文件夹与当前层文件，或受限搜索结果。
- `uploadFile()`：上传文件并触发刷新。

### `web/js/pages/table.js`

- `renderTablePage()`：通用列表页面入口（院校/待办/面试题等）。
- `renderPrograms()` / `renderTable()` / `formatCell()`：院校紧凑列表与普通表格。
- `bindTableActions()` / `bindProgramFilters()`：新增/编辑/删除/移动/筛选事件。

## 8. 非源码目录与文件

### `data/`

- `app.db`：SQLite 运行数据库，包含实体索引、待办、面试题、清单勾选、阶段状态和设置。
- `backups/`：通过“备份数据”生成的数据库副本。
- `avatar.*`：当前上传头像。
- `state/`：阶段进度/决策日志（JSON，预留）。

### `保研准备/`

- 用户实际资料库，是资料扫描和资源页浏览根目录。
- 本目录内容属于个人资料，不是系统源码；删除资源页文件会删除这里的真实文件。

### `处理文件/`

- 文档处理工作区。

### `imgs/`

- README 使用的页面截图。

### `docs/`

- 项目章程等对外文档。

## 9. 常见修改定位

| 想修改的功能 | 首要文件 | 同步检查 |
| --- | --- | --- |
| 默认配色或主题 | `web/style.css` | `web/index.html` 主题选项 |
| 状态名称/统计口径 | `scenes/tuimian/hooks.py` | `scenes/tuimian/scene.json`、`web/js/status-colors.js` |
| 状态徽章颜色 | `web/js/status-colors.js` | `web/js/ui.js`、页面是否使用 `renderBadge()` |
| 实体字段/列/排序 | `scenes/tuimian/scene.json` | `engine/scene.py`（表结构自动跟随） |
| 业务枚举与分类规则 | `scenes/tuimian/hooks.py` | `scenes/tuimian/scene.json` |
| SOP 阶段/清单/必停点 | `scenes/tuimian/scene.json` | `engine/sop.py`、`engine/checklist.py` |
| 资源扫描规则 | `engine/materials.py` | `scenes/tuimian/hooks.py`、`engine/server.py` 后台同步日志 |
| 总览指标 | `scenes/tuimian/hooks.py` | `web/js/pages/dashboard.js` |
| API 路由或日志 | `engine/server.py` | `web/js/api.js` |
| 设置字段 | `web/index.html`、`web/js/ui.js` | `scenes/tuimian/scene.json`、`engine/settings.py` |
| 数据库引擎表 | `engine/db.py` | `engine/scene.py`、`engine/bootstrap.py` |
