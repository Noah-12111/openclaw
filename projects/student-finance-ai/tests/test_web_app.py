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

    def request_json(self, path, payload=None, method=None, content_type="application/json"):
        body = None if payload is None else (
            payload.encode("utf-8") if isinstance(payload, str)
            else json.dumps(payload).encode("utf-8")
        )
        request_method = method or ("POST" if body is not None else "GET")
        headers = {"Content-Type": content_type} if body is not None else {}
        request = Request(self.base_url + path, data=body, headers=headers, method=request_method)
        with urlopen(request, timeout=3) as response:
            raw = response.read().decode("utf-8-sig")
            return response.status, json.loads(raw) if "application/json" in response.headers.get("Content-Type", "") else raw

    def expect_http_error(self, path, payload, method, expected_code, content_type="application/json"):
        body = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=body, method=method, headers={"Content-Type": content_type})
        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=3)
        self.assertEqual(raised.exception.code, expected_code)

    def test_dashboard_is_served_with_security_headers(self):
        with urlopen(self.base_url + "/", timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("SpendWise", response.read().decode("utf-8"))
            self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
            self.assertIn("Content-Security-Policy", response.headers)

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
        self.expect_http_error("/api/transactions", {
            "kind": "expense", "amount_vnd": 10.5, "category": "food"
        }, "POST", 400)

    def test_create_budget_and_delete_budget(self):
        status, result = self.request_json("/api/budgets", {
            "month": "2026-10", "category": "food", "amount_vnd": 500000
        })
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        _, budgets = self.request_json("/api/budgets?month=2026-10")
        self.assertEqual(budgets["budgets"][0]["budget_vnd"], 500000)
        _, deleted = self.request_json("/api/budgets?month=2026-10&category=food", method="DELETE")
        self.assertTrue(deleted["ok"])
        _, budgets = self.request_json("/api/budgets?month=2026-10")
        self.assertEqual(budgets["budgets"], [])

    def test_update_and_delete_transaction_via_api(self):
        _, created = self.request_json("/api/transactions", {
            "kind": "expense", "amount_vnd": 45000, "category": "food",
            "note": "Lunch", "transaction_date": "2026-10-28"
        })
        tx_id = created["id"]
        _, updated = self.request_json(f"/api/transactions/{tx_id}", {
            "kind": "income", "amount_vnd": 60000, "category": "refund",
            "note": "Refund", "transaction_date": "2026-10-29"
        }, method="PUT")
        self.assertTrue(updated["ok"])
        _, transaction = self.request_json(f"/api/transactions/{tx_id}")
        self.assertEqual(transaction["transaction"]["kind"], "income")
        _, deleted = self.request_json(f"/api/transactions/{tx_id}", method="DELETE")
        self.assertTrue(deleted["ok"])
        self.expect_http_error(f"/api/transactions/{tx_id}", {}, "DELETE", 404)

    def test_csv_import_and_export(self):
        csv_data = "transaction_date,kind,amount_vnd,category,note\n2026-10-28,expense,45000,food,Lunch\n"
        _, imported = self.request_json("/api/import.csv", csv_data, content_type="text/csv; charset=utf-8")
        self.assertEqual(imported["imported"], 1)
        _, summary = self.request_json("/api/summary?month=2026-10")
        self.assertEqual(summary["expenses_vnd"], 45000)
        _, export_text = self.request_json("/api/export.csv?month=2026-10")
        self.assertIn("transaction_date,kind,amount_vnd,category,note", export_text)
        self.assertIn("45000", export_text)
        self.assertIn("Content", "")  # response parsing handled by request_json

    def test_csv_import_rejects_malformed_data_without_partial_write(self):
        csv_data = "transaction_date,kind,amount_vnd,category,note\n2026-10-28,expense,45000,food,Lunch\n2026-99-99,expense,100,food,Bad\n"
        self.expect_http_error("/api/import.csv", csv_data, "POST", 400, "text/csv")
        _, summary = self.request_json("/api/summary?month=2026-10")
        self.assertEqual(summary["transaction_count"], 0)

    def test_categories_endpoint(self):
        self.request_json("/api/transactions", {
            "kind": "expense", "amount_vnd": 45000, "category": "food", "transaction_date": "2026-10-28"
        })
        _, result = self.request_json("/api/categories")
        self.assertEqual(result["categories"], ["food"])


if __name__ == "__main__":
    unittest.main()
