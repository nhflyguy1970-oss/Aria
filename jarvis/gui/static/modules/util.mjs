/** Shared DOM helpers for ES modules. */

export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

export function $(id) {
  return document.getElementById(id);
}
