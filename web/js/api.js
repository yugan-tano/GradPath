import { t } from "./i18n.js";

export async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || t("api.requestFail", { status: response.status }));
  return payload;
}

export async function uploadForm(path, form) {
  const response = await fetch(path, { method: "POST", body: form });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || t("api.uploadFail"));
  return payload;
}
