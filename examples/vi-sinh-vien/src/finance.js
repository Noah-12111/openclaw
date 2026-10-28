export function currentMonth(date) {
  return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0");
}
export function localDate(date) {
  return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
}
export function totalByType(items, type) {
  return items.reduce((total, item) => total + (item.type === type ? Number(item.amount) || 0 : 0), 0);
}
export function monthlySummary(items) {
  const income = totalByType(items, "income");
  const expense = totalByType(items, "expense");
  return { income, expense, balance: income - expense, savingRate: income ? Math.round((income - expense) / income * 100) : 0 };
}
export function expensesByCategory(items) {
  const totals = new Map();
  items.filter(item => item.type === "expense").forEach(item => totals.set(item.category, (totals.get(item.category) || 0) + Number(item.amount || 0)));
  return Array.from(totals, ([category, amount]) => ({ category, amount })).sort((a, b) => b.amount - a.amount);
}
