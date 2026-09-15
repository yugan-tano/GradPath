import { api } from "../api.js";
import { label, sceneText, t } from "../i18n.js";
import { escapeHtml } from "../utils.js";

export async function renderAggregate(page, bindCommonActions) {
  const entity = page.entity;
  const data = await api(`/api/links/board?entity=${encodeURIComponent(entity)}`);
  const board = data.items || [];
  document.querySelector("#app").innerHTML = `
    <section class="screen-hero">
      <div>
        <p class="eyebrow">${t("board.eyebrow")}</p>
        <h3>${escapeHtml(sceneText(page.title, page.titleEn))}</h3>
      </div>
    </section>
    <section class="board-grid">
      ${board.length ? board.map(card).join("") : `<div class="empty">${t("board.noRecords")}</div>`}
    </section>
  `;
  bindCommonActions();
}

function card(item) {
  const groups = (item.groups || [])
    .map(
      (group) => `
        <div class="board-group">
          <span class="board-group-label">${escapeHtml(label(group.label))} · ${group.count}</span>
          <div class="board-group-items">
            ${group.items
              .map(
                (it) => `<span class="chip" title="${escapeHtml(it.label || "")}">${escapeHtml(it.name)}</span>`,
              )
              .join("")}
          </div>
        </div>
      `,
    )
    .join("");
  const status = item.row?.status ? `<span class="badge">${escapeHtml(item.row.status)}</span>` : "";
  return `
    <div class="board-card">
      <div class="board-card-head">
        <h4>${escapeHtml(item.name)}</h4>
        <span class="board-total" title="${t("board.total")}">${item.total}</span>
      </div>
      <div class="board-card-meta">${status}</div>
      ${groups || `<div class="empty small">${t("board.noLinks")}</div>`}
    </div>
  `;
}
