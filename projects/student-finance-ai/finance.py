#!/usr/bin/env python3
"""Local-first student income and expense tracker (standard library only)."""
from __future__ import annotations

import argparse
import csv
import io
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DEFAULT_DB = str(Path.home() / ".student-finance" / "student_finance.db")
MAX_AMOUNT_VND = 9_000_000_000_000_000_000
MAX_CATEGORY_LENGTH = 80
MAX_NOTE_LENGTH = 500
CSV_REQUIRED_COLUMNS = {"transaction_date", "kind", "amount_vnd", "category", "note"}


def db_path() -> Path:
    return Path(os.environ.get("STUDENT_FINANCE_DB", DEFAULT_DB)).expanduser()


def connect(path: Optional[Path] = None) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kind TEXT NOT NULL CHECK (kind IN ('income','expense')),
      amount_vnd INTEGER NOT NULL CHECK (amount_vnd > 0),
      category TEXT NOT NULL CHECK (length(trim(category)) > 0),
      note TEXT NOT NULL DEFAULT '', transaction_date TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
    CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
    CREATE TABLE IF NOT EXISTS budgets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      month TEXT NOT NULL,
      category TEXT NOT NULL,
      amount_vnd INTEGER NOT NULL CHECK (amount_vnd > 0),
      UNIQUE(month, category)
    );
    """)
    conn.commit()


def validate_month(value: str) -> str:
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        raise ValueError("Month must use YYYY-MM format.")
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise ValueError("Month must use YYYY-MM format.") from exc
    return value


def validate_date(value: str) -> str:
    if not isinstance(value, str) or len(value) != 10 or value[4:5] != "-" or value[7:8] != "-":
        raise ValueError("Date must use YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format.") from exc


def next_month(month: str) -> str:
    validate_month(month)
    year, mon = map(int, month.split("-"))
    return f"{year + 1:04d}-01" if mon == 12 else f"{year:04d}-{mon + 1:02d}"


def _validate_transaction(kind: str, amount_vnd: int, category: str,
                          note: str = "", transaction_date: Optional[str] = None) -> tuple[str, int, str, str, str]:
    if kind not in ("income", "expense"):
        raise ValueError("Type must be income or expense.")
    if type(amount_vnd) is not int or not 0 < amount_vnd <= MAX_AMOUNT_VND:
        raise ValueError("Amount must be a positive integer number of VND.")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category cannot be empty.")
    clean_category = category.strip()
    if len(clean_category) > MAX_CATEGORY_LENGTH:
        raise ValueError(f"Category cannot exceed {MAX_CATEGORY_LENGTH} characters.")
    if not isinstance(note, str):
        raise ValueError("Note must be a string.")
    clean_note = note.strip()
    if len(clean_note) > MAX_NOTE_LENGTH:
        raise ValueError(f"Note cannot exceed {MAX_NOTE_LENGTH} characters.")
    tx_date = validate_date(transaction_date or date.today().isoformat())
    return kind, amount_vnd, clean_category, clean_note, tx_date


def add_transaction(conn: sqlite3.Connection, kind: str, amount_vnd: int, category: str,
                    note: str = "", transaction_date: Optional[str] = None) -> int:
    kind, amount_vnd, category, note, tx_date = _validate_transaction(
        kind, amount_vnd, category, note, transaction_date
    )
    cur = conn.execute(
        "INSERT INTO transactions(kind,amount_vnd,category,note,transaction_date) VALUES(?,?,?,?,?)",
        (kind, amount_vnd, category, note, tx_date),
    )
    conn.commit()
    return int(cur.lastrowid)


def get_transaction(conn: sqlite3.Connection, transaction_id: int) -> Optional[dict]:
    if type(transaction_id) is not int or transaction_id <= 0:
        raise ValueError("Transaction ID must be a positive integer.")
    row = conn.execute(
        "SELECT id,kind,amount_vnd,category,note,transaction_date FROM transactions WHERE id=?",
        (transaction_id,),
    ).fetchone()
    return dict(row) if row else None


def update_transaction(conn: sqlite3.Connection, transaction_id: int, kind: str,
                       amount_vnd: int, category: str, note: str = "",
                       transaction_date: Optional[str] = None) -> bool:
    if type(transaction_id) is not int or transaction_id <= 0:
        raise ValueError("Transaction ID must be a positive integer.")
    kind, amount_vnd, category, note, tx_date = _validate_transaction(
        kind, amount_vnd, category, note, transaction_date
    )
    cur = conn.execute(
        """UPDATE transactions
           SET kind=?, amount_vnd=?, category=?, note=?, transaction_date=?
           WHERE id=?""",
        (kind, amount_vnd, category, note, tx_date, transaction_id),
    )
    conn.commit()
    return cur.rowcount == 1


def delete_transaction(conn: sqlite3.Connection, transaction_id: int) -> bool:
    if type(transaction_id) is not int or transaction_id <= 0:
        raise ValueError("Transaction ID must be a positive integer.")
    cur = conn.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
    conn.commit()
    return cur.rowcount == 1


def list_transactions(conn: sqlite3.Connection, month: Optional[str] = None, limit: int = 100,
                      search: Optional[str] = None, kind: Optional[str] = None,
                      category: Optional[str] = None) -> list[sqlite3.Row]:
    if not 1 <= limit <= 1000:
        raise ValueError("Limit must be between 1 and 1000.")
    clauses: list[str] = []
    params: list[object] = []
    if month:
        validate_month(month)
        clauses.extend(["transaction_date >= ?", "transaction_date < ?"])
        params.extend([month + "-01", next_month(month) + "-01"])
    if kind:
        if kind not in ("income", "expense"):
            raise ValueError("Type must be income or expense.")
        clauses.append("kind = ?")
        params.append(kind)
    if category:
        clauses.append("category = ?")
        params.append(category.strip())
    if search and search.strip():
        clauses.append("(category LIKE ? ESCAPE '\\' OR note LIKE ? ESCAPE '\\')")
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params.extend([f"%{escaped}%", f"%{escaped}%"])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    return list(conn.execute(
        "SELECT id,kind,amount_vnd,category,note,transaction_date FROM transactions"
        + where + " ORDER BY transaction_date DESC,id DESC LIMIT ?",
        params,
    ).fetchall())


def all_transactions_for_month(conn: sqlite3.Connection, month: str) -> list[sqlite3.Row]:
    validate_month(month)
    return list(conn.execute(
        """SELECT id,kind,amount_vnd,category,note,transaction_date
           FROM transactions WHERE transaction_date >= ? AND transaction_date < ?
           ORDER BY transaction_date ASC,id ASC""",
        (month + "-01", next_month(month) + "-01"),
    ).fetchall())


def list_categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """SELECT category FROM transactions
           UNION SELECT category FROM budgets
           ORDER BY category COLLATE NOCASE"""
    ).fetchall()
    return [str(row[0]) for row in rows]


def monthly_summary(conn: sqlite3.Connection, month: str) -> dict:
    validate_month(month)
    row = conn.execute(
        """SELECT
             COALESCE(SUM(CASE WHEN kind='income' THEN amount_vnd ELSE 0 END),0) income,
             COALESCE(SUM(CASE WHEN kind='expense' THEN amount_vnd ELSE 0 END),0) expenses,
             COUNT(*) count
           FROM transactions WHERE transaction_date >= ? AND transaction_date < ?""",
        (month + "-01", next_month(month) + "-01"),
    ).fetchone()
    cats = conn.execute(
        """SELECT category,SUM(amount_vnd) total FROM transactions
           WHERE kind='expense' AND transaction_date >= ? AND transaction_date < ?
           GROUP BY category ORDER BY total DESC,category ASC""",
        (month + "-01", next_month(month) + "-01"),
    ).fetchall()
    income, expenses = int(row["income"]), int(row["expenses"])
    return {
        "month": month,
        "income_vnd": income,
        "expenses_vnd": expenses,
        "balance_vnd": income - expenses,
        "transaction_count": int(row["count"]),
        "expenses_by_category": [
            {"category": r["category"], "amount_vnd": int(r["total"])} for r in cats
        ],
    }


def set_budget(conn: sqlite3.Connection, month: str, category: str, amount_vnd: int) -> None:
    validate_month(month)
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category cannot be empty.")
    category = category.strip()
    if len(category) > MAX_CATEGORY_LENGTH:
        raise ValueError(f"Category cannot exceed {MAX_CATEGORY_LENGTH} characters.")
    if type(amount_vnd) is not int or not 0 < amount_vnd <= MAX_AMOUNT_VND:
        raise ValueError("Budget must be a positive integer number of VND.")
    conn.execute(
        """INSERT INTO budgets(month,category,amount_vnd) VALUES(?,?,?)
           ON CONFLICT(month,category) DO UPDATE SET amount_vnd=excluded.amount_vnd""",
        (month, category, amount_vnd),
    )
    conn.commit()


def delete_budget(conn: sqlite3.Connection, month: str, category: str) -> bool:
    validate_month(month)
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category cannot be empty.")
    cur = conn.execute("DELETE FROM budgets WHERE month=? AND category=?", (month, category.strip()))
    conn.commit()
    return cur.rowcount == 1


def list_budgets(conn: sqlite3.Connection, month: str) -> list[dict]:
    validate_month(month)
    rows = conn.execute(
        """SELECT b.category,b.amount_vnd,
                  COALESCE(SUM(t.amount_vnd),0) spent_vnd
           FROM budgets b
           LEFT JOIN transactions t
             ON t.category=b.category AND t.kind='expense'
             AND t.transaction_date >= b.month || '-01'
             AND t.transaction_date < ?
           WHERE b.month=?
           GROUP BY b.category,b.amount_vnd
           ORDER BY b.category COLLATE NOCASE""",
        (next_month(month) + "-01", month),
    ).fetchall()
    return [
        {
            "category": r["category"],
            "budget_vnd": int(r["amount_vnd"]),
            "spent_vnd": int(r["spent_vnd"]),
            "remaining_vnd": int(r["amount_vnd"]) - int(r["spent_vnd"]),
        }
        for r in rows
    ]


def import_transactions_csv(conn: sqlite3.Connection, content: str, max_records: int = 5000) -> int:
    """Validate every CSV row before inserting any records, so imports are all-or-nothing."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("CSV file is empty.")
    try:
        reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff"), newline=""))
        headers = {str(name).strip() for name in (reader.fieldnames or []) if name is not None}
        if not CSV_REQUIRED_COLUMNS.issubset(headers):
            required = ", ".join(sorted(CSV_REQUIRED_COLUMNS))
            raise ValueError(f"CSV must include these columns: {required}.")
        records: list[tuple[str, int, str, str, str]] = []
        for line_number, row in enumerate(reader, start=2):
            if line_number > max_records + 1:
                raise ValueError(f"CSV cannot contain more than {max_records} transactions.")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row at line {line_number}.")
            raw_amount = (row.get("amount_vnd") or "").strip()
            if not raw_amount.isdigit():
                raise ValueError(f"amount_vnd must be a positive integer at line {line_number}.")
            try:
                record = _validate_transaction(
                    (row.get("kind") or "").strip(),
                    int(raw_amount),
                    row.get("category") or "",
                    row.get("note") or "",
                    (row.get("transaction_date") or "").strip(),
                )
            except ValueError as exc:
                raise ValueError(f"Line {line_number}: {exc}") from exc
            records.append(record)
        if not records:
            raise ValueError("CSV contains no transaction rows.")
    except csv.Error as exc:
        raise ValueError(f"Invalid CSV file: {exc}") from exc

    try:
        conn.executemany(
            """INSERT INTO transactions(kind,amount_vnd,category,note,transaction_date)
               VALUES(?,?,?,?,?)""",
            records,
        )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    return len(records)


def money(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " đ"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Student Finance AI — local student budget tracker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create local SQLite database")
    add = sub.add_parser("add", help="Add income or expense")
    add.add_argument("--type", choices=("income", "expense"), required=True)
    add.add_argument("--amount", type=int, required=True)
    add.add_argument("--category", required=True)
    add.add_argument("--note", default="")
    add.add_argument("--date", dest="transaction_date")
    listing = sub.add_parser("list", help="List transactions")
    listing.add_argument("--month")
    listing.add_argument("--limit", type=int, default=100)
    summary = sub.add_parser("summary", help="Show monthly summary")
    summary.add_argument("--month", default=date.today().strftime("%Y-%m"))
    budget = sub.add_parser("budget-set", help="Set category budget")
    budget.add_argument("--month", required=True)
    budget.add_argument("--category", required=True)
    budget.add_argument("--amount", type=int, required=True)
    budgets = sub.add_parser("budgets", help="Compare budget with spending")
    budgets.add_argument("--month", default=date.today().strftime("%Y-%m"))
    update = sub.add_parser("update", help="Update an existing transaction")
    update.add_argument("--id", type=int, required=True)
    update.add_argument("--type", choices=("income", "expense"), required=True)
    update.add_argument("--amount", type=int, required=True)
    update.add_argument("--category", required=True)
    update.add_argument("--note", default="")
    update.add_argument("--date", dest="transaction_date")
    delete = sub.add_parser("delete", help="Delete an existing transaction")
    delete.add_argument("--id", type=int, required=True)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with connect() as conn:
            init_db(conn)
            if args.command == "init":
                print(f"Database ready: {db_path()}")
            elif args.command == "add":
                tx_id = add_transaction(conn, args.type, args.amount, args.category, args.note, args.transaction_date)
                print(f"Saved transaction #{tx_id}: {args.type} {money(args.amount)} [{args.category}]")
            elif args.command == "list":
                rows = list_transactions(conn, args.month, args.limit)
                if not rows:
                    print("No transactions found.")
                for r in rows:
                    print(f"#{r['id']} {r['transaction_date']} {r['kind']:7} {money(int(r['amount_vnd'])):>16}  {r['category']}  {r['note']}")
            elif args.command == "summary":
                result = monthly_summary(conn, args.month)
                print(f"Summary for {result['month']}\nIncome:       {money(result['income_vnd'])}\nExpenses:     {money(result['expenses_vnd'])}\nBalance:      {money(result['balance_vnd'])}\nTransactions: {result['transaction_count']}")
                for item in result["expenses_by_category"]:
                    print(f"  {item['category']}: {money(item['amount_vnd'])}")
            elif args.command == "budget-set":
                set_budget(conn, args.month, args.category, args.amount)
                print(f"Budget saved: {args.month} {args.category} {money(args.amount)}")
            elif args.command == "budgets":
                rows = list_budgets(conn, args.month)
                if not rows:
                    print("No budgets set for this month.")
                for r in rows:
                    print(f"{r['category']}: budget {money(r['budget_vnd'])}, spent {money(r['spent_vnd'])}, remaining {money(r['remaining_vnd'])}")
            elif args.command == "update":
                if update_transaction(conn, args.id, args.type, args.amount, args.category, args.note, args.transaction_date):
                    print(f"Updated transaction #{args.id}.")
                else:
                    print(f"Transaction #{args.id} not found.", file=sys.stderr)
                    return 1
            elif args.command == "delete":
                if delete_transaction(conn, args.id):
                    print(f"Deleted transaction #{args.id}.")
                else:
                    print(f"Transaction #{args.id} not found.", file=sys.stderr)
                    return 1
        return 0
    except (ValueError, sqlite3.Error, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
