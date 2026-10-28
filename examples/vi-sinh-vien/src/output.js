import { CATEGORY_ICONS } from "./config.js";

export function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[char]);
}
export function formatMoney(value) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(Number(value) || 0);
}
export function formatDate(value) {
  if (!value) return "—";
  const parts = String(value).split("-").map(Number);
  if (parts.length !== 3 || parts.some(number => !number)) return String(value);
  return new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(parts[0], parts[1] - 1, parts[2]));
}
export function transactionRow(item) {
  const sign = item.type === "income" ? "+" : "−";
  const icon = CATEGORY_ICONS[item.category] || "•";
  return "<tr><td><span class=\"transaction-icon\">" + icon + "</span><strong>" + escapeHtml(item.name) + (item.note ? "<small>" + escapeHtml(item.note) + "</small>" : "") + "</strong></td>" +
    "<td><span class=\"category-pill\">" + escapeHtml(item.category) + "</span></td><td>" + formatDate(item.date) + "</td>" +
    "<td class=\"amount " + item.type + "\">" + sign + " " + formatMoney(item.amount) + "</td>" +
    "<td><div class=\"row-actions\"><button type=\"button\" data-action=\"edit\" data-id=\"" + escapeHtml(item.id) + "\">Sửa</button><button type=\"button\" class=\"delete\" data-action=\"delete\" data-id=\"" + escapeHtml(item.id) + "\">Xóa</button></div></td></tr>";
}
export function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
