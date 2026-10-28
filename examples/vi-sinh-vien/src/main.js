import { CATEGORIES } from "./config.js";
import { currentMonth, localDate, monthlySummary, expensesByCategory } from "./finance.js";
import { validateTransactionInput, parseBackupData } from "./input.js";
import { loadState, saveState, clearState } from "./storage.js";
import { escapeHtml, formatMoney, transactionRow, downloadFile } from "./output.js";
import { suggestCategory, analyzeSpending } from "./assistant.js";

const $ = selector => document.querySelector(selector);
const now = new Date();
const monthNow = currentMonth(now);
let state = loadState();
let noticeTimer;
let categoryManuallyChosen = false;
let lastSuggestedCategory = "";

function showNotice(message, error = false) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.style.color = error ? "#c75a55" : "#168967";
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => { notice.textContent = ""; }, 3500);
}
function selectedMonthItems() {
  const month = $("#month-select").value || monthNow;
  return state.transactions.filter(item => item.date && item.date.slice(0, 7) === month);
}
function persist() {
  if (!saveState(state)) {
    showNotice("Không thể lưu dữ liệu. Hãy xuất bản sao lưu và kiểm tra dung lượng trình duyệt.", true);
    return false;
  }
  return true;
}
function refreshCategories(selected = "") {
  const options = CATEGORIES[$("#transaction-type").value];
  $("#transaction-category").innerHTML = options.map(category => "<option value=\"" + escapeHtml(category) + "\"" + (category === selected ? " selected" : "") + ">" + escapeHtml(category) + "</option>").join("");
}
function applyCategorySuggestion() {
  const hint = $("#category-auto-hint");
  if (!hint) return;
  const guess = suggestCategory($("#transaction-name").value + " " + $("#transaction-note").value, $("#transaction-type").value);
  if (!guess) {
    if (!categoryManuallyChosen && lastSuggestedCategory && $("#transaction-category").value === lastSuggestedCategory) $("#transaction-category").selectedIndex = 0;
    lastSuggestedCategory = "";
    hint.textContent = "Chưa nhận diện được danh mục; bạn có thể chọn thủ công.";
    hint.classList.toggle("manual", categoryManuallyChosen);
    return;
  }
  if (categoryManuallyChosen) {
    hint.textContent = "Bạn đang chọn thủ công: " + $("#transaction-category").value + ".";
    hint.classList.add("manual");
    return;
  }
  const hasOption = Array.from($("#transaction-category").options).some(option => option.value === guess);
  if (hasOption) {
    $("#transaction-category").value = guess;
    lastSuggestedCategory = guess;
    hint.textContent = "Tự gợi ý danh mục: " + guess + ". Bạn vẫn có thể đổi nếu chưa đúng.";
    hint.classList.remove("manual");
  } else {
    hint.textContent = "Gợi ý " + guess + " không có trong danh mục hiện tại; hãy chọn thủ công.";
  }
}
function renderAssistant() {
  const analysis = analyzeSpending(state.transactions, state.budgets, {
    period: $("#assistant-period").value,
    anchorDate: $("#assistant-date").value || localDate(new Date())
  });
  $("#assistant-range").textContent = analysis.title;
  $("#assistant-income").textContent = formatMoney(analysis.income);
  $("#assistant-expense").textContent = formatMoney(analysis.expense);
  $("#assistant-count").textContent = String(analysis.transactions);
  $("#assistant-insights").innerHTML = analysis.insights.map(item => "<li>" + escapeHtml(item) + "</li>").join("");
  $("#assistant-recommendations").innerHTML = analysis.recommendations.map(item => "<li>" + escapeHtml(item) + "</li>").join("");
}

function renderSummary() {
  const summary = monthlySummary(selectedMonthItems());
  $("#balance-total").textContent = formatMoney(summary.balance);
  $("#income-total").textContent = formatMoney(summary.income);
  $("#expense-total").textContent = formatMoney(summary.expense);
  $("#saving-rate").textContent = summary.savingRate + "%";
  renderCategories();
  renderBudget();
}
function renderCategories() {
  const categories = expensesByCategory(selectedMonthItems());
  const total = categories.reduce((sum, item) => sum + item.amount, 0);
  const target = $("#category-summary");
  if (!categories.length) { target.innerHTML = "<p class=\"empty\">Chưa có dữ liệu chi tiêu trong tháng.</p>"; return; }
  target.innerHTML = categories.map(item => {
    const percent = total ? Math.round(item.amount / total * 100) : 0;
    return "<div class=\"category-item\"><span class=\"category-icon\">" + escapeHtml(item.category.slice(0, 1)) + "</span><div><div class=\"category-label\">" + escapeHtml(item.category) + "</div><div class=\"category-track\"><span style=\"width:" + percent + "%\"></span></div></div><span class=\"category-amount\">" + formatMoney(item.amount) + "</span></div>";
  }).join("");
}
function renderBudget() {
  const month = $("#budget-month").value || monthNow;
  const spent = state.transactions.filter(item => item.date && item.date.slice(0, 7) === month && item.type === "expense").reduce((sum, item) => sum + Number(item.amount || 0), 0);
  const limit = Number(state.budgets[month]) || 0;
  const left = limit - spent;
  const percent = limit > 0 ? Math.round(spent / limit * 100) : 0;
  $("#budget-limit").value = limit || "";
  $("#budget-spent").textContent = formatMoney(spent);
  $("#budget-left").textContent = limit ? formatMoney(left) : "Chưa đặt";
  $("#budget-percent").textContent = limit ? percent + "%" : "—";
  $("#budget-progress").style.width = Math.min(100, Math.max(0, percent)) + "%";
  $("#budget-progress").style.background = percent > 100 ? "#dd7655" : percent >= 80 ? "#e5a14a" : "#6658d3";
  $("#budget-note").textContent = !limit ? "Hãy đặt ngân sách để bắt đầu theo dõi." : percent > 100 ? "Bạn đã vượt ngân sách " + formatMoney(spent - limit) + "." : percent >= 80 ? "Bạn đã sử dụng phần lớn ngân sách tháng này." : "Bạn còn " + formatMoney(left) + " trong ngân sách tháng.";
  $("#budget-left").style.color = limit && left < 0 ? "#dd7655" : "";
}
function renderTransactions() {
  const query = $("#search-input").value.trim().toLocaleLowerCase("vi-VN");
  const type = $("#type-filter").value;
  const items = state.transactions.filter(item => {
    const text = (item.name + " " + item.category + " " + (item.note || "")).toLocaleLowerCase("vi-VN");
    return (!query || text.includes(query)) && (type === "all" || type === item.type);
  }).sort((a, b) => b.date.localeCompare(a.date) || Number(b.createdAt || 0) - Number(a.createdAt || 0));
  $("#transaction-list").innerHTML = items.map(transactionRow).join("");
  $("#transactions-empty").hidden = items.length > 0;
  $("#transaction-count").textContent = items.length + " giao dịch";
}
function renderAll() { renderSummary(); renderTransactions(); renderAssistant(); }
function resetTransactionForm() {
  $("#transaction-form").reset();
  categoryManuallyChosen = false;
  lastSuggestedCategory = "";
  $("#transaction-id").value = "";
  $("#transaction-date").value = localDate(now);
  $("#transaction-type").value = "expense";
  refreshCategories();
  applyCategorySuggestion();
  $("#save-transaction").textContent = "Lưu giao dịch";
  $("#cancel-edit").hidden = true;
}
function onTransactionSubmit(event) {
  event.preventDefault();
  const result = validateTransactionInput({
    id: $("#transaction-id").value, type: $("#transaction-type").value, category: $("#transaction-category").value,
    name: $("#transaction-name").value, amount: $("#transaction-amount").value, date: $("#transaction-date").value,
    note: $("#transaction-note").value
  });
  if (!result.ok) { showNotice(result.error, true); return; }
  const value = result.value;
  const existing = value.id ? state.transactions.find(item => item.id === value.id) : null;
  const transaction = {
    ...value,
    id: value.id || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : "txn-" + Date.now() + "-" + Math.random().toString(36).slice(2)),
    createdAt: existing ? existing.createdAt : Date.now()
  };
  state.transactions = existing ? state.transactions.map(row => row.id === existing.id ? transaction : row) : state.transactions.concat(transaction);
  if (!persist()) return;
  resetTransactionForm(); renderAll(); showNotice(existing ? "Đã cập nhật giao dịch." : "Đã thêm giao dịch.");
}
function handleTransactionAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const item = state.transactions.find(row => row.id === button.dataset.id);
  if (!item) return;
  if (button.dataset.action === "edit") {
    $("#transaction-id").value = item.id; $("#transaction-type").value = item.type; refreshCategories(item.category);
    $("#transaction-name").value = item.name; $("#transaction-amount").value = item.amount;
    $("#transaction-date").value = item.date; $("#transaction-note").value = item.note || "";
    $("#save-transaction").textContent = "Lưu thay đổi"; $("#cancel-edit").hidden = false; $("#transaction-name").focus();
  } else if (button.dataset.action === "delete" && confirm("Xóa giao dịch \"" + item.name + "\"?")) {
    state.transactions = state.transactions.filter(row => row.id !== item.id);
    if (persist()) { renderAll(); showNotice("Đã xóa giao dịch."); }
  }
}
function exportCsv() {
  if (!state.transactions.length) { showNotice("Chưa có giao dịch để xuất.", true); return; }
  const rows = [["Ngày", "Loại", "Tên giao dịch", "Danh mục", "Số tiền (VND)", "Ghi chú"]];
  state.transactions.slice().sort((a, b) => a.date.localeCompare(b.date)).forEach(item => rows.push([
    item.date, item.type === "income" ? "Thu nhập" : "Chi tiêu", item.name, item.category, String(item.amount), item.note || ""
  ]));
  const csv = "\uFEFF" + rows.map(row => row.map(value => "\"" + String(value).replace(/"/g, "\"\"") + "\"").join(",")).join("\r\n");
  downloadFile(csv, "vi-sinh-vien-" + localDate(now) + ".csv", "text/csv;charset=utf-8;");
  showNotice("Đã xuất CSV.");
}
function exportBackup() {
  const data = { app: "ViSinhVien", version: 1, exportedAt: new Date().toISOString(), transactions: state.transactions, budgets: state.budgets };
  downloadFile(JSON.stringify(data, null, 2), "sao-luu-vi-sinh-vien-" + localDate(now) + ".json", "application/json");
  showNotice("Đã tải bản sao lưu JSON.");
}
function importBackup(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = parseBackupData(JSON.parse(String(reader.result)));
      if (!confirm("Nhập " + parsed.transactions.length + " giao dịch và thay thế dữ liệu hiện tại? Hãy sao lưu trước nếu muốn giữ dữ liệu cũ.")) return;
      state = parsed;
      state.transactions = state.transactions.map(item => ({ ...item, id: item.id || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : "txn-" + Date.now()) }));
      if (persist()) { renderAll(); showNotice("Đã khôi phục dữ liệu."); }
    } catch (error) {
      showNotice("Tệp JSON không đúng định dạng bản sao lưu của Ví Sinh Viên.", true);
    } finally { $("#import-json").value = ""; }
  };
  reader.onerror = () => showNotice("Không đọc được tệp JSON.", true);
  reader.readAsText(file);
}
function bindEvents() {
  $("#transaction-form").addEventListener("submit", onTransactionSubmit);
  $("#transaction-type").addEventListener("change", () => { categoryManuallyChosen = false; lastSuggestedCategory = ""; refreshCategories(); applyCategorySuggestion(); });
  $("#transaction-category").addEventListener("change", () => { categoryManuallyChosen = true; lastSuggestedCategory = ""; $("#category-auto-hint").textContent = "Bạn đã chọn danh mục thủ công: " + $("#transaction-category").value + "."; $("#category-auto-hint").classList.add("manual"); });
  $("#transaction-name").addEventListener("input", applyCategorySuggestion);
  $("#transaction-note").addEventListener("input", applyCategorySuggestion);
  $("#cancel-edit").addEventListener("click", resetTransactionForm);
  $("#month-select").addEventListener("change", renderSummary);
  $("#assistant-run").addEventListener("click", renderAssistant);
  $("#assistant-period").addEventListener("change", renderAssistant);
  $("#assistant-date").addEventListener("change", renderAssistant);
  $("#budget-month").addEventListener("change", renderBudget);
  $("#budget-form").addEventListener("submit", event => {
    event.preventDefault();
    const month = $("#budget-month").value, amount = Number($("#budget-limit").value);
    if (!month || !Number.isFinite(amount) || amount <= 0) { showNotice("Hãy nhập tháng và ngân sách lớn hơn 0 đồng.", true); return; }
    state.budgets[month] = Math.round(amount);
    if (persist()) { renderBudget(); showNotice("Đã lưu ngân sách."); }
  });
  $("#search-input").addEventListener("input", renderTransactions);
  $("#type-filter").addEventListener("change", renderTransactions);
  $("#transaction-list").addEventListener("click", handleTransactionAction);
  $("#export-csv").addEventListener("click", exportCsv);
  $("#backup-json").addEventListener("click", exportBackup);
  $("#import-json").addEventListener("change", event => importBackup(event.target.files && event.target.files[0]));
  $("#clear-data").addEventListener("click", () => {
    if (!confirm("Xóa toàn bộ giao dịch và ngân sách đã lưu trong trình duyệt này? Hãy sao lưu JSON trước nếu cần.")) return;
    state = { transactions: [], budgets: {} };
    try { clearState(); } catch (error) { console.warn("Không thể xóa dữ liệu cục bộ:", error); }
    resetTransactionForm(); renderAll(); showNotice("Đã xóa dữ liệu trên trình duyệt này.");
  });
}
function init() {
  $("#month-select").value = monthNow; $("#budget-month").value = monthNow; $("#assistant-date").value = localDate(now); $("#transaction-date").value = localDate(now);
  refreshCategories(); bindEvents(); renderAll();
}
init();
