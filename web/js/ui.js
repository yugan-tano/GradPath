import { api, uploadForm } from "./api.js";
import { fileButtons, fileIcon, renderFileList } from "./files.js";
import { label, sceneText, t } from "./i18n.js";
import { ensureScene } from "./scene.js";
import { scenePages, state } from "./state.js";
import { $, escapeHtml, shortText } from "./utils.js";
import { statusStyle } from "./status-colors.js";

const BRAND_LOGO_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/></svg>`;

export function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.hidden = false;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => {
    el.hidden = true;
  }, 2800);
}

export async function loadSettings() {
  state.settings = await api("/api/settings");
  applySettings();
}

export function applySettings() {
  const settings = state.settings || {};
  const brandTitle = settings.brandTitle || "GradPath";
  const workspaceName = settings.workspaceName || "推免准备 · 本地工作台";
  $("#brandTitle").textContent = brandTitle;
  $("#workspaceName").textContent = workspaceName;
  document.title = `${brandTitle} ${t("title.suffix")}`;
  document.body.dataset.theme = settings.theme || "default";
  const mark = $("#brandMark");
  if (settings.avatarMode === "upload" && settings.avatarUrl) {
    mark.innerHTML = `<img src="${settings.avatarUrl}" alt="" />`;
  } else if (settings.avatarText) {
    mark.textContent = settings.avatarText.slice(0, 2);
  } else {
    mark.innerHTML = BRAND_LOGO_SVG;
  }
}

export function renderNav(setPage) {
  const nav = $("#nav");
  nav.innerHTML = scenePages()
    .map(
      (page) => `<button class="nav-btn ${state.page === page.id ? "active" : ""}" data-page="${page.id}">${escapeHtml(sceneText(page.title, page.titleEn))}</button>`,
    )
    .join("");
  nav.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => setPage(button.dataset.page)));
}

export function renderSceneSwitcher(switchHandler) {
  const menu = $("#sceneMenu");
  if (!menu) return;
  const active = state.activeSceneId;
  menu.innerHTML = state.scenes
    .map((scene) => {
      const isActive = scene.id === active;
      return `<button class="scene-option ${isActive ? "active" : ""}" data-scene="${escapeHtml(scene.id)}">
        <span class="scene-option-name">${escapeHtml(sceneText(scene.name, scene.nameEn))}</span>
        <span class="scene-option-desc">${escapeHtml(sceneText(scene.description, scene.descriptionEn))}</span>
      </button>`;
    })
    .join("");
  menu.querySelectorAll("[data-scene]").forEach((button) =>
    button.addEventListener("click", () => {
      if (button.dataset.scene !== active) switchHandler(button.dataset.scene);
      menu.hidden = true;
    }),
  );
}

export function applySceneName() {
  const btn = $("#sceneBtn");
  if (!btn) return;
  const scene = state.scenes.find((item) => item.id === state.activeSceneId);
  btn.textContent = scene ? sceneText(scene.name, scene.nameEn) : "GradPath";
}

export function renderBadge(value, extra = "") {
  return `<span class="badge ${extra}" style="${statusStyle(value)}">${escapeHtml(value || t("common.notSet"))}</span>`;
}

export function renderExportButtons(entityKey) {
  return `
    <button class="mini" data-export="${escapeHtml(entityKey)}" data-format="csv">${t("common.exportCsv")}</button>
    <button class="mini" data-export="${escapeHtml(entityKey)}" data-format="md">${t("common.exportMd")}</button>
  `;
}

export function bindExportButtons() {
  document.querySelectorAll("[data-export]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.export;
      const format = button.dataset.format;
      const a = document.createElement("a");
      a.href = `/api/export/${encodeURIComponent(key)}?format=${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    });
  });
}

export function renderSimpleList(rows, titleKey, subKey, metaKey) {
  if (!rows.length) return `<div class="empty">${t("common.empty")}</div>`;
  return `
    <div class="list compact-list">
      ${rows
        .slice(0, 8)
        .map((row) => `<div class="list-item"><strong>${escapeHtml(row[titleKey])}</strong><p>${escapeHtml(row[subKey] || t("common.notSet"))} · ${escapeHtml(row[metaKey] || t("common.toFill"))}</p></div>`)
        .join("")}
    </div>
  `;
}

export function openPapersDialog(title, rows, allowAssign = false, refreshContact = null) {
  $("#papersTitle").textContent = title;
  $("#papersList").innerHTML = rows.length
    ? `<div class="file-list">${rows
        .map(
          (row) => `
            <div class="file-item">
              ${fileIcon(row)}
              <div class="file-main"><strong>${escapeHtml(row.name)}</strong><span>${escapeHtml(row.relative_path)} · ${escapeHtml(row.resource_kind || t("files.resource"))}</span></div>
              <div class="actions">
                ${fileButtons(row)}
                ${allowAssign ? `${professorAssignSelect(row.id)}<button class="mini" data-remove-contact="${row.id}">${t("contact.removeContact")}</button>` : `<button class="mini" data-edit-material="${row.id}">${t("contact.categorize")}</button>`}
              </div>
            </div>
          `,
        )
        .join("")}</div>`
    : `<div class="empty">${t("contact.noFiles")}</div>`;
  bindAssignActions(refreshContact);
  $("#papersDialog").showModal();
}

function professorAssignSelect(id) {
  return `
    <select class="mini-select" data-assign-paper="${id}">
      <option value="">${t("contact.moveToProf")}</option>
      ${(state.contactData?.professors || []).map((prof) => `<option value="${escapeHtml(prof.name)}">${escapeHtml(prof.name)}</option>`).join("")}
    </select>
  `;
}

function bindAssignActions(refreshContact) {
  document.querySelectorAll("[data-assign-paper]").forEach((select) => {
    select.addEventListener("change", async () => {
      if (!select.value) return;
      await api(`/api/materials/${select.dataset.assignPaper}`, {
        method: "PATCH",
        body: JSON.stringify({ category: "套磁", stage: "套磁", related_professor: select.value }),
      });
      $("#papersDialog").close();
      toast(t("contact.toast.categorized", { name: select.value }));
      refreshContact?.();
    });
  });
  document.querySelectorAll("[data-remove-contact]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/api/materials/${button.dataset.removeContact}`, {
        method: "PATCH",
        body: JSON.stringify({ category: "参考", stage: "通用", related_professor: "" }),
      });
      $("#papersDialog").close();
      toast(t("contact.toast.unassigned"));
      refreshContact?.();
    });
  });
}

export async function ensureOptions() {
  if (!state.options) state.options = await api("/api/options");
  return state.options;
}

export async function openEditor(page, row = null, refresh) {
  const entity = (await ensureScene()).entities[page];
  const options = await ensureOptions();
  const dialog = $("#editor");
  $("#editorTitle").textContent = row ? t("editor.editTitle", { label: label(entity.label) }) : t("editor.addTitle", { label: label(entity.label) });
  $("#editorFields").innerHTML = entity.fields.map((field) => renderField(field, row, options)).join("");
  bindKeyValueEditors(row);
  await bindLinksEditors(page, row);
  renderEditorOrderActions(page, row, dialog, refresh);
  $("#saveBtn").onclick = async (event) => {
    event.preventDefault();
    const payload = collectForm(entity);
    if (page === "materials") normalizeMaterialPayload(payload);
    const missing = entity.fields.find((field) => field.required && field.type !== "links" && !String(payload[field.key] || "").trim());
    if (missing) return toast(t("editor.required", { label: label(missing.label) }));
    const path = row ? `${entity.endpoint}/${row.id}` : entity.endpoint;
    const method = row ? "PATCH" : "POST";
    const saved = await api(path, { method, body: JSON.stringify(payload) });
    const linksField = entity.fields.find((field) => field.type === "links");
    if (linksField) {
      const id = row ? row.id : saved.id;
      await api("/api/links", {
        method: "POST",
        body: JSON.stringify({ scene: state.activeSceneId, entity: page, id, links: collectLinks(linksField.key) }),
      });
    }
    dialog.close();
    toast(t("editor.saved"));
    refresh();
  };
  dialog.showModal();
}

async function renderEditorOrderActions(page, row, dialog, refresh) {
  const actions = $("#editorOrderActions");
  const entity = (await ensureScene()).entities[page];
  if (!row?.id || !entity.ordered) {
    actions.innerHTML = "";
    return;
  }
  actions.innerHTML = `
    <button type="button" class="secondary" data-editor-move="top">${t("editor.moveTop")}</button>
    <button type="button" class="secondary" data-editor-move="bottom">${t("editor.moveBottom")}</button>
  `;
  actions.querySelector('[data-editor-move="top"]').onclick = () => moveEditorRow(page, row.id, 1, dialog, refresh);
  actions.querySelector('[data-editor-move="bottom"]').onclick = () => moveEditorRow(page, row.id, 1000000, dialog, refresh);
}

async function moveEditorRow(page, id, targetPosition, dialog, refresh) {
  await api(`/api/${page}/${id}/move`, { method: "POST", body: JSON.stringify({ target_position: targetPosition }) });
  dialog.close();
  toast(targetPosition === 1 ? t("editor.movedTop") : t("editor.movedBottom"));
  refresh();
}

function renderField(field, row, options) {
  const value = row?.[field.key] ?? "";
  const type = field.type || "text";
  const full = field.full || type === "textarea" || type === "keyvalue" || type === "links" ? " full" : "";
  let control = "";
  if (type === "select" || type === "multiselect") {
    const optionList = field.optionSource ? options[field.optionSource] || [] : field.options || [];
    const values = field.allowEmpty ? ["", ...optionList] : [...optionList];
    if (value && !values.includes(String(value))) values.push(String(value));
    const multiple = type === "multiselect" ? " multiple" : "";
    control = `<select name="${field.key}"${multiple}>${values.map((option) => `<option value="${escapeHtml(option)}" ${String(value) === String(option) ? "selected" : ""}>${escapeHtml(option || t("editor.notSet"))}</option>`).join("")}</select>`;
  } else if (type === "textarea") {
    control = `<textarea name="${field.key}">${escapeHtml(value)}</textarea>`;
  } else if (type === "keyvalue") {
    control = `<div class="kv-editor" data-kv-name="${field.key}"><div class="kv-rows"></div><button type="button" class="mini kv-add">+ ${t("editor.kvAdd")}</button></div>`;
  } else if (type === "links") {
    control = `<div class="links-editor" data-links-name="${field.key}"><div class="link-rows"></div><button type="button" class="mini link-add">+ ${t("links.add")}</button></div>`;
  } else if (type === "checkbox") {
    control = `<input name="${field.key}" type="checkbox" ${value === "1" || value === 1 || value === true ? "checked" : ""} />`;
  } else if (type === "file") {
    control = `<input name="${field.key}" type="file" />`;
  } else {
    const inputType = type === "number" ? "number" : type === "date" ? "date" : type === "datetime" ? "datetime-local" : "text";
    control = `<input name="${field.key}" type="${inputType}" value="${escapeHtml(value)}" />`;
  }
  return `<label class="field${full}"><span>${label(field.label)}</span>${control}</label>`;
}

function bindKeyValueEditors(row) {
  document.querySelectorAll("[data-kv-name]").forEach((editor) => {
    const name = editor.dataset.kvName;
    let pairs = parseKeyValue(row?.[name]);
    if (!pairs.length) pairs = [{ k: "", v: "" }];
    const rowsEl = editor.querySelector(".kv-rows");
    const addBtn = editor.querySelector(".kv-add");
    const render = () => {
      rowsEl.innerHTML = pairs
        .map(
          (pair, index) => `
            <div class="kv-row">
              <input type="text" class="kv-key" placeholder="${t("editor.kvKey")}" value="${escapeHtml(pair.k)}" data-i="${index}" />
              <input type="text" class="kv-val" placeholder="${t("editor.kvValue")}" value="${escapeHtml(pair.v)}" data-i="${index}" />
              <button type="button" class="mini kv-del" data-i="${index}" title="${t("common.delete")}">×</button>
            </div>
          `,
        )
        .join("");
      rowsEl.querySelectorAll(".kv-key").forEach((input) => input.addEventListener("input", () => (pairs[Number(input.dataset.i)].k = input.value)));
      rowsEl.querySelectorAll(".kv-val").forEach((input) => input.addEventListener("input", () => (pairs[Number(input.dataset.i)].v = input.value)));
      rowsEl.querySelectorAll(".kv-del").forEach((button) =>
        button.addEventListener("click", () => {
          pairs.splice(Number(button.dataset.i), 1);
          if (!pairs.length) pairs = [{ k: "", v: "" }];
          render();
        }),
      );
    };
    addBtn.addEventListener("click", () => {
      pairs.push({ k: "", v: "" });
      render();
    });
    render();
  });
}

function parseKeyValue(raw) {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed
        .map((item) => ({ k: String(item?.k ?? item?.key ?? ""), v: String(item?.v ?? item?.value ?? "") }))
        .filter((item) => item.k || item.v);
    }
    if (parsed && typeof parsed === "object") {
      return Object.entries(parsed).map(([k, v]) => ({ k, v: String(v) }));
    }
  } catch {
    return [];
  }
  return [];
}

function splitTarget(value) {
  if (!value) return ["", ""];
  const idx = value.indexOf("/");
  return idx >= 0 ? [value.slice(0, idx), value.slice(idx + 1)] : ["", value];
}

function filterLinkTargets(allEntities, targets, activeScene) {
  if (!targets || !targets.length) return allEntities.filter((item) => item.scene === activeScene);
  const targetSet = new Set(targets);
  return allEntities.filter((item) => {
    if (targetSet.has(item.entity) && item.scene === activeScene) return true;
    return targetSet.has(`${item.scene}.${item.entity}`);
  });
}

function buildEntityOptions(options, activeScene) {
  const groups = {};
  for (const item of options) (groups[item.scene] ||= []).push(item);
  let html = `<option value="">${t("links.selectType")}</option>`;
  for (const [sceneId, items] of Object.entries(groups)) {
    const name = items[0]?.sceneName || sceneId;
    html += `<optgroup label="${escapeHtml(name)}">`;
    for (const item of items) html += `<option value="${escapeHtml(`${sceneId}/${item.entity}`)}">${escapeHtml(item.label)}</option>`;
    html += `</optgroup>`;
  }
  return html;
}

async function bindLinksEditors(entityKey, row) {
  const editors = document.querySelectorAll("[data-links-name]");
  if (!editors.length) return;
  const scene = state.activeSceneId;
  const allEntities = (await api("/api/links/entities")).items || [];
  let existing = [];
  if (row?.id) {
    const data = await api(`/api/links?scene=${encodeURIComponent(scene)}&entity=${encodeURIComponent(entityKey)}&id=${row.id}`);
    existing = data.items || [];
  }
  const recordCache = {};

  for (const editor of editors) {
    const fieldKey = editor.dataset.linksName;
    const entity = (state.scene?.entities || {})[entityKey] || {};
    const field = (entity.fields || []).find((f) => f.key === fieldKey);
    const options = filterLinkTargets(allEntities, field?.targets, scene);
    const entityOptionsHtml = buildEntityOptions(options, scene);

    let links = existing.map((link) => ({ scene: link.scene, entity: link.entity, id: link.rowId, label: link.label || "" }));
    if (!links.length) links = [{ scene: "", entity: "", id: null, label: "" }];

    const rowsEl = editor.querySelector(".link-rows");
    const addBtn = editor.querySelector(".link-add");

    const loadOptions = async (targetScene, targetEntity) => {
      const key = `${targetScene}/${targetEntity}`;
      if (!recordCache[key]) recordCache[key] = (async () => (await api(`/api/links/options?scene=${encodeURIComponent(targetScene)}&entity=${encodeURIComponent(targetEntity)}`)).items || [])();
      return recordCache[key];
    };

    const render = async () => {
      rowsEl.innerHTML = links
        .map(
          (link, index) => `
            <div class="link-row" data-i="${index}">
              <select class="link-entity">${entityOptionsHtml}</select>
              <select class="link-record" ${link.entity ? "" : "disabled"}></select>
              <input type="text" class="link-label" placeholder="${t("links.labelPlaceholder")}" value="${escapeHtml(link.label)}" />
              <button type="button" class="mini link-del" title="${t("common.delete")}">×</button>
            </div>
          `,
        )
        .join("");
      rowsEl.querySelectorAll(".link-row").forEach(async (rowEl) => {
        const index = Number(rowEl.dataset.i);
        const link = links[index];
        const entitySel = rowEl.querySelector(".link-entity");
        const recordSel = rowEl.querySelector(".link-record");
        entitySel.value = link.entity ? `${link.scene}/${link.entity}` : "";
        if (link.entity) {
          const items = await loadOptions(link.scene, link.entity);
          recordSel.innerHTML = `<option value="">${t("links.selectRecord")}</option>${items
            .map((item) => `<option value="${item.id}" ${String(link.id) === String(item.id) ? "selected" : ""}>${escapeHtml(item.name)}</option>`)
            .join("")}`;
          recordSel.value = String(link.id ?? "");
          recordSel.disabled = false;
        }
        entitySel.addEventListener("change", async () => {
          const [targetScene, targetEntity] = splitTarget(entitySel.value);
          link.scene = targetScene;
          link.entity = targetEntity;
          link.id = null;
          if (targetEntity) await loadOptions(targetScene, targetEntity);
          await render();
        });
        recordSel.addEventListener("change", () => {
          link.id = recordSel.value ? Number(recordSel.value) : null;
        });
        rowEl.querySelector(".link-label").addEventListener("input", (event) => {
          link.label = event.target.value;
        });
        rowEl.querySelector(".link-del").addEventListener("click", () => {
          links.splice(index, 1);
          if (!links.length) links = [{ scene: "", entity: "", id: null, label: "" }];
          render();
        });
      });
    };
    addBtn.addEventListener("click", () => {
      links.push({ scene: "", entity: "", id: null, label: "" });
      render();
    });
    await render();
  }
}

function collectLinks(fieldKey) {
  const editor = document.querySelector(`[data-links-name="${fieldKey}"]`);
  const links = [];
  editor?.querySelectorAll(".link-row").forEach((rowEl) => {
    const entitySel = rowEl.querySelector(".link-entity");
    const [scene, entity] = splitTarget(entitySel?.value || "");
    const id = rowEl.querySelector(".link-record")?.value;
    const label = rowEl.querySelector(".link-label")?.value.trim() || "";
    if (entity && id) links.push({ scene: scene || state.activeSceneId, entity, id: Number(id), label });
  });
  return links;
}

function collectForm(entity) {
  const payload = {};
  entity.fields.forEach((field) => {
    if (field.type === "links") return;
    if (field.type === "keyvalue") {
      const editor = document.querySelector(`[data-kv-name="${field.key}"]`);
      const pairs = [];
      editor?.querySelectorAll(".kv-row").forEach((rowEl) => {
        const k = rowEl.querySelector(".kv-key")?.value.trim() ?? "";
        const v = rowEl.querySelector(".kv-val")?.value.trim() ?? "";
        if (k || v) pairs.push({ k, v });
      });
      payload[field.key] = JSON.stringify(pairs);
      return;
    }
    const el = document.querySelector(`[name="${field.key}"]`);
    if (!el) {
      payload[field.key] = "";
      return;
    }
    if (field.type === "checkbox") {
      payload[field.key] = el.checked ? "1" : "0";
    } else {
      payload[field.key] = el.value ?? "";
    }
  });
  return payload;
}

function normalizeMaterialPayload(payload) {
  const stageMap = { 基本材料: "通用", 套磁: "套磁", 院校: "夏令营", 项目: "科研", 面试: "面试", 参考: "通用" };
  payload.stage = stageMap[payload.category] || "通用";
  if (payload.category !== "套磁") payload.related_professor = "";
  if (payload.category !== "院校") payload.related_program = "";
  if (!payload.resource_kind) payload.resource_kind = payload.category || "参考";
}

export function openSettings(refresh) {
  const dialog = $("#settingsDialog");
  const settings = state.settings || {};
  dialog.querySelector('[name="brandTitle"]').value = settings.brandTitle || "";
  dialog.querySelector('[name="workspaceName"]').value = settings.workspaceName || "";
  dialog.querySelector('[name="avatarText"]').value = settings.avatarText || "";
  dialog.querySelector('[name="motto"]').value = settings.motto || "";
  dialog.querySelector('[name="theme"]').value = settings.theme || "default";
  dialog.querySelector(`[name="avatarMode"][value="${settings.avatarMode || "text"}"]`).checked = true;
  $("#avatarInput").value = "";
  updateAvatarPreview();
  dialog.querySelectorAll('[name="avatarMode"], [name="avatarText"]').forEach((el) => el.addEventListener("input", updateAvatarPreview));
  $("#avatarInput").onchange = updateAvatarPreview;
  $("#saveSettingsBtn").onclick = (event) => saveSettings(event, refresh);
  bindDataRoot(refresh);
  dialog.showModal();
}

async function bindDataRoot(refresh) {
  try {
    const info = await api("/api/dataroot");
    $("#dataRootPath").value = info.root;
    renderDataRootHistory(info.history);
  } catch (error) {
    toast(error.message || t("root.readFail"));
    return;
  }
  $("#migrateDataRootBtn").onclick = async () => {
    const path = $("#dataRootNewPath").value.trim();
    if (!path) return toast(t("root.enterPath"));
    try {
      const info = await api("/api/dataroot/migrate", { method: "POST", body: JSON.stringify({ path }) });
      toast(t("root.migrated"));
      $("#dataRootPath").value = info.root;
      $("#dataRootNewPath").value = "";
      renderDataRootHistory(info.history);
      refresh();
    } catch (error) {
      toast(error.message || t("root.migrateFail"));
    }
  };
  $("#rollbackDataRootBtn").onclick = async () => {
    if (!confirm(t("root.rollbackConfirm"))) return;
    try {
      const info = await api("/api/dataroot/rollback", { method: "POST" });
      toast(t("root.rolledBack"));
      $("#dataRootPath").value = info.root;
      renderDataRootHistory(info.history);
      refresh();
    } catch (error) {
      toast(error.message || t("root.rollbackFail"));
    }
  };
}

function renderDataRootHistory(history) {
  const el = $("#dataRootHistory");
  if (!history || !history.length) {
    el.innerHTML = "";
    return;
  }
  el.innerHTML = `<p class="field-caption">${t("root.history")}</p>` +
    history
      .slice(-5)
      .reverse()
      .map((entry) => `<p class="field-caption">${escapeHtml(entry.at || "")} · ${escapeHtml(entry.from || "")} → ${escapeHtml(entry.to || "")}</p>`)
      .join("");
}

function updateAvatarPreview() {
  const dialog = $("#settingsDialog");
  const mode = dialog.querySelector('[name="avatarMode"]:checked')?.value || "text";
  const preview = $("#avatarPreview");
  const file = $("#avatarInput").files[0];
  if (mode === "upload" && file) {
    preview.innerHTML = `<img src="${URL.createObjectURL(file)}" alt="" />`;
  } else if (mode === "upload" && state.settings?.avatarUrl) {
    preview.innerHTML = `<img src="${state.settings.avatarUrl}" alt="" />`;
  } else if (dialog.querySelector('[name="avatarText"]').value) {
    preview.textContent = dialog.querySelector('[name="avatarText"]').value.slice(0, 2);
  } else {
    preview.innerHTML = BRAND_LOGO_SVG;
  }
}

async function saveSettings(event, refresh) {
  event.preventDefault();
  const dialog = $("#settingsDialog");
  const payload = {
    brandTitle: dialog.querySelector('[name="brandTitle"]').value.trim(),
    workspaceName: dialog.querySelector('[name="workspaceName"]').value.trim(),
    avatarText: dialog.querySelector('[name="avatarText"]').value.trim(),
    avatarMode: dialog.querySelector('[name="avatarMode"]:checked')?.value || "text",
    motto: dialog.querySelector('[name="motto"]').value.trim(),
    theme: dialog.querySelector('[name="theme"]').value,
  };
  state.settings = await api("/api/settings", { method: "PATCH", body: JSON.stringify(payload) });
  const avatar = $("#avatarInput").files[0];
  if (payload.avatarMode === "upload" && avatar) {
    const form = new FormData();
    form.append("avatar", avatar);
    state.settings = await uploadForm("/api/settings/avatar", form);
  }
  applySettings();
  dialog.close();
  toast(t("main.settingsSaved"));
  refresh();
}

export function shortDirection(value) {
  return shortText(value, 10);
}
