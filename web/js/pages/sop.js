import { api } from "../api.js";
import { sceneText, t } from "../i18n.js";
import { ensureScene } from "../scene.js";
import { escapeHtml } from "../utils.js";
import { toast } from "../ui.js";

const STATUS_LABEL = { pending: () => t("sop.status.pending"), active: () => t("sop.status.active"), done: () => t("sop.status.done") };

export async function renderSop(refresh) {
  const acts = await api("/api/sop");
  document.querySelector("#app").innerHTML = acts
    .map((act) => renderAct(act))
    .join("") || `<div class="empty">${t("sop.empty")}</div>`;
  bindSopActions(refresh);
}

function renderAct(act) {
  return `
    <section class="panel">
      <div class="panel-head"><h3>${escapeHtml(sceneText(act.name, act.nameEn))}</h3></div>
      <div class="panel-body sop-flow">
        ${act.stages.map((stage, index) => renderStage(stage, index, act.stages.length)).join("")}
      </div>
    </section>
  `;
}

function renderStage(stage, index, total) {
  const status = stage.state?.status || "pending";
  const statusLabel = STATUS_LABEL[status] ? STATUS_LABEL[status]() : status;
  const enterOk = stage.enterOk !== false;
  const exitOk = stage.exitOk !== false;
  const enterHint = stage.enterReasons?.length ? `（${stage.enterReasons[0]}）` : "";
  const exitHint = stage.exitReasons?.length ? `（${stage.exitReasons[0]}）` : "";
  const enterText = stage.enter
    ? `${enterOk ? t("sop.enterOk") : t("sop.enterNot")}${enterHint}`
    : t("sop.noEnter");
  const exitText = `${exitOk ? t("sop.exitOk") : t("sop.exitNot")}${exitHint}`;
  return `
    <div class="sop-stage" data-stage="${escapeHtml(stage.id)}">
      <div class="sop-stage-head">
        <span class="sop-step">${index + 1}</span>
        <div class="sop-stage-title">
          <strong>${escapeHtml(sceneText(stage.name, stage.nameEn))}</strong>
          <span class="sop-cond ${enterOk ? "ok" : "warn"}" title="${escapeHtml((stage.enterReasons || []).join("；"))}">${enterText}</span>
        </div>
        <span class="badge ${status === "done" ? "" : status === "active" ? "hot" : ""}">${statusLabel}</span>
      </div>
      ${stage.checklist ? renderChecklist(stage.checklist, status) : ""}
      <div class="sop-stage-foot">
        ${stage.exit ? `<span class="sop-cond ${exitOk ? "ok" : "warn"}" title="${escapeHtml((stage.exitReasons || []).join("；"))}">${exitText}</span>` : ""}
        <div class="actions">
          ${status === "pending" ? `<button class="primary" data-sop-start="${escapeHtml(stage.id)}">${t("sop.start")}</button>` : ""}
          ${status === "active" ? `<button class="primary" data-sop-advance="${escapeHtml(stage.id)}">${t("sop.finish")}</button>` : ""}
          ${status === "done" ? `<button class="mini" data-sop-reset="${escapeHtml(stage.id)}">${t("sop.reset")}</button>` : ""}
        </div>
      </div>
    </div>
  `;
}

function renderChecklist(checklistId, status) {
  return `<div class="sop-checklist" data-checklist="${escapeHtml(checklistId)}">${t("sop.loading")}</div>`;
}

async function loadChecklist(container) {
  const checklistId = container.dataset.checklist;
  try {
    const [data, scene] = await Promise.all([api(`/api/checklist/global/${encodeURIComponent(checklistId)}`), ensureScene()]);
    const cfg = scene.checklists?.[checklistId];
    const itemsEn = cfg?.itemsEn || [];
    container.innerHTML = `
      <div class="sop-checklist-head">
        <span>${t("sop.checklist")}</span>
        <b>${data.done}/${data.total}</b>
      </div>
      <ul class="sop-check-list">
        ${data.items
          .map(
            (item) => `
              <li>
                <label>
                  <input type="checkbox" data-check-item="${item.id}" ${item.done ? "checked" : ""} />
                  <span class="${item.done ? "done" : ""}">${escapeHtml(sceneText(item.title, itemsEn[item.sort_order]))}</span>
                </label>
              </li>
            `,
          )
          .join("")}
      </ul>
    `;
    bindChecklistItems(container);
  } catch (error) {
    container.innerHTML = `<span class="muted">${t("sop.loadFail", { msg: escapeHtml(error.message) })}</span>`;
  }
}

function bindChecklistItems(container) {
  container.querySelectorAll("[data-check-item]").forEach((checkbox) => {
    checkbox.addEventListener("change", async () => {
      await api(`/api/checklist/items/${checkbox.dataset.checkItem}`, {
        method: "PATCH",
        body: JSON.stringify({ done: checkbox.checked }),
      });
    });
  });
}

function bindSopActions(refresh) {
  document.querySelectorAll("[data-sop-start]").forEach((button) => {
    button.addEventListener("click", () => callSop(`/api/sop/${button.dataset.sopStart}/start`, refresh));
  });
  document.querySelectorAll("[data-sop-advance]").forEach((button) => {
    button.addEventListener("click", () => callSop(`/api/sop/${button.dataset.sopAdvance}/advance`, refresh));
  });
  document.querySelectorAll("[data-sop-reset]").forEach((button) => {
    button.addEventListener("click", () => callSop(`/api/sop/${button.dataset.sopReset}/reset`, refresh));
  });
  document.querySelectorAll("[data-checklist]").forEach((container) => loadChecklist(container));
}

async function callSop(path, refresh) {
  try {
    await api(path, { method: "POST" });
    toast(t("sop.updated"));
    refresh();
  } catch (error) {
    toast(error.message || t("sop.failed"));
  }
}
