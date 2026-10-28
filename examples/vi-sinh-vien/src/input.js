const DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;
export function isValidDate(value) {
  const match = DATE_PATTERN.exec(String(value || ""));
  if (!match) return false;
  const year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
  const parsed = new Date(year, month - 1, day);
  return parsed.getFullYear() === year && parsed.getMonth() === month - 1 && parsed.getDate() === day;
}
export function validateTransactionInput(input) {
  const id = String(input.id || "").trim();
  const type = String(input.type || "");
  const name = String(input.name || "").trim();
  const amount = Number(input.amount);
  const category = String(input.category || "").trim();
  const date = String(input.date || "");
  const note = String(input.note || "").trim();
  if (!name) return { ok: false, error: "Vui lòng nhập tên giao dịch." };
  if (!["income", "expense"].includes(type)) return { ok: false, error: "Hãy chọn thu nhập hoặc chi tiêu." };
  if (!Number.isFinite(amount) || amount <= 0) return { ok: false, error: "Số tiền phải lớn hơn 0." };
  if (!category) return { ok: false, error: "Vui lòng chọn danh mục." };
  if (!isValidDate(date)) return { ok: false, error: "Ngày giao dịch không hợp lệ." };
  return { ok: true, value: { id, type, name: name.slice(0, 80), amount: Math.round(amount), category: category.slice(0, 60), date, note: note.slice(0, 200) } };
}
export function parseBackupData(data) {
  if (!data || !Array.isArray(data.transactions)) throw new Error("Tệp sao lưu không có danh sách giao dịch.");
  const transactions = data.transactions.map(item => {
    const amount = Number(item && item.amount);
    if (!item || !["income", "expense"].includes(item.type) || !Number.isFinite(amount) || amount <= 0 || !String(item.name || "").trim() || !isValidDate(item.date)) {
      throw new Error("Có giao dịch không hợp lệ trong tệp sao lưu.");
    }
    return { id: String(item.id || ""), type: item.type, name: String(item.name).trim().slice(0, 80), amount: Math.round(amount), category: String(item.category || "Khác").slice(0, 60), date: String(item.date), note: String(item.note || "").slice(0, 200), createdAt: Number(item.createdAt) || Date.now() };
  });
  const budgets = {};
  if (data.budgets && typeof data.budgets === "object" && !Array.isArray(data.budgets)) {
    Object.entries(data.budgets).forEach(([month, value]) => {
      const amount = Number(value);
      if (/^\d{4}-\d{2}$/.test(month) && Number.isFinite(amount) && amount > 0) budgets[month] = Math.round(amount);
    });
  }
  return { transactions, budgets };
}
