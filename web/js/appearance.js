// 暗色模式：切换 body[data-dark]，持久化到 localStorage，并更新切换按钮图标。

import { t } from "./i18n.js";

const STORAGE_KEY = "gradpath.dark";

const MOON_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
const SUN_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>`;

export function isDark() {
  return document.body.dataset.dark === "true";
}

export function initAppearance() {
  const saved = localStorage.getItem(STORAGE_KEY);
  document.body.dataset.dark = saved === "1" || saved === "true" ? "true" : "false";
  renderDarkToggle();
}

export function toggleDark() {
  const next = document.body.dataset.dark !== "true";
  document.body.dataset.dark = next ? "true" : "false";
  localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
  renderDarkToggle();
  return next;
}

export function renderDarkToggle() {
  const btn = document.querySelector("#darkToggle");
  if (!btn) return;
  const dark = isDark();
  btn.innerHTML = dark ? SUN_SVG : MOON_SVG;
  const tip = t(dark ? "dark.toLight" : "dark.toDark");
  btn.title = tip;
  btn.setAttribute("aria-label", tip);
}

export function renderLangToggle() {
  const btn = document.querySelector("#langToggle");
  if (!btn) return;
  const isZh = document.documentElement.lang === "zh-CN";
  btn.textContent = isZh ? "EN" : "中";
  const tip = t(isZh ? "lang.toEnglish" : "lang.toChinese");
  btn.title = tip;
  btn.setAttribute("aria-label", tip);
}
