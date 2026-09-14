import { api } from "./api.js";
import { state } from "./state.js";

export async function ensureScene() {
  if (!state.scene) state.scene = await api("/api/scene");
  return state.scene;
}

export function entity(page) {
  return state.scene?.entities?.[page] || null;
}
