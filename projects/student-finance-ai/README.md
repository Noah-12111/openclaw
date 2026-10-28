# Student Finance AI — SpendWise

A privacy-conscious personal income and expense tracker designed for students. This runnable MVP is intended to become an OpenClaw-powered assistant.

## Features
- Record income and expenses with date, category, integer VND amount, and note.
- Store data in local SQLite.
- List transactions; calculate monthly income, expenses, and balance.
- Set and inspect monthly category budgets.
- Keep calculations deterministic in Python; AI should interpret requests, not invent totals.

## Requirements
Python 3.10+. No third-party packages required.

## Quick start

```bash
python finance.py init
python finance.py add --type expense --amount 25000 --category food --note "Breakfast"
python finance.py add --type income --amount 1500000 --category allowance --note "Monthly allowance"
python finance.py list
python finance.py summary --month 2026-10
python finance.py budget-set --month 2026-10 --category food --amount 900000
python finance.py budgets --month 2026-10
```

The database defaults to `./student_finance.db`. Set `STUDENT_FINANCE_DB` to choose another location and use that same variable for subsequent commands.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Data model
- `transactions`: kind (`income` or `expense`), positive integer VND amount, category, note, ISO date.
- `budgets`: month (`YYYY-MM`), category, positive integer VND limit.

## OpenClaw integration plan
`SKILL.md` describes assistant behavior and intended tool contract. The Python CLI is the deterministic business-logic MVP; it is not yet registered as an OpenClaw plugin. Next, expose validated tools such as `add_transaction`, `list_transactions`, `get_monthly_summary`, and `set_budget` through a version-pinned plugin or local adapter.

## Privacy and safety
- Data stays in the local SQLite file unless explicitly exported or transmitted.
- Never store bank passwords, authentication codes, or full payment-card details.
- Back up the database securely.
- Confirm ambiguous amounts/dates before saving through a future AI interface.
- Do not allow a model to execute arbitrary SQL; validate arguments and use parameterized SQL.
- This is a budgeting aid, not financial, tax, or investment advice.

## Limitations
No bank connection, automatic payment, web dashboard, or scheduled notifications. Categories are user-supplied; automatic natural-language categorization belongs to future OpenClaw integration. Edit/delete commands are not implemented yet.
