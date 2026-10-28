#!/usr/bin/env python3
"""Local-only web UI/API for Student Finance AI; uses the same SQLite store as finance.py."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from finance import (
    add_transaction,
    connect,
    init_db,
    list_budgets,
    list_transactions,
    monthly_summary,
    set_budget,
)

PROJECT_DIR = Path(__file__).resolve().parent
INDEX_FILE = PROJECT_DIR / "static" / "index.html"
MAX_BODY_BYTES = 64 * 1024


class FinanceRequestHandler(BaseHTTPRequestHandler):
    server_version = "StudentFinanceAI/0.1"

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _json_error(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})

    def _read_json(self) -> dict:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json.")
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except (TypeError, ValueError) as exc:
            raise ValueError("A valid Content-Length header is required.") from exc
        if length < 0:
            raise ValueError("Invalid request body length.")
        if length > MAX_BODY_BYTES:
            raise OverflowError("Request body is too large.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid UTF-8 JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")
        return payload

    @staticmethod
    def _required_text(payload: dict, key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"'{key}' must be a non-empty string.")
        return value.strip()

    @staticmethod
    def _required_amount(payload: dict, key: str = "amount_vnd") -> int:
        value = payload.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"'{key}' must be a positive integer amount in VND.")
        return value

    def do_GET(self) -> None:  # noqa: N802 - HTTP handler API
        parsed = urlparse(self.path)
        if parsed.path == "/":
            try:
                body = INDEX_FILE.read_bytes()
            except OSError:
                self._json_error(500, "Web interface file is unavailable.")
                return
            self._send_bytes(200, body, "text/html; charset=utf-8")
            return

        query = parse_qs(parsed.query, keep_blank_values=False)
        month = query.get("month", [date.today().strftime("%Y-%m")])[0]
        try:
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/summary":
                    self._send_json(200, monthly_summary(conn, month))
                elif parsed.path == "/api/transactions":
                    raw_limit = query.get("limit", ["100"])[0]
                    try:
                        limit = int(raw_limit)
                    except ValueError as exc:
                        raise ValueError("limit must be an integer from 1 to 1000.") from exc
                    rows = list_transactions(conn, month or None, limit)
                    self._send_json(200, {"transactions": [dict(row) for row in rows]})
                elif parsed.path == "/api/budgets":
                    self._send_json(200, {"budgets": list_budgets(conn, month)})
                else:
                    self._json_error(404, "Route not found.")
        except ValueError as exc:
            self._json_error(400, str(exc))
        except (sqlite3.Error, OSError):
            self._json_error(500, "Database operation failed. Check the local database path and permissions.")

    def do_POST(self) -> None:  # noqa: N802 - HTTP handler API
        parsed = urlparse(self.path)
        if parsed.path not in ("/api/transactions", "/api/budgets"):
            self._json_error(404, "Route not found.")
            return

        try:
            payload = self._read_json()
            with connect() as conn:
                init_db(conn)
                if parsed.path == "/api/transactions":
                    kind = self._required_text(payload, "kind")
                    amount = self._required_amount(payload)
                    category = self._required_text(payload, "category")
                    note = payload.get("note", "")
                    if not isinstance(note, str):
                        raise ValueError("'note' must be a string.")
                    tx_date = payload.get("transaction_date")
                    if tx_date is not None and not isinstance(tx_date, str):
                        raise ValueError("'transaction_date' must be a YYYY-MM-DD string.")
                    tx_id = add_transaction(conn, kind, amount, category, note, tx_date)
                    self._send_json(201, {"ok": True, "id": tx_id})
                else:
                    month = self._required_text(payload, "month")
                    category = self._required_text(payload, "category")
                    amount = self._required_amount(payload)
                    set_budget(conn, month, category, amount)
                    self._send_json(200, {"ok": True})
        except OverflowError as exc:
            self._json_error(413, str(exc))
        except (ValueError, TypeError) as exc:
            self._json_error(400, str(exc))
        except (sqlite3.Error, OSError):
            self._json_error(500, "Database operation failed. Check the local database path and permissions.")

    def log_message(self, format: str, *args) -> None:
        # Keep the local dashboard quiet; users can inspect terminal errors if needed.
        return


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    """Create a server. The default is loopback-only; do not expose it to a public network."""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("For safety, bind only to a loopback address.")
    return ThreadingHTTPServer((host, port), FinanceRequestHandler)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Student Finance AI web dashboard locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Loopback address only (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port number (default: 8765)")
    args = parser.parse_args()
    try:
        server = make_server(args.host, args.port)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    with server:
        print(f"Student Finance AI is running at http://{args.host}:{server.server_port}")
        print("Data is stored in the same SQLite database used by finance.py.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping Student Finance AI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
