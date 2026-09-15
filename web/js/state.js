export const state = {
  page: "dashboard",
  q: "",
  rows: {},
  contactData: null,
  resourceMode: "folder",
  resourcePath: "",
  options: null,
  settings: null,
  scene: null,
  scenes: [],
  activeSceneId: "",
};

// 场景驱动的导航页：由 scenes/<id>/scene.json 的 pages 声明，不再硬编码。
export function scenePages() {
  return state.scene?.pages || [];
}

export function currentPage() {
  return scenePages().find((item) => item.id === state.page) || null;
}
