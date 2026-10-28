import test from "node:test";
import assert from "node:assert/strict";
import { suggestCategory, analyzeSpending } from "../src/assistant.js";

test("auto-categorizes common Vietnamese expense text without accents", () => {
  assert.equal(suggestCategory("Cà phê trước giờ học", "expense"), "Ăn uống");
  assert.equal(suggestCategory("Do xang xe may", "expense"), "Đi lại");
  assert.equal(suggestCategory("Mua giao trinh", "expense"), "Học tập");
});
test("auto-categorizes income based on description", () => {
  assert.equal(suggestCategory("Luong lam them thang 10", "income"), "Làm thêm");
  assert.equal(suggestCategory("Hoc bong hoc ky", "income"), "Học bổng");
});
test("returns no category when no rule is a reasonable match", () => {
  assert.equal(suggestCategory("Khoan tien khong ro", "expense"), null);
});
test("daily analysis compares expenses with the previous day and budget guidance", () => {
  const transactions = [
    { id: "1", type: "expense", name: "Ăn trưa", category: "Ăn uống", amount: 30000, date: "2026-10-27" },
    { id: "2", type: "expense", name: "Cà phê", category: "Ăn uống", amount: 90000, date: "2026-10-28" },
    { id: "3", type: "income", name: "Làm thêm", category: "Làm thêm", amount: 500000, date: "2026-10-28" }
  ];
  const result = analyzeSpending(transactions, { "2026-10": 1500000 }, { period: "day", anchorDate: "2026-10-28" });
  assert.equal(result.transactions, 2);
  assert.equal(result.income, 500000);
  assert.equal(result.expense, 90000);
  assert.ok(result.insights.some(line => line.includes("tăng 200%")));
  assert.ok(result.recommendations.some(line => line.includes("ngân sách")));
});
test("monthly analysis flags a high-share category and recurring expenses", () => {
  const transactions = [
    { id: "1", type: "expense", name: "Tiền phòng", category: "Nhà ở", amount: 2000000, date: "2026-09-05" },
    { id: "2", type: "expense", name: "Tiền phòng", category: "Nhà ở", amount: 2100000, date: "2026-10-05" },
    { id: "3", type: "expense", name: "Ăn trưa", category: "Ăn uống", amount: 100000, date: "2026-10-06" },
    { id: "4", type: "income", name: "Lương", category: "Làm thêm", amount: 3000000, date: "2026-10-01" }
  ];
  const result = analyzeSpending(transactions, { "2026-10": 2500000 }, { period: "month", anchorDate: "2026-10-20" });
  assert.equal(result.expense, 2200000);
  assert.ok(result.insights.some(line => line.includes("Nhà ở")));
  assert.ok(result.insights.some(line => line.includes("lặp lại")));
});
test("year analysis aggregates monthly budgets", () => {
  const transactions = [
    { id: "1", type: "income", name: "Học bổng", category: "Học bổng", amount: 1000000, date: "2026-02-01" },
    { id: "2", type: "expense", name: "Sách", category: "Học tập", amount: 150000, date: "2026-02-02" }
  ];
  const result = analyzeSpending(transactions, { "2026-01": 2000000, "2026-02": 2000000 }, { period: "year", anchorDate: "2026-10-20" });
  assert.equal(result.transactions, 2);
  assert.equal(result.budget, 4000000);
  assert.ok(result.recommendations.some(line => line.includes("tháng còn lại")));
});
