import { api } from "../api.js";
import { t } from "../i18n.js";
import { escapeHtml } from "../utils.js";

export async function renderStats(bindCommonActions) {
  const data = await api("/api/stats");
  document.querySelector("#app").innerHTML = `
    <section class="screen-hero">
      <div>
        <p class="eyebrow">${t("stats.eyebrow")}</p>
        <h3>${t("stats.title")}</h3>
      </div>
    </section>
    <section class="metric-grid">
      ${(data.metrics || []).map(metricCard).join("")}
    </section>
    <section class="panel">
      <div class="panel-head"><h3>${t("stats.semesterTable")}</h3></div>
      <div class="panel-body">
        ${renderSemesterTable(data.semesters || [])}
      </div>
    </section>
    <section class="panel">
      <div class="panel-head"><h3>${t("stats.gradeMap")}</h3><span class="muted">${t("stats.gradeMapHint")}</span></div>
      <div class="panel-body">${renderGradeMap(data.gradeMap || [])}</div>
    </section>
  `;
  bindCommonActions();
}

function metricCard(metric) {
  const safeScore = Math.max(0, Math.min(100, Number(metric.score || 0)));
  return `
    <div class="metric-card" style="--score:${safeScore}">
      <span>${escapeHtml(metric.labelEn || metric.label)}</span>
      <strong>${escapeHtml(metric.value)}</strong>
      <i aria-hidden="true"></i>
    </div>
  `;
}

function renderSemesterTable(semesters) {
  if (!semesters.length) return `<div class="empty">${t("stats.noCourses")}</div>`;
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>${t("stats.semester")}</th>
          <th>${t("stats.courses")}</th>
          <th>${t("stats.credits")}</th>
          <th>${t("stats.graded")}</th>
          <th>${t("stats.avgScore")}</th>
          <th>${t("stats.gpa")}</th>
        </tr></thead>
        <tbody>
          ${semesters
            .map(
              (row) => `
                <tr>
                  <td><strong>${escapeHtml(row.semester)}</strong></td>
                  <td>${row.courses}</td>
                  <td>${row.credits}</td>
                  <td>${row.graded}</td>
                  <td>${row.avgScore || t("common.notSet")}</td>
                  <td>${row.gpa ? row.gpa.toFixed(2) : t("common.notSet")}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderGradeMap(gradeMap) {
  return `
    <div class="grade-map">
      ${gradeMap
        .map(
          (item) => `
            <div class="grade-map-row">
              <span>${escapeHtml(item.range)}</span>
              <b>${item.gp.toFixed(1)}</b>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}
