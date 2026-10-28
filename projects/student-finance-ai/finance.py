#!/usr/bin/env python3
"""Local-first student income and expense tracker (standard library only)."""
from __future__ import annotations
import argparse, os, sqlite3, sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DEFAULT_DB = "student_finance.db"

def db_path() -> Path:
    return Path(os.environ.get("STUDENT_FINANCE_DB", DEFAULT_DB)).expanduser()

def connect(path: Optional[Path] = None) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
      id INTEGER PRIMARY KEY AUTOINCREMENT, month TEXT NOT NULL,
      category TEXT NOT NULL, amount_vnd INTEGER NOT NULL CHECK (amount_vnd > 0),
      UNIQUE(month, category)
    );
    """)
    conn.commit()

def validate_month(value: str) -> str:
    try: datetime.strptime(value, "%Y-%m")
    except ValueError as exc: raise ValueError("Month must use YYYY-MM format.") from exc
    if len(value) != 7: raise ValueError("Month must use YYYY-MM format.")
    return value

def validate_date(value: str) -> str:
    try: return date.fromisoformat(value).isoformat()
    except ValueError as exc: raise ValueError("Date must use YYYY-MM-DD format.") from exc

def next_month(month: str) -> str:
    validate_month(month)
    year, mon = map(int, month.split("-"))
    return f"{year + 1:04d}-01" if mon == 12 else f"{year:04d}-{mon + 1:02d}"

def add_transaction(conn: sqlite3.Connection, kind: str, amount_vnd: int, category: str,
                    note: str = "", transaction_date: Optional[str] = None) -> int:
    if kind not in ("income", "expense"): raise ValueError("Type must be income or expense.")
    if isinstance(amount_vnd, bool) or amount_vnd <= 0: raise ValueError("Amount must be a positive integer number of VND.")
    if not category or not category.strip(): raise ValueError("Category cannot be empty.")
    tx_date = validate_date(transaction_date or date.today().isoformat())
    cur = conn.execute("INSERT INTO transactions(kind,amount_vnd,category,note,transaction_date) VALUES(?,?,?,?,?)",
                       (kind, amount_vnd, category.strip(), note.strip(), tx_date))
    conn.commit()
    return int(cur.lastrowid)

def list_transactions(conn: sqlite3.Connection, month: Optional[str] = None, limit: int = 100) -> list[sqlite3.Row]:
    if not 1 <= limit <= 1000: raise ValueError("Limit must be between 1 and 1000.")
    if month:
        validate_month(month)
        rows = conn.execute("SELECT id,kind,amount_vnd,category,note,transaction_date FROM transactions WHERE transaction_date >= ? AND transaction_date < ? ORDER BY transaction_date DESC,id DESC LIMIT ?",
                             (month + "-01", next_month(month) + "-01", limit))
    else:
        rows = conn.execute("SELECT id,kind,amount_vnd,category,note,transaction_date FROM transactions ORDER BY transaction_date DESC,id DESC LIMIT ?", (limit,))
    return list(rows.fetchall())

def monthly_summary(conn: sqlite3.Connection, month: str) -> dict:
    validate_month(month)
    row = conn.execute("SELECT COALESCE(SUM(CASE WHEN kind='income' THEN amount_vnd ELSE 0 END),0) income, COALESCE(SUM(CASE WHEN kind='expense' THEN amount_vnd ELSE 0 END),0) expenses, COUNT(*) count FROM transactions WHERE transaction_date >= ? AND transaction_date < ?",
                       (month + "-01", next_month(month) + "-01")).fetchone()
    cats = conn.execute("SELECT category,SUM(amount_vnd) total FROM transactions WHERE kind='expense' AND transaction_date >= ? AND transaction_date < ? GROUP BY category ORDER BY total DESC,category ASC",
                        (month + "-01", next_month(month) + "-01")).fetchall()
    income, expenses = int(row["income"]), int(row["expenses"])
    return {"month": month, "income_vnd": income, "expenses_vnd": expenses, "balance_vnd": income-expenses,
            "transaction_count": int(row["count"]), "expenses_by_category": [{"category": r["category"], "amount_vnd": int(r["total"])} for r in cats]}

def set_budget(conn: sqlite3.Connection, month: str, category: str, amount_vnd: int) -> None:
    validate_month(month)
    if not category or not category.strip(): raise ValueError("Category cannot be empty.")
    if isinstance(amount_vnd, bool) or amount_vnd <= 0: raise ValueError("Budget must be a positive integer number of VND.")
    conn.execute("INSERT INTO budgets(month,category,amount_vnd) VALUES(?,?,?) ON CONFLICT(month,category) DO UPDATE SET amount_vnd=excluded.amount_vnd",
                 (month, category.strip(), amount_vnd))
    conn.commit()

def list_budgets(conn: sqlite3.Connection, month: str) -> list[dict]:
    validate_month(month)
    rows = conn.execute("SELECT b.category,b.amount_vnd,COALESCE(SUM(t.amount_vnd),0) spent_vnd FROM budgets b LEFT JOIN transactions t ON t.category=b.category AND t.kind='expense' AND t.transaction_date >= b.month || '-01' AND t.transaction_date < ? WHERE b.month=? GROUP BY b.category,b.amount_vnd ORDER BY b.category",
                         (next_month(month) + "-01", month)).fetchall()
    return [{"category": r["category"], "budget_vnd": int(r["amount_vnd"]), "spent_vnd": int(r["spent_vnd"]), "remaining_vnd": int(r["amount_vnd"])-int(r["spent_vnd"])} for r in rows]

def money(value: int) -> str: return f"{value:,}".replace(",", ".") + " đ"

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Student Finance AI — local student budget tracker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create local SQLite database")
    add = sub.add_parser("add", help="Add income or expense")
    add.add_argument("--type", choices=("income","expense"), required=True); add.add_argument("--amount", type=int, required=True)
    add.add_argument("--category", required=True); add.add_argument("--note", default=""); add.add_argument("--date", dest="transaction_date")
    listing = sub.add_parser("list", help="List transactions"); listing.add_argument("--month"); listing.add_argument("--limit", type=int, default=100)
    summary = sub.add_parser("summary", help="Show monthly summary"); summary.add_argument("--month", default=date.today().strftime("%Y-%m"))
    budget = sub.add_parser("budget-set", help="Set category budget"); budget.add_argument("--month", required=True); budget.add_argument("--category", required=True); budget.add_argument("--amount", type=int, required=True)
    budgets = sub.add_parser("budgets", help="Compare budget with spending"); budgets.add_argument("--month", default=date.today().strftime("%Y-%m"))
    return parser

def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with connect() as conn:
            init_db(conn)
            if args.command == "init": print(f"Database ready: {db_path()}")
            elif args.command == "add":
                tx_id = add_transaction(conn,args.type,args.amount,args.category,args.note,args.transaction_date)
                print(f"Saved transaction #{tx_id}: {args.type} {money(args.amount)} [{args.category}]")
            elif args.command == "list":
                rows = list_transactions(conn,args.month,args.limit)
                if not rows: print("No transactions found.")
                for r in rows: print(f"#{r['id']} {r['transaction_date']} {r['kind']:7} {money(int(r['amount_vnd'])):>16}  {r['category']}  {r['note']}")
            elif args.command == "summary":
                r = monthly_summary(conn,args.month)
                print(f"Summary for {r['month']}\nIncome:       {money(r['income_vnd'])}\nExpenses:     {money(r['expenses_vnd'])}\nBalance:      {money(r['balance_vnd'])}\nTransactions: {r['transaction_count']}")
                for item in r["expenses_by_category"]: print(f"  {item['category']}: {money(item['amount_vnd'])}")
            elif args.command == "budget-set":
                set_budget(conn,args.month,args.category,args.amount); print(f"Budget saved: {args.month} {args.category} {money(args.amount)}")
            elif args.command == "budgets":
                rows = list_budgets(conn,args.month)
                if not rows: print("No budgets set for this month.")
                for r in rows: print(f"{r['category']}: budget {money(r['budget_vnd'])}, spent {money(r['spent_vnd'])}, remaining {money(r['remaining_vnd'])}")
        return 0
    except (ValueError, sqlite3.Error, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
