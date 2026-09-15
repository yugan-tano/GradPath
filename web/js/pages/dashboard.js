import { api } from "../api.js";
import { renderFileList } from "../files.js";
import { sceneText, t } from "../i18n.js";
import { state } from "../state.js";
import { escapeHtml } from "../utils.js";
import { statusColor } from "../status-colors.js";

export async function renderDashboard(bindCommonActions) {
  const data = await api("/api/summary");
  const fileResults = state.q ? await api(`/api/materials?q=${encodeURIComponent(state.q)}&limit=100`) : null;
  document.querySelector("#app").innerHTML = `
    <section class="screen-hero">
      <div>
        <p class="eyebrow">${t("dash.eyebrow")}</p>
        <h3>${t("dash.overview")}</h3>
      </div>
      <button class="secondary" data-export="report" data-format="md">${t("common.exportReport")}</button>
    </section>
    <section class="metric-grid">
      ${(data.metrics || []).map(metricCard).join("")}
    </section>
    ${
      state.q
        ? `<section class="panel search-results"><div class="panel-head"><h3>${t("dash.searchTitle")}</h3><span class="muted">${t("dash.searchCount", { n: fileResults.items.length })}</span></div><div class="panel-body">${renderFileList(fileResults.items.filter((item) => !item.missing))}</div></section>`
        : ""
    }
    <section class="dashboard-grid">
      ${(data.charts || []).map(chartPanel).join("")}
    </section>
    <section class="motto-banner"><p>${escapeHtml(state.settings?.motto || "")}</p></section>
  `;
  bindCommonActions();
}

function metricCard(metric) {
  const safeScore = Math.max(0, Math.min(100, Number(metric.score || 0)));
  return `
    <div class="metric-card" style="--score:${safeScore}">
      <span>${escapeHtml(sceneText(metric.label, metric.labelEn))}</span>
      <strong>${escapeHtml(metric.value)}</strong>
      <i aria-hidden="true"></i>
    </div>
  `;
}

function chartPanel(chart) {
  return `
    <div class="panel data-panel pie-panel">
      <div class="panel-head"><h3>${escapeHtml(sceneText(chart.title, chart.titleEn))}</h3>${chart.jump ? `<button class="secondary" data-jump="${escapeHtml(chart.jump)}">${escapeHtml(sceneText(chart.jumpLabel, chart.jumpLabelEn))}</button>` : ""}</div>
      <div class="panel-body">${pieChart(chart.rows || [])}</div>
    </div>
  `;
}

function pieChart(rows) {
  if (!rows.length) return `<div class="empty small">${t("dash.noData")}</div>`;
  const total = rows.reduce((sum, item) => sum + Number(item.count || 0), 0);
  let cursor = 0;
  const segments = rows
    .map((item, index) => {
      const value = Number(item.count || 0);
      const start = cursor;
      cursor += total ? (value / total) * 100 : 0;
      return `${statusColor(item.name, index)} ${start}% ${cursor}%`;
    })
    .join(", ");
  return `
    <div class="pie-layout">
      <div class="pie-visual" style="background: conic-gradient(${segments || "#e7eef2 0 100%"});">
        <span>${total}</span>
      </div>
      <div class="pie-legend">
        ${rows
        .map(
          (item, index) => `
            <div class="pie-row">
              <i style="background:${statusColor(item.name, index)}"></i>
              <span title="${escapeHtml(item.name || t("common.notSet"))}">${escapeHtml(item.name || t("common.notSet"))}</span>
              <b>${item.count}</b>
              <em>${total ? Math.round((Number(item.count || 0) / total) * 100) : 0}%</em>
            </div>
          `,
        )
        .join("")}
      </div>
    </div>
  `;
}
