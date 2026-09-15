import { api } from "../api.js";
import { label, t } from "../i18n.js";
import { ensureScene } from "../scene.js";
import { state } from "../state.js";
import { escapeHtml } from "../utils.js";
import { openEditor, openPapersDialog, renderBadge, renderExportButtons, toast } from "../ui.js";

const filterState = {};

export async function renderTablePage(page, bindCommonActions, refresh) {
  const entity = (await ensureScene()).entities[page];
  const data = await api(`${entity.endpoint}${state.q ? `?q=${encodeURIComponent(state.q)}` : ""}`);
  const allItems = data.items;
  const filterField = entity.filterField;
  const items = filterField && filterState[page] ? allItems.filter((row) => row[filterField] === filterState[page]) : allItems;
  state.rows[page] = items;
  document.querySelector("#app").innerHTML = `
    <section class="panel">
      <div class="panel-head"><h3>${label(entity.label)}</h3><div class="actions">${renderExportButtons(page)}<button class="primary" id="addBtn">${t("common.add")}</button></div></div>
      <div class="panel-body">
        ${filterField ? renderFilters(entity, allItems, items.length, page) : `<div class="toolbar"><p>${t("table.records", { n: items.length })}</p></div>`}
        ${renderTable(entity, page, items)}
      </div>
    </section>
  `;
  document.querySelector("#addBtn").addEventListener("click", () => openEditor(page, null, refresh));
  bindFilters(page, refresh);
  bindTableActions(entity, page, refresh);
  bindCommonActions();
}

function renderFilters(entity, rows, visibleCount, page) {
  const field = entity.filterField;
  const values = uniqueValues(rows.map((row) => row[field] || t("common.notSet")));
  const current = filterState[page] || "";
  return `
    <div class="toolbar program-filters">
      <p>${t("table.recordsFiltered", { visible: visibleCount, total: rows.length })}</p>
      <div class="filter-controls">
        <select class="mini-select" data-entity-filter="${page}">
          <option value="">${t("table.all")}</option>
          ${values.map((value) => `<option value="${escapeHtml(value)}" ${current === value ? "selected" : ""}>${escapeHtml(value)}</option>`).join("")}
        </select>
      </div>
    </div>
  `;
}

function renderTable(entity, page, rows) {
  if (!rows.length) return `<div class="empty">${t("common.empty")}</div>`;
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${entity.columns.map(([, colLabel]) => `<th>${label(colLabel)}</th>`).join("")}<th>${t("common.actions")}</th></tr></thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  ${entity.columns.map(([key]) => `<td>${formatCell(key, row, entity)}</td>`).join("")}
                  <td><div class="actions">${entityActions(entity, page, row)}<button class="mini" data-action="edit" data-page="${page}" data-id="${row.id}">${t("common.edit")}</button><button class="mini danger" data-action="delete" data-page="${page}" data-id="${row.id}">${t("common.delete")}</button></div></td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function entityActions(entity, page, row) {
  let html = "";
  if (entity.ordered) {
    html += `<button class="mini" data-move-row="${row.id}" data-dir="-1" data-page="${page}">↑</button><button class="mini" data-move-row="${row.id}" data-dir="1" data-page="${page}">↓</button>`;
  }
  if (entity.filesButton) {
    html += `<button class="mini" data-show-files="${escapeHtml(row[entity.filesButton.linkField])}" data-page="${page}">${label(entity.filesButton.label || "文件")}</button>`;
  }
  return html;
}

function uniqueValues(values) {
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
}

function formatCell(key, row, entity) {
  const value = row[key] ?? "";
  const field = (entity.fields || []).find((f) => f.key === key) || {};
  if (field.badge) return renderBadge(value, field.hotValues?.includes(value) ? "hot" : "");
  if (field.truncate || field.type === "textarea") return `<div class="truncate" title="${escapeHtml(value)}">${escapeHtml(value)}</div>`;
  return escapeHtml(value);
}

function bindTableActions(entity, page, refresh) {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.id;
      const targetPage = button.dataset.page;
      if (button.dataset.action === "edit") {
        const row = state.rows[targetPage].find((item) => String(item.id) === String(id));
        return openEditor(targetPage, row, refresh);
      }
      if (!confirm(t("table.deleteConfirm"))) return;
      const targetEntity = state.scene.entities[targetPage];
      await api(`${targetEntity.endpoint}/${id}`, { method: "DELETE" });
      toast(t("table.deleted"));
      refresh();
    });
  });
  document.querySelectorAll("[data-show-files]").forEach((button) => button.addEventListener("click", () => openEntityFiles(entity, button.dataset.showFiles)));
  document.querySelectorAll("[data-move-row]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/api/${button.dataset.page}/${button.dataset.moveRow}/move`, { method: "POST", body: JSON.stringify({ direction: Number(button.dataset.dir) }) });
      refresh();
    });
  });
}

function bindFilters(page, refresh) {
  document.querySelectorAll("[data-entity-filter]").forEach((select) => {
    select.addEventListener("change", () => {
      filterState[page] = select.value;
      refresh();
    });
  });
}

async function openEntityFiles(entity, linkValue) {
  const matchField = entity.filesButton.matchField;
  const data = await api("/api/materials");
  const rows = data.items.filter((item) => !item.missing && item[matchField] === linkValue);
  openPapersDialog(t("table.relatedFiles", { name: linkValue }), rows);
}
