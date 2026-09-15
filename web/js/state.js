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
};

export const pages = [
  { id: "dashboard", title: "总览" },
  { id: "sop", title: "面试 SOP" },
  { id: "contact", title: "套磁" },
  { id: "resources", title: "资源" },
  { id: "programs", title: "院校" },
  { id: "tasks", title: "待办" },
  { id: "questions", title: "面试" },
];
