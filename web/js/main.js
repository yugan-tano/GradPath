import { api } from "./api.js";
import { initAppearance, renderLangToggle, toggleDark } from "./appearance.js";
import { deleteFile, openFolderPath, openMaterial } from "./files.js";
import { initI18n, setLang, currentLang, sceneText, t } from "./i18n.js";
import { renderContact } from "./pages/contact.js";
import { renderDashboard } from "./pages/dashboard.js";
import { renderAggregate } from "./pages/aggregate.js";
import { renderResources } from "./pages/resources.js";
import { renderSop } from "./pages/sop.js";
import { renderStats } from "./pages/stats.js";
import { renderTablePage } from "./pages/table.js";
import { ensureScene } from "./scene.js";
import { currentPage, state } from "./state.js";
import { $, escapeHtml } from "./utils.js";
import { applySceneName, bindExportButtons, loadSettings, openEditor, openSettings, renderNav, renderSceneSwitcher, toast } from "./ui.js";

function setPage(page) {
  state.page = page;
  state.q = "";
  $("#searchInput").value = "";
  render();
}

async function render() {
  renderNav(setPage);
  const page = currentPage() || {};
  const title = sceneText(page.title, page.titleEn) || "";
  $("#pageTitle").textContent = title;
  $("#searchInput").placeholder = state.page === "dashboard" ? t("search.all") : t("search.in", { title });
  const type = page.type || "table";
  if (type === "dashboard") return renderDashboard(bindCommonActions);
  if (type === "sop") return renderSop(render);
  if (type === "stats") return renderStats(bindCommonActions);
  if (type === "aggregate") return renderAggregate(page, bindCommonActions);
  if (type === "contact") return renderContact(bindCommonActions, render);
  if (type === "resources") return renderResources(bindCommonActions, scanMaterials);
  return renderTablePage(page.entity || state.page, bindCommonActions, render);
}

function bindCommonActions() {
  bindExportButtons();
  document.querySelectorAll("[data-jump]").forEach((button) => button.addEventListener("click", () => setPage(button.dataset.jump)));
  document.querySelectorAll("[data-open]").forEach((button) => button.addEventListener("click", () => openMaterial(button.dataset.open, toast)));
  document.querySelectorAll("[data-open-folder-path]").forEach((button) =>
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openFolderPath(button.dataset.openFolderPath, toast);
    }),
  );
  document.querySelectorAll("[data-delete-file]").forEach((button) => button.addEventListener("click", () => deleteFile(button.dataset.deleteFile, button.dataset.fileName, toast, render)));
  document.querySelectorAll("[data-edit-material]").forEach((button) => {
    button.addEventListener("click", async () => {
      const data = await api("/api/materials");
      const row = data.items.find((item) => String(item.id) === String(button.dataset.editMaterial));
      if (!row) return toast(t("main.noRecord"));
      openEditor("materials", row, render);
    });
  });
}

async function scanMaterials() {
  const data = await api("/api/materials/scan", { method: "POST" });
  toast(t("main.syncDone", { a: data.inserted, b: data.updated, c: data.missing }));
  render();
}

async function backupData() {
  const data = await api("/api/backup", { method: "POST" });
  toast(t("main.backupDone", { path: data.path }));
}

async function loadScenes() {
  const data = await api("/api/scenes");
  state.scenes = data.scenes;
  state.activeSceneId = data.active;
  renderSceneSwitcher(switchScene);
  applySceneName();
  bindSceneSwitcherToggle();
}

async function switchScene(id) {
  try {
    await api("/api/scene/switch", { method: "POST", body: JSON.stringify({ scene: id }) });
    state.scene = null;
    state.options = null;
    state.settings = null;
    state.rows = {};
    state.contactData = null;
    state.resourcePath = "";
    state.activeSceneId = id;
    state.page = "dashboard";
    await Promise.all([loadSettings(), ensureScene()]);
    renderSceneSwitcher(switchScene);
    applySceneName();
    render();
    toast(t("scene.switched"));
  } catch (error) {
    toast(error.message || t("scene.switchFail"));
  }
}

function bindSceneSwitcherToggle() {
  const btn = $("#sceneBtn");
  const menu = $("#sceneMenu");
  if (!btn || !menu) return;
  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    menu.hidden = !menu.hidden;
  });
  document.addEventListener("click", (event) => {
    if (!menu.hidden && !menu.contains(event.target) && event.target !== btn) menu.hidden = true;
  });
}

$("#scanBtn").addEventListener("click", scanMaterials);
$("#backupBtn").addEventListener("click", backupData);
$("#settingsBtn").addEventListener("click", () => openSettings(render));
$("#darkToggle").addEventListener("click", toggleDark);
$("#langToggle").addEventListener("click", () => {
  setLang(currentLang() === "zh" ? "en" : "zh");
  renderLangToggle();
  render();
});

let searchTimer = null;
$("#searchInput").addEventListener("input", (event) => {
  window.clearTimeout(searchTimer);
  state.q = event.target.value.trim();
  searchTimer = window.setTimeout(render, 160);
});

window.addEventListener("app-refresh", render);
window.addEventListener("app-scan", scanMaterials);
window.addEventListener("app-toast", (event) => toast(event.detail));

initI18n();
initAppearance();
renderLangToggle();

Promise.all([loadSettings(), ensureScene(), loadScenes()])
  .then(render)
  .catch((error) => {
    console.error(error);
    toast(error.message);
  });
