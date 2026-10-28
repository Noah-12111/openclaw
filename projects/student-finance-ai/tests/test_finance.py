import sqlite3
import unittest

from finance import (
    add_transaction, delete_budget, delete_transaction, get_transaction,
    import_transactions_csv, init_db, list_budgets, list_categories,
    list_transactions, monthly_summary, set_budget, update_transaction,
)


class FinanceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_monthly_summary_and_month_boundary(self):
        add_transaction(self.conn, "income", 1500000, "allowance", transaction_date="2026-10-01")
        add_transaction(self.conn, "expense", 25000, "food", transaction_date="2026-10-02")
        add_transaction(self.conn, "expense", 100000, "books", transaction_date="2026-10-31")
        add_transaction(self.conn, "expense", 50000, "food", transaction_date="2026-11-01")
        result = monthly_summary(self.conn, "2026-10")
        self.assertEqual(
            (result["income_vnd"], result["expenses_vnd"], result["balance_vnd"], result["transaction_count"]),
            (1500000, 125000, 1375000, 3),
        )
        self.assertEqual(result["expenses_by_category"][0]["category"], "books")

    def test_rejects_invalid_amount_and_type(self):
        with self.assertRaises(ValueError):
            add_transaction(self.conn, "expense", 0, "food")
        with self.assertRaises(ValueError):
            add_transaction(self.conn, "transfer", 1000, "food")
        with self.assertRaises(ValueError):
            add_transaction(self.conn, "expense", 10.5, "food")
        with self.assertRaises(ValueError):
            add_transaction(self.conn, "expense", 1000, "x" * 81)

    def test_rejects_invalid_date_and_month(self):
        with self.assertRaises(ValueError):
            add_transaction(self.conn, "expense", 1000, "food", transaction_date="yesterday")
        with self.assertRaises(ValueError):
            add_transaction(self.conn, "expense", 1000, "food", transaction_date="20261028")
        with self.assertRaises(ValueError):
            monthly_summary(self.conn, "2026-13")
        with self.assertRaises(ValueError):
            monthly_summary(self.conn, "2026-1")

    def test_budget_upsert_spending_and_delete(self):
        add_transaction(self.conn, "expense", 120000, "food", transaction_date="2026-10-05")
        set_budget(self.conn, "2026-10", "food", 300000)
        set_budget(self.conn, "2026-10", "food", 250000)
        rows = list_budgets(self.conn, "2026-10")
        self.assertEqual((len(rows), rows[0]["budget_vnd"], rows[0]["spent_vnd"], rows[0]["remaining_vnd"]),
                         (1, 250000, 120000, 130000))
        self.assertTrue(delete_budget(self.conn, "2026-10", "food"))
        self.assertFalse(delete_budget(self.conn, "2026-10", "food"))

    def test_list_filters_month(self):
        add_transaction(self.conn, "expense", 1000, "food", transaction_date="2026-10-31")
        add_transaction(self.conn, "expense", 2000, "food", transaction_date="2026-11-01")
        self.assertEqual(len(list_transactions(self.conn, month="2026-10")), 1)

    def test_search_and_kind_and_category_filters(self):
        add_transaction(self.conn, "expense", 1000, "food", "iced coffee", "2026-10-01")
        add_transaction(self.conn, "income", 5000, "salary", "part time", "2026-10-02")
        add_transaction(self.conn, "expense", 2000, "books", "course book", "2026-10-03")
        self.assertEqual(len(list_transactions(self.conn, "2026-10", search="coffee")), 1)
        self.assertEqual(len(list_transactions(self.conn, "2026-10", kind="income")), 1)
        self.assertEqual(list_transactions(self.conn, "2026-10", category="books")[0]["amount_vnd"], 2000)
        self.assertEqual(len(list_transactions(self.conn, "2026-10", search="%")), 0)

    def test_update_and_delete_transaction(self):
        tx_id = add_transaction(self.conn, "expense", 10000, "food", "lunch", "2026-10-01")
        self.assertTrue(update_transaction(self.conn, tx_id, "income", 25000, "salary", "refund", "2026-10-02"))
        result = get_transaction(self.conn, tx_id)
        self.assertEqual((result["kind"], result["amount_vnd"], result["category"], result["note"], result["transaction_date"]),
                         ("income", 25000, "salary", "refund", "2026-10-02"))
        self.assertFalse(update_transaction(self.conn, 9999, "expense", 1, "other", "", "2026-10-03"))
        self.assertTrue(delete_transaction(self.conn, tx_id))
        self.assertIsNone(get_transaction(self.conn, tx_id))
        self.assertFalse(delete_transaction(self.conn, tx_id))

    def test_csv_import_is_atomic(self):
        valid_header = "transaction_date,kind,amount_vnd,category,note\n"
        good_row = "2026-10-01,expense,45000,food,Lunch\n"
        bad_row = "2026-99-99,expense,10,food,Wrong date\n"
        with self.assertRaises(ValueError):
            import_transactions_csv(self.conn, valid_header + good_row + bad_row)
        self.assertEqual(monthly_summary(self.conn, "2026-10")["transaction_count"], 0)
        imported = import_transactions_csv(self.conn, valid_header + good_row + "2026-10-02,income,100000,allowance,Monthly\n")
        self.assertEqual(imported, 2)
        self.assertEqual(monthly_summary(self.conn, "2026-10")["transaction_count"], 2)

    def test_csv_import_rejects_missing_columns_and_empty_files(self):
        with self.assertRaises(ValueError):
            import_transactions_csv(self.conn, "")
        with self.assertRaises(ValueError):
            import_transactions_csv(self.conn, "kind,amount_vnd\nexpense,100\n")

    def test_categories_include_budgets_and_transactions(self):
        add_transaction(self.conn, "expense", 1000, "food")
        set_budget(self.conn, "2026-10", "transport", 50000)
        self.assertEqual(list_categories(self.conn), ["food", "transport"])


if __name__ == "__main__":
    unittest.main()
