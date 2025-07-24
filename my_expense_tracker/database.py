# database.py
import sqlite3
from datetime import datetime

DATABASE_NAME = 'expenses.db'

def init_db():
    """Initializes the SQLite database and creates the expenses table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, description TEXT, category TEXT NOT NULL, amount REAL NOT NULL, payment_method TEXT NOT NULL, mpesa_charge REAL DEFAULT 0.0, total_outflow REAL NOT NULL)
    """)
    conn.commit()
    conn.close()
    # print(f"Database '{DATABASE_NAME}' initialized.") # Uncomment for debugging

def add_expense(date: str, description: str, category: str, amount: float, payment_method: str, mpesa_charge: float):
    """Adds a new expense record to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    total_outflow = amount + mpesa_charge
    cursor.execute('''
        INSERT INTO expenses (date, description, category, amount, payment_method, mpesa_charge, total_outflow)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, description, category, amount, payment_method, mpesa_charge, total_outflow))
    conn.commit()
    conn.close()
    print("Expense added successfully!")

from typing import Optional, Tuple

def get_expenses(start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None, page: int = 1, limit: int = 15) -> Tuple[list, int]:
    """Retrieves expenses from the database, with optional date and category filters."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Return rows that can be accessed by column name
    cursor = conn.cursor()
    
    # Base query for filtering
    base_query = "FROM expenses WHERE 1=1"
    params = []

    if start_date:
        base_query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        base_query += " AND date <= ?"
        params.append(end_date)
    if category:
        base_query += " AND category = ?"
        params.append(category)

    # Get total count for pagination
    count_query = f"SELECT COUNT(id) {base_query}"
    cursor.execute(count_query, params)
    total_records = cursor.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * limit
    query = f"SELECT date, description, category, amount, payment_method, mpesa_charge, total_outflow {base_query} ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
    
    # Add limit and offset to params for the main query
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows, total_records

from typing import Optional

def get_summary_by_category(start_date: Optional[str] = None, end_date: Optional[str] = None) -> list:
    """Calculates total spending per category for a given date range."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Return rows that can be accessed by column name
    cursor = conn.cursor()
    query = """
        SELECT category, SUM(total_outflow) as total_spent
        FROM expenses 
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " GROUP BY category ORDER BY total_spent DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

from typing import Optional

def get_total_mpesa_charges(start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
    """Calculates the sum of M-Pesa charges for a given date range."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT SUM(mpesa_charge) FROM expenses WHERE 1=1"
    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0.0

    

# You can add more database functions here:
# - update_expense(id, new_data)
# - delete_expense(id)
# - get_expenses_by_month(year, month) - useful for specific monthly reports