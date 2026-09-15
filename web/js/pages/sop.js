import { api } from "../api.js";
import { escapeHtml } from "../utils.js";
import { toast } from "../ui.js";

const STATUS_LABEL = { pending: "未开始", active: "进行中", done: "已完成" };

export async function renderSop(refresh) {
  const acts = await api("/api/sop");
  document.querySelector("#app").innerHTML = acts
    .map((act) => renderAct(act))
    .join("") || `<div class="empty">当前场景未配置 SOP 流程。</div>`;
  bindSopActions(refresh);
}

function renderAct(act) {
  return `
    <section class="panel">
      <div class="panel-head"><h3>${escapeHtml(act.name)}</h3></div>
      <div class="panel-body sop-flow">
        ${act.stages.map((stage, index) => renderStage(stage, index, act.stages.length)).join("")}
      </div>
    </section>
  `;
}

function renderStage(stage, index, total) {
  const status = stage.state?.status || "pending";
  const statusLabel = STATUS_LABEL[status] || status;
  const enterOk = stage.enterOk !== false;
  const exitOk = stage.exitOk !== false;
  const enterHint = stage.enterReasons?.length ? `（${stage.enterReasons[0]}）` : "";
  const exitHint = stage.exitReasons?.length ? `（${stage.exitReasons[0]}）` : "";
  return `
    <div class="sop-stage" data-stage="${escapeHtml(stage.id)}">
      <div class="sop-stage-head">
        <span class="sop-step">${index + 1}</span>
        <div class="sop-stage-title">
          <strong>${escapeHtml(stage.name)}</strong>
          <span class="sop-cond ${enterOk ? "ok" : "warn"}" title="${escapeHtml((stage.enterReasons || []).join("；"))}">${stage.enter ? `进入条件：${enterOk ? "已满足" : "未满足"}${enterHint}` : "无进入条件"}</span>
        </div>
        <span class="badge ${status === "done" ? "" : status === "active" ? "hot" : ""}">${statusLabel}</span>
      </div>
      ${stage.checklist ? renderChecklist(stage.checklist, status) : ""}
      <div class="sop-stage-foot">
        ${stage.exit ? `<span class="sop-cond ${exitOk ? "ok" : "warn"}" title="${escapeHtml((stage.exitReasons || []).join("；"))}">退出条件：${exitOk ? "已满足" : "未满足"}${exitHint}</span>` : ""}
        <div class="actions">
          ${status === "pending" ? `<button class="primary" data-sop-start="${escapeHtml(stage.id)}">开始</button>` : ""}
          ${status === "active" ? `<button class="primary" data-sop-advance="${escapeHtml(stage.id)}">完成本阶段</button>` : ""}
          ${status === "done" ? `<button class="mini" data-sop-reset="${escapeHtml(stage.id)}">重置</button>` : ""}
        </div>
      </div>
    </div>
  `;
}

function renderChecklist(checklistId, status) {
  return `<div class="sop-checklist" data-checklist="${escapeHtml(checklistId)}">载入中…</div>`;
}

async function loadChecklist(container) {
  const checklistId = container.dataset.checklist;
  try {
    const data = await api(`/api/checklist/global/${encodeURIComponent(checklistId)}`);
    container.innerHTML = `
      <div class="sop-checklist-head">
        <span>检查清单</span>
        <b>${data.done}/${data.total}</b>
      </div>
      <ul class="sop-check-list">
        ${data.items
          .map(
            (item) => `
              <li>
                <label>
                  <input type="checkbox" data-check-item="${item.id}" ${item.done ? "checked" : ""} />
                  <span class="${item.done ? "done" : ""}">${escapeHtml(item.title)}</span>
                </label>
              </li>
            `,
          )
          .join("")}
      </ul>
    `;
    bindChecklistItems(container);
  } catch (error) {
    container.innerHTML = `<span class="muted">清单加载失败：${escapeHtml(error.message)}</span>`;
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
    toast("已更新阶段状态");
    refresh();
  } catch (error) {
    toast(error.message || "操作失败");
  }
}
