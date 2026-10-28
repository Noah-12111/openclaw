import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from web_app import FinanceRequestHandler


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_db = os.environ.get("STUDENT_FINANCE_DB")
        os.environ["STUDENT_FINANCE_DB"] = os.path.join(self.temp_dir.name, "shared.db")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FinanceRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.old_db is None:
            os.environ.pop("STUDENT_FINANCE_DB", None)
        else:
            os.environ["STUDENT_FINANCE_DB"] = self.old_db
        self.temp_dir.cleanup()

    def request_json(self, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_dashboard_is_served(self):
        with urlopen(self.base_url + "/", timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("SpendWise", response.read().decode("utf-8"))

    def test_create_transaction_and_read_same_month_summary(self):
        status, created = self.request_json("/api/transactions", {
            "kind": "expense", "amount_vnd": 45000, "category": "food",
            "note": "Lunch", "transaction_date": "2026-10-28"
        })
        self.assertEqual(status, 201)
        self.assertTrue(created["ok"])
        _, summary = self.request_json("/api/summary?month=2026-10")
        self.assertEqual(summary["expenses_vnd"], 45000)
        self.assertEqual(summary["transaction_count"], 1)

    def test_rejects_non_integer_amount(self):
        request = Request(
            self.base_url + "/api/transactions",
            data=json.dumps({"kind": "expense", "amount_vnd": 10.5, "category": "food"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=3)
        self.assertEqual(raised.exception.code, 400)

    def test_create_budget(self):
        status, result = self.request_json("/api/budgets", {
            "month": "2026-10", "category": "food", "amount_vnd": 500000
        })
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        _, budgets = self.request_json("/api/budgets?month=2026-10")
        self.assertEqual(budgets["budgets"][0]["budget_vnd"], 500000)


if __name__ == "__main__":
    unittest.main()
