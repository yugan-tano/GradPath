// 界面文案国际化：中文 / English。数据（院校、导师、面试题等用户内容）不翻译。

const STORAGE_KEY = "gradpath.lang";

let lang = "zh";

const DICT = {
  // 导航与顶栏
  "nav.dashboard": { zh: "总览", en: "Overview" },
  "nav.sop": { zh: "面试 SOP", en: "Interview SOP" },
  "nav.contact": { zh: "套磁", en: "Contact" },
  "nav.resources": { zh: "资源", en: "Resources" },
  "nav.programs": { zh: "院校", en: "Programs" },
  "nav.tasks": { zh: "待办", en: "Tasks" },
  "nav.questions": { zh: "面试", en: "Interview" },
  "nav.scan": { zh: "扫描材料", en: "Scan files" },
  "nav.backup": { zh: "备份数据", en: "Backup data" },
  "nav.settings": { zh: "设置", en: "Settings" },
  "scene.switch": { zh: "切换场景", en: "Switch scene" },
  "scene.switched": { zh: "场景已切换", en: "Scene switched" },
  "scene.switchFail": { zh: "场景切换失败", en: "Failed to switch scene" },
  "search.all": { zh: "搜索全部文件", en: "Search all files" },
  "search.in": { zh: "搜索{title}", en: "Search {title}" },

  // 通用
  "common.save": { zh: "保存", en: "Save" },
  "common.cancel": { zh: "取消", en: "Cancel" },
  "common.edit": { zh: "编辑", en: "Edit" },
  "common.add": { zh: "新增", en: "Add" },
  "common.delete": { zh: "删除", en: "Delete" },
  "common.actions": { zh: "操作", en: "Actions" },
  "common.empty": { zh: "暂无记录。", en: "No records yet." },
  "common.notSet": { zh: "未填写", en: "Not set" },
  "common.toFill": { zh: "待补充", en: "To fill" },
  "common.close": { zh: "关闭", en: "Close" },
  "common.done": { zh: "完成", en: "Done" },
  "common.preview": { zh: "预览", en: "Preview" },
  "common.open": { zh: "打开", en: "Open" },
  "common.view": { zh: "查看", en: "View" },
  "common.files": { zh: "文件", en: "Files" },
  "common.sync": { zh: "同步文件", en: "Sync files" },
  "common.exportCsv": { zh: "导出 CSV", en: "Export CSV" },
  "common.exportMd": { zh: "导出 Markdown", en: "Export MD" },
  "common.exportReport": { zh: "导出报表", en: "Export report" },
  "title.suffix": { zh: "工作台", en: "Workspace" },

  // 总览
  "dash.eyebrow": { zh: "GradPath · 申请进度", en: "GradPath · Application progress" },
  "dash.overview": { zh: "推免进度总览", en: "Application overview" },
  "dash.metric.campInterested": { zh: "关注院校", en: "Programs of interest" },
  "dash.metric.camp": { zh: "入营 / 报名", en: "Admitted / Applied" },
  "dash.metric.campExcellent": { zh: "优营 / 通过", en: "Excellent / Passed" },
  "dash.metric.reply": { zh: "套磁回复 / 发送", en: "Replies / Sent" },
  "dash.metric.tasks": { zh: "待办", en: "Open tasks" },
  "dash.searchTitle": { zh: "全局文件搜索", en: "Global file search" },
  "dash.searchCount": { zh: "{n} 个结果", en: "{n} results" },
  "dash.pie.program": { zh: "院校状态占比", en: "Program status" },
  "dash.pie.professor": { zh: "套磁状态占比", en: "Contact status" },
  "dash.managePrograms": { zh: "管理院校", en: "Manage programs" },
  "dash.gotoContact": { zh: "进入套磁", en: "Go to contact" },
  "dash.noData": { zh: "暂无数据", en: "No data" },

  // SOP
  "sop.empty": { zh: "当前场景未配置 SOP 流程。", en: "No SOP is configured for this scene." },
  "sop.loading": { zh: "载入中…", en: "Loading…" },
  "sop.checklist": { zh: "检查清单", en: "Checklist" },
  "sop.loadFail": { zh: "清单加载失败：{msg}", en: "Failed to load checklist: {msg}" },
  "sop.enterOk": { zh: "进入条件：已满足", en: "Enter condition: met" },
  "sop.enterNot": { zh: "进入条件：未满足", en: "Enter condition: unmet" },
  "sop.noEnter": { zh: "无进入条件", en: "No enter condition" },
  "sop.exitOk": { zh: "退出条件：已满足", en: "Exit condition: met" },
  "sop.exitNot": { zh: "退出条件：未满足", en: "Exit condition: unmet" },
  "sop.start": { zh: "开始", en: "Start" },
  "sop.finish": { zh: "完成本阶段", en: "Complete stage" },
  "sop.reset": { zh: "重置", en: "Reset" },
  "sop.status.pending": { zh: "未开始", en: "Not started" },
  "sop.status.active": { zh: "进行中", en: "In progress" },
  "sop.status.done": { zh: "已完成", en: "Completed" },
  "sop.updated": { zh: "已更新阶段状态", en: "Stage updated" },
  "sop.failed": { zh: "操作失败", en: "Operation failed" },

  // 套磁
  "contact.title": { zh: "导师套磁", en: "Professors" },
  "contact.schoolColor": { zh: "学校配色", en: "School colors" },
  "contact.addProf": { zh: "新增导师", en: "Add professor" },
  "contact.priority": { zh: "优先级", en: "Priority" },
  "contact.professor": { zh: "导师", en: "Professor" },
  "contact.school": { zh: "学校", en: "School" },
  "contact.college": { zh: "学院/组", en: "College/Group" },
  "contact.direction": { zh: "方向", en: "Direction" },
  "contact.status": { zh: "状态", en: "Status" },
  "contact.files": { zh: "文件", en: "Files" },
  "contact.letter": { zh: "套磁信", en: "Email" },
  "contact.related": { zh: "相关文件", en: "Related files" },
  "contact.archive": { zh: "归档", en: "Archive" },
  "contact.create": { zh: "建档", en: "Create" },
  "contact.unassigned": { zh: "未归类资源", en: "Unassigned resources" },
  "contact.unassignedHint": { zh: "{n} 个文件待确认归属", en: "{n} files awaiting assignment" },
  "contact.schoolCount": { zh: "{n} 所学校", en: "{n} schools" },
  "contact.hexFormat": { zh: "颜色格式：#RRGGBB", en: "Format: #RRGGBB" },
  "contact.official": { zh: "官方色", en: "Official" },
  "contact.auto": { zh: "自动", en: "Auto" },
  "contact.officialPreset": { zh: "官方预设色", en: "official preset color" },
  "contact.autoColor": { zh: "自动配色", en: "auto color" },
  "contact.colorHint": { zh: "已按学校官方视觉规范预设，可使用 Hex 颜色覆盖。", en: "Preset to official school visual standards; override with a hex color." },
  "contact.restoreOfficial": { zh: "恢复学校官方预设色", en: "Restore official preset" },
  "contact.restoreAuto": { zh: "恢复自动配色", en: "Restore auto color" },
  "contact.emptySchool": { zh: "为导师填写学校后，即可在这里设置配色。", en: "Add a school to professors to customize colors here." },
  "contact.allSchool": { zh: "全部学校", en: "All schools" },
  "contact.allStatus": { zh: "全部状态", en: "All statuses" },
  "contact.profCount": { zh: "{visible} / {total} 位导师", en: "{visible} / {total} professors" },
  "contact.toast.hex": { zh: "请输入有效的 Hex 颜色，例如 #5B7FA3", en: "Enter a valid hex color, e.g. #5B7FA3" },
  "contact.toast.saved": { zh: "已保存 {school} 的配色 {color}", en: "Saved color {color} for {school}" },
  "contact.toast.restored": { zh: "已恢复 {school} 的{kind}", en: "Restored {kind} for {school}" },
  "contact.toast.saveFail": { zh: "学校配色保存失败", en: "Failed to save school color" },
  "contact.toast.created": { zh: "已建立导师记录", en: "Professor record created" },
  "contact.archiveConfirm": { zh: "确定归档这位导师吗？归档后将从套磁页隐藏，可在数据库中保留记录。", en: "Archive this professor? They will be hidden from the contact page but kept in the database." },
  "contact.toast.archived": { zh: "已归档导师", en: "Professor archived" },
  "contact.deleteConfirm": { zh: "确定删除导师记录吗？\n\n{name}\n\n这不会删除本地文件，但会清空这些文件上的导师关联。", en: "Delete this professor record?\n\n{name}\n\nLocal files won't be deleted, but their professor links will be cleared." },
  "contact.toast.deleted": { zh: "已删除导师记录", en: "Professor record deleted" },
  "contact.autoNote": { zh: "由套磁信文件名自动识别：{name}", en: "Auto-detected from email filename: {name}" },
  "contact.paperTitle": { zh: "导师论文", en: "Professor papers" },
  "contact.moveToProf": { zh: "归到导师...", en: "Assign to professor..." },
  "contact.removeContact": { zh: "移出套磁", en: "Remove from contact" },
  "contact.categorize": { zh: "归类", en: "Categorize" },
  "contact.toast.categorized": { zh: "已归类到：{name}", en: "Assigned to: {name}" },
  "contact.toast.unassigned": { zh: "已从未归类套磁资源移出", en: "Removed from unassigned resources" },
  "contact.noFiles": { zh: "暂无相关文件。", en: "No related files." },

  // 资源
  "res.title": { zh: "资源浏览", en: "Resource browser" },
  "res.searching": { zh: "搜索“{q}”", en: "Searching “{q}”" },
  "res.lazy": { zh: "按需加载当前目录，进入文件夹后才读取下一级", en: "Loads the current directory on demand" },
  "res.addFile": { zh: "添加文件", en: "Add file" },
  "res.childCount": { zh: "{n} 个直接子项", en: "{n} direct children" },
  "res.openLocal": { zh: "本机打开", en: "Open locally" },
  "res.openCurrent": { zh: "打开当前文件夹", en: "Open current folder" },
  "res.currentFiles": { zh: "当前层文件", en: "Files in this folder" },
  "res.empty": { zh: "当前文件夹为空。", en: "This folder is empty." },
  "res.found": { zh: "找到 {n} 个文件", en: "Found {n} files" },
  "res.truncated": { zh: "，仅显示前 200 个", en: ", showing first 200" },
  "res.backToDir": { zh: "返回目录", en: "Back to directory" },
  "res.added": { zh: "已添加：{name}", en: "Added: {name}" },

  // 表格
  "table.records": { zh: "{n} 条记录", en: "{n} records" },
  "table.recordsFiltered": { zh: "{visible} / {total} 条记录", en: "{visible} / {total} records" },
  "table.all": { zh: "全部状态", en: "All" },
  "table.deleteConfirm": { zh: "确定删除这条记录吗？本地文件不会被删除。", en: "Delete this record? Local files won't be deleted." },
  "table.deleted": { zh: "已删除记录", en: "Record deleted" },
  "table.relatedFiles": { zh: "{name}的相关文件", en: "Files related to {name}" },

  // 文件
  "files.empty": { zh: "暂无文件", en: "No files" },
  "files.resource": { zh: "资料", en: "resource" },
  "files.delete": { zh: "删除文件", en: "Delete file" },
  "files.opened": { zh: "已调用本机默认程序打开文件", en: "Opened with default app" },
  "files.folderOpened": { zh: "已打开文件夹", en: "Folder opened" },
  "files.deleteConfirm": { zh: "确定删除本地文件吗？\n\n{name}\n\n此操作会直接删除文件。", en: "Delete this local file?\n\n{name}\n\nThis permanently deletes the file." },
  "files.deleted": { zh: "已删除本地文件", en: "Local file deleted" },

  // 编辑器
  "editor.editTitle": { zh: "编辑{label}", en: "Edit {label}" },
  "editor.addTitle": { zh: "新增{label}", en: "Add {label}" },
  "editor.required": { zh: "请填写：{label}", en: "Please fill in: {label}" },
  "editor.saved": { zh: "已保存", en: "Saved" },
  "editor.moveTop": { zh: "移至顶端", en: "Move to top" },
  "editor.moveBottom": { zh: "移至底端", en: "Move to bottom" },
  "editor.movedTop": { zh: "已移至顶端", en: "Moved to top" },
  "editor.movedBottom": { zh: "已移至底端", en: "Moved to bottom" },
  "editor.notSet": { zh: "未设置", en: "Not set" },
  "editor.kvAdd": { zh: "添加一项", en: "Add item" },
  "editor.kvKey": { zh: "名称", en: "Key" },
  "editor.kvValue": { zh: "值", en: "Value" },

  // 关联链接
  "links.add": { zh: "添加链接", en: "Add link" },
  "links.selectType": { zh: "选择类型", en: "Choose type" },
  "links.selectRecord": { zh: "选择记录", en: "Choose record" },
  "links.labelPlaceholder": { zh: "备注（可选）", en: "Note (optional)" },

  // 聚合页
  "board.eyebrow": { zh: "GradPath · 关联聚合", en: "GradPath · Linked board" },
  "board.total": { zh: "关联总数", en: "Total links" },
  "board.noLinks": { zh: "暂无关联，可在记录编辑中添加链接。", en: "No links yet; add links when editing a record." },
  "board.noRecords": { zh: "暂无记录。", en: "No records yet." },

  // 绩点统计
  "stats.eyebrow": { zh: "GradPath · 学习统计", en: "GradPath · Study stats" },
  "stats.title": { zh: "绩点核算与选课统计", en: "GPA & credit statistics" },
  "stats.semesterTable": { zh: "时间阶段追踪表", en: "Time-stage tracking" },
  "stats.gradeMap": { zh: "绩点换算对照表", en: "Grade point conversion" },
  "stats.gradeMapHint": { zh: "成绩 → 4.0 绩点", en: "Score → 4.0 GPA" },
  "stats.semester": { zh: "学期", en: "Semester" },
  "stats.courses": { zh: "课程数", en: "Courses" },
  "stats.credits": { zh: "学分", en: "Credits" },
  "stats.graded": { zh: "已出成绩", en: "Graded" },
  "stats.avgScore": { zh: "加权均分", en: "Weighted avg" },
  "stats.gpa": { zh: "绩点", en: "GPA" },
  "stats.noCourses": { zh: "暂无课程记录，请先在「课程」页添加课程与成绩。", en: "No courses yet. Add courses and scores on the Courses page first." },

  // 设置
  "settings.title": { zh: "设置", en: "Settings" },
  "settings.name": { zh: "名字", en: "Name" },
  "settings.workspace": { zh: "工作台名", en: "Workspace name" },
  "settings.avatarMode": { zh: "头像方式", en: "Avatar mode" },
  "settings.text": { zh: "文字", en: "Text" },
  "settings.upload": { zh: "上传", en: "Upload" },
  "settings.avatarPreview": { zh: "头像预览", en: "Avatar preview" },
  "settings.avatarText": { zh: "头像文字", en: "Avatar text" },
  "settings.uploadAvatar": { zh: "上传头像", en: "Upload avatar" },
  "settings.motto": { zh: "首页横幅文字", en: "Homepage banner text" },
  "settings.theme": { zh: "整体风格", en: "Theme" },
  "settings.dataRoot": { zh: "数据目录", en: "Data directory" },
  "settings.current": { zh: "当前位置", en: "Current location" },
  "settings.migrateTo": { zh: "迁移到新位置", en: "Migrate to new location" },
  "settings.migrate": { zh: "迁移", en: "Migrate" },
  "settings.migrateHint": { zh: "迁移会复制全部数据并校验一致性，旧目录保留作为回滚副本。", en: "Migration copies all data and verifies consistency; the old directory is kept as a rollback copy." },
  "settings.rollback": { zh: "回滚到上一个目录", en: "Roll back to previous directory" },
  "settings.disclaimer": { zh: "本网站为开源项目，仅供学习与交流使用，使用风险由用户自行承担。", en: "Open-source project for learning and exchange only; use at your own risk." },

  // 主题名
  "theme.default": { zh: "青野暖阳", en: "Teal & Amber" },
  "theme.morandi": { zh: "莫兰迪色系", en: "Morandi" },
  "theme.pink": { zh: "粉红泡沫", en: "Pink" },
  "theme.forest": { zh: "松林薄雾", en: "Forest" },
  "theme.paper": { zh: "暖纸书桌", en: "Paper" },
  "theme.aurora": { zh: "极光蓝紫", en: "Aurora" },
  "theme.matcha": { zh: "抹茶拿铁", en: "Matcha" },
  "theme.sunset": { zh: "落日珊瑚", en: "Sunset" },
  "theme.ink": { zh: "墨蓝银灰", en: "Ink" },
  "theme.ugly90s": { zh: "丑萌 90s", en: "90s Retro" },
  "theme.traffic": { zh: "红绿灯警告", en: "Traffic" },
  "theme.neonMud": { zh: "霓虹泥潭", en: "Neon Mud" },

  // 数据目录
  "root.readFail": { zh: "读取数据目录失败", en: "Failed to read data directory" },
  "root.enterPath": { zh: "请输入新的数据目录路径", en: "Enter a new data directory path" },
  "root.migrated": { zh: "迁移完成，数据目录已更新", en: "Migration complete, data directory updated" },
  "root.migrateFail": { zh: "迁移失败", en: "Migration failed" },
  "root.rollbackConfirm": { zh: "确定回滚到上一个数据目录吗？", en: "Roll back to the previous data directory?" },
  "root.rolledBack": { zh: "已回滚到上一个数据目录", en: "Rolled back to previous directory" },
  "root.rollbackFail": { zh: "回滚失败", en: "Rollback failed" },
  "root.history": { zh: "历史迁移记录（最近 5 条）：", en: "Migration history (last 5):" },

  // 主流程
  "main.syncDone": { zh: "同步完成：新增 {a}，更新 {b}，缺失 {c}", en: "Sync complete: {a} added, {b} updated, {c} missing" },
  "main.backupDone": { zh: "备份完成：{path}", en: "Backup complete: {path}" },
  "main.noRecord": { zh: "没有找到这条文件记录，请先同步文件", en: "Record not found; sync files first" },
  "main.settingsSaved": { zh: "设置已保存", en: "Settings saved" },

  // 网络
  "api.requestFail": { zh: "请求失败：{status}", en: "Request failed: {status}" },
  "api.uploadFail": { zh: "上传失败", en: "Upload failed" },

  // 外观切换
  "dark.toDark": { zh: "切换暗色模式", en: "Switch to dark mode" },
  "dark.toLight": { zh: "切换亮色模式", en: "Switch to light mode" },
  "lang.toEnglish": { zh: "切换到英文", en: "Switch to English" },
  "lang.toChinese": { zh: "切换到中文", en: "Switch to Chinese" },
};

// 实体 / 字段 / 列标题标签（来自 scene.json）的中英对照。
const LABELS = {
  文件: "Files",
  名称: "Name",
  归类: "Category",
  关联: "Links",
  关联导师: "Professor",
  关联院校: "Program",
  备注: "Note",
  置顶: "Pin",
  院校项目: "Programs",
  学校: "School",
  简称: "Abbreviation",
  学院: "College",
  专业: "Major",
  类型: "Type",
  方向: "Direction",
  阶段: "Stage",
  时间: "Date",
  状态: "Status",
  账号: "Account",
  密码: "Password",
  导师: "Professors",
  姓名: "Name",
  "学院/组": "College/Group",
  研究方向: "Research direction",
  邮箱: "Email",
  主页: "Homepage",
  待办: "Tasks",
  事项: "Item",
  范围: "Scope",
  截止: "Due",
  截止日期: "Due date",
  优先级: "Priority",
  面试题: "Questions",
  主题: "Topic",
  问题: "Question",
  答案要点: "Key points",
  标签: "Tag",
  课程: "Courses",
  考试: "Exams",
  笔记: "Notes",
  学期: "Semester",
  学分: "Credits",
  成绩: "Score",
  难度: "Difficulty",
  任课教师: "Instructor",
  "考试/作业": "Exam / Assignment",
  作业: "Assignment",
  项目: "Projects",
  论文: "Papers",
  实验: "Experiments",
  组会: "Meetings",
  实验次数: "Attempts",
  次数: "Count",
  参数调整: "Parameters",
  参数: "Parameters",
  变量: "Variables",
  政策: "Policies",
  英语: "English",
  申请: "Applications",
  标题: "Title",
  "期刊/会议": "Venue",
  提交: "Submitted",
  开始: "Start",
  结束: "End",
  开始日期: "Start date",
  结束日期: "End date",
  日期: "Date",
  结果: "Result",
  学校类型: "School type",
  政策类别: "Category",
  政策标题: "Policy",
  政策内容: "Content",
  关注点: "Attention",
  时间节点: "Deadline",
  考试类型: "Exam type",
  目标总分: "Target",
  当前总分: "Current",
  听力: "Listening",
  阅读: "Reading",
  写作: "Writing",
  口语: "Speaking",
  最近考试日期: "Test date",
  国家: "Country",
  目标院校: "Target school",
  相关导师: "Professor",
  资助形式: "Funding",
  语言要求: "Language requirement",
  截止时间: "Deadline",
  治安了解: "Safety",
};

export function currentLang() {
  return lang;
}

export function t(key, vars) {
  const entry = DICT[key];
  let text = entry ? entry[lang] ?? entry.zh ?? key : key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.replaceAll(`{${name}}`, value);
    }
  }
  return text;
}

// 翻译 scene.json 中的界面标签；未知标签原样返回。
export function label(text) {
  if (lang === "zh") return text;
  return LABELS[String(text)] || text;
}

// 场景内容（幕/阶段名、检查项）：优先使用 scene.json 中声明的英文，否则回退中文。
export function sceneText(zh, en) {
  if (lang === "en" && en) return en;
  return zh;
}

export function initI18n() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "en" || saved === "zh") lang = saved;
  applyStatic();
}

export function setLang(next) {
  lang = next;
  localStorage.setItem(STORAGE_KEY, next);
  applyStatic();
}

// 更新静态 HTML 上带 data-i18n / data-i18n-placeholder / data-i18n-title 的元素。
export function applyStatic() {
  document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });
}
