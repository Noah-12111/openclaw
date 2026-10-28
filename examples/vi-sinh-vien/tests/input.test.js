import test from "node:test";
import assert from "node:assert/strict";
import { validateTransactionInput, parseBackupData } from "../src/input.js";

test("accepts valid transaction input and normalizes the amount", () => {
  const result = validateTransactionInput({ type: "expense", name: "Ăn trưa", amount: "45000", category: "Ăn uống", date: "2026-10-28", note: "Ở trường" });
  assert.equal(result.ok, true);
  assert.equal(result.value.amount, 45000);
});
test("rejects non-positive amounts", () => {
  for (const amount of ["0", "-1", "NaN"]) {
    const result = validateTransactionInput({ type: "expense", name: "Test", amount, category: "Khác", date: "2026-10-28" });
    assert.equal(result.ok, false);
  }
});
test("rejects impossible calendar dates", () => {
  const result = validateTransactionInput({ type: "expense", name: "Test", amount: 10, category: "Khác", date: "2026-02-30" });
  assert.equal(result.ok, false);
});
test("normalizes backup transactions and ignores invalid budget entries", () => {
  const result = parseBackupData({ transactions: [{ id: "a", type: "income", name: "Học bổng", amount: 1000000, category: "Học bổng", date: "2026-10-01" }], budgets: { "2026-10": 2500000, invalid: -100 } });
  assert.equal(result.transactions.length, 1);
  assert.equal(result.budgets["2026-10"], 2500000);
  assert.equal(Object.hasOwn(result.budgets, "invalid"), false);
});
test("rejects malformed backup files", () => {
  assert.throws(() => parseBackupData({ transactions: [{ type: "expense", name: "Invalid", amount: 1, date: "2026-02-30" }] }));
});
