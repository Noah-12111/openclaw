import { STORAGE_KEY } from "./config.js";
export function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return { transactions: [], budgets: {} };
    const parsed = JSON.parse(saved);
    return {
      transactions: Array.isArray(parsed.transactions) ? parsed.transactions : [],
      budgets: parsed.budgets && typeof parsed.budgets === "object" && !Array.isArray(parsed.budgets) ? parsed.budgets : {}
    };
  } catch (error) {
    console.warn("Không đọc được dữ liệu đã lưu:", error);
    return { transactions: [], budgets: {} };
  }
}
export function saveState(state) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); return true; }
  catch (error) { console.error("Không thể lưu dữ liệu:", error); return false; }
}
export function clearState() { localStorage.removeItem(STORAGE_KEY); }
