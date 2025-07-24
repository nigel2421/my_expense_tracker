# database.py
import sqlite3
from datetime import datetime

DB_NAME = 'expenses.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and table schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_id TEXT UNIQUE, -- Ensures no duplicate M-Pesa codes
            payment_method TEXT NOT NULL,
            mpesa_charge REAL DEFAULT 0.0,
            total_outflow REAL GENERATED ALWAYS AS (amount + mpesa_charge) VIRTUAL
        );
    ''')
    # Add transaction_id column if it doesn't exist (for migration)
    try:
        cursor.execute("SELECT transaction_id FROM expenses LIMIT 1;")
    except sqlite3.OperationalError:
        # Cannot add a UNIQUE constraint directly with ALTER TABLE in older SQLite
        # Add the column first, then create a unique index on it.
        cursor.execute("ALTER TABLE expenses ADD COLUMN transaction_id TEXT;")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_transaction_id ON expenses (transaction_id);")
        conn.commit()
    conn.close()

def add_expense(date, description, category, amount, payment_method, mpesa_charge, transaction_id=None):
    """Adds a new expense to the database, preventing duplicates by transaction_id."""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO expenses (date, description, category, amount, payment_method, mpesa_charge, transaction_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (date, description, category, amount, payment_method, mpesa_charge, transaction_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_expenses(start_date=None, end_date=None, category=None, page=1, limit=15):
    """Retrieves a paginated list of expenses."""
    conn = get_db_connection()
    query = 'SELECT * FROM expenses WHERE 1=1'
    params = []

    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if category:
        query += ' AND category = ?'
        params.append(category)

    count_query = query.replace('SELECT *', 'SELECT COUNT(id)')
    total_records = conn.execute(count_query, tuple(params)).fetchone()[0]

    query += ' ORDER BY date DESC, id DESC LIMIT ? OFFSET ?'
    params.extend([limit, (page - 1) * limit])

    expenses = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return expenses, total_records

def get_summary_by_category(start_date, end_date):
    """Retrieves a summary of expenses grouped by category."""
    conn = get_db_connection()
    summary = conn.execute('''
        SELECT category, SUM(amount) as total_spent
        FROM expenses WHERE date BETWEEN ? AND ?
        GROUP BY category ORDER BY total_spent DESC
    ''', (start_date, end_date)).fetchall()
    conn.close()
    return summary

def get_total_mpesa_charges(start_date=None, end_date=None):
    """Calculates the total M-Pesa charges for a given period."""
    conn = get_db_connection()
    query = 'SELECT SUM(mpesa_charge) FROM expenses WHERE payment_method = "MPESA"'
    # ... (rest of the function logic)
    total = conn.execute(query, ()).fetchone()[0]
    conn.close()
    return total or 0.0