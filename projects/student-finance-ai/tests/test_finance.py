import sqlite3
import unittest
from finance import add_transaction, init_db, list_budgets, list_transactions, monthly_summary, set_budget

class FinanceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)
    def tearDown(self): self.conn.close()
    def test_monthly_summary_and_month_boundary(self):
        add_transaction(self.conn,"income",1500000,"allowance",transaction_date="2026-10-01")
        add_transaction(self.conn,"expense",25000,"food",transaction_date="2026-10-02")
        add_transaction(self.conn,"expense",100000,"books",transaction_date="2026-10-31")
        add_transaction(self.conn,"expense",50000,"food",transaction_date="2026-11-01")
        r = monthly_summary(self.conn,"2026-10")
        self.assertEqual((r["income_vnd"],r["expenses_vnd"],r["balance_vnd"],r["transaction_count"]),(1500000,125000,1375000,3))
        self.assertEqual(r["expenses_by_category"][0]["category"],"books")
    def test_rejects_invalid_amount_and_type(self):
        with self.assertRaises(ValueError): add_transaction(self.conn,"expense",0,"food")
        with self.assertRaises(ValueError): add_transaction(self.conn,"transfer",1000,"food")
    def test_rejects_invalid_date_and_month(self):
        with self.assertRaises(ValueError): add_transaction(self.conn,"expense",1000,"food",transaction_date="yesterday")
        with self.assertRaises(ValueError): add_transaction(self.conn,"expense",1000,"food",transaction_date="20261028")
        with self.assertRaises(ValueError): monthly_summary(self.conn,"2026-13")
    def test_budget_upsert_and_spending(self):
        add_transaction(self.conn,"expense",120000,"food",transaction_date="2026-10-05")
        set_budget(self.conn,"2026-10","food",300000); set_budget(self.conn,"2026-10","food",250000)
        rows = list_budgets(self.conn,"2026-10")
        self.assertEqual((len(rows),rows[0]["budget_vnd"],rows[0]["spent_vnd"],rows[0]["remaining_vnd"]),(1,250000,120000,130000))
    def test_list_filters_month(self):
        add_transaction(self.conn,"expense",1000,"food",transaction_date="2026-10-31")
        add_transaction(self.conn,"expense",2000,"food",transaction_date="2026-11-01")
        self.assertEqual(len(list_transactions(self.conn,month="2026-10")),1)

if __name__ == "__main__": unittest.main()
