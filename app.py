# app.py
from flask import Flask, request, jsonify, render_template
from datetime import datetime
from calendar import monthrange
import os
import sqlite3
from werkzeug.utils import secure_filename

import database
from mpesa_charges import calculate_mpesa_charge
from sms_parser import parse_mpesa_message
from financial_agent import FinancialAgent
from pdf_parser import parse_mpesa_statement_pdf

# --- Configuration ---
# This can eventually be loaded from a config file or database.
BUDGETED_AMOUNTS = {
    'Rent (Incl. Utilities)': 10000,
    'Food': 11000,
    'Mobile Data/Airtime': 1000,
    'Bike Maintenance/Transport': 1000,
    'Personal Care & Misc.': 4500,
    'Discretionary/Flex': 2000,
    'Contingency': 500,
    'Savings Fund': 10000,
    'Investment (e.g., Sacco)': 0
}

app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

database.init_db() # Initialize the database when the app starts
agent = FinancialAgent(BUDGETED_AMOUNTS) # Initialize the financial agent

# --- HTML Rendering Routes ---

@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/add-expense')
def add_expense_page():
    """Serves the page for adding a new expense."""
    categories = sorted(list(BUDGETED_AMOUNTS.keys()) + ['Other'])
    return render_template('add_expense.html', categories=categories)

@app.route('/view-expenses')
def view_expenses_page():
    """Serves the page for viewing all expenses."""
    return render_template('view_expenses.html')

# --- API Endpoints ---

@app.route('/api/expenses', methods=['POST'])
def add_expense_api():
    """API endpoint to add a new expense."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    # Basic validation
    required_fields = ['date', 'description', 'category', 'amount', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        amount = float(data['amount'])
        mpesa_charge = float(data.get('mpesa_charge', 0.0))
        # Get transaction_id, default to None if not present
        transaction_id = data.get('transaction_id') or None
        
        database.add_expense(
            date=data['date'],
            description=data['description'],
            category=data['category'],
            amount=amount,
            payment_method=data['payment_method'],
            mpesa_charge=mpesa_charge,
            transaction_id=transaction_id # Pass it to the database function
        )
        return jsonify({"message": "Expense added successfully!"}), 201
    except sqlite3.IntegrityError:
        # This error is raised when the UNIQUE constraint on transaction_id fails
        return jsonify({"error": f"Duplicate transaction: An expense with ID '{transaction_id}' already exists."}), 409 # 409 Conflict
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid data format: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@app.route('/api/expenses', methods=['GET'])
def get_expenses_api():
    """API endpoint to retrieve expenses with optional filters."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 15, type=int)

    expenses_data, total_records = database.get_expenses(
        start_date=start_date, end_date=end_date, category=category or None, page=page, limit=limit
    )
    
    # Convert list of Row objects to list of dicts
    expenses_list = [dict(row) for row in expenses_data]

    return jsonify({
        "expenses": expenses_list,
        "page": page,
        "limit": limit,
        "total_records": total_records
    })


@app.route('/api/summary', methods=['GET'])
def get_summary_api():
    """API endpoint for monthly summary by category."""
    year_month = request.args.get('year_month', datetime.now().strftime("%Y-%m"))
    
    try:
        year, month = map(int, year_month.split('-'))
        start_date = f"{year_month}-01"
        days_in_month = monthrange(year, month)[1]
        end_date = f"{year_month}-{days_in_month:02d}"
    except ValueError:
        return jsonify({"error": "Invalid year_month format. Use YYYY-MM."}), 400

    summary_data = database.get_summary_by_category(start_date, end_date) # This will now return dict-like rows
    
    # Convert list of Row objects to list of dicts
    summary_list = [dict(row) for row in summary_data]

    # Combine with budget for a more comprehensive view
    combined_summary = []
    spent_categories = {item['category'] for item in summary_list}

    for item in summary_list:
        budget = BUDGETED_AMOUNTS.get(item['category'], 0)
        item['budgeted'] = float(budget)
        item['remaining'] = float(budget - item['total_spent']) if budget > 0 else 0.0
        combined_summary.append(item)

    # Add budgeted categories that have no spending yet
    for category, budget in BUDGETED_AMOUNTS.items():
        if category not in spent_categories and budget > 0:
            combined_summary.append({
                'category': category,
                'total_spent': 0.0,
                'budgeted': float(budget),
                'remaining': float(budget)
            })

    # Calculate totals
    total_spent = sum(item['total_spent'] for item in summary_list)
    total_budgeted = sum(float(b) for b in BUDGETED_AMOUNTS.values())

    return jsonify({"summary": combined_summary, "totals": {"spent": total_spent, "budgeted": total_budgeted, "remaining": total_budgeted - total_spent}})

@app.route('/api/parse-sms', methods=['POST'])
def parse_sms_api():
    """API endpoint to parse an M-Pesa SMS."""
    data = request.get_json()
    if not data or 'sms_message' not in data:
        return jsonify({"error": "Missing 'sms_message' in request"}), 400
    
    parsed_data = parse_mpesa_message(data['sms_message'])
    
    if parsed_data:
        # Suggest a category to help the user
        description_lower = parsed_data.get('description', '').lower()
        business_lower = parsed_data.get('business', '').lower()
        
        if "airtime" in description_lower:
            parsed_data['suggested_category'] = "Mobile Data/Airtime"
        elif "withdrawal" in description_lower or "agent" in description_lower:
            parsed_data['suggested_category'] = "Contingency"
        elif business_lower in ['kplc', 'zuku', 'safaricom home']:
            parsed_data['suggested_category'] = "Rent (Incl. Utilities)"
        else:
            # A common default for other payments
            parsed_data['suggested_category'] = "Food" 
        
        return jsonify(parsed_data)
    else:
        return jsonify({"error": "Could not parse SMS message"}), 400

@app.route('/api/insights', methods=['GET'])
def get_insights_api():
    """API endpoint to get financial insights."""
    try:
        insights = agent.analyze_current_month()
        return jsonify({"insights": insights})
    except Exception as e:
        # In a real app, you'd log this error
        print(f"Error generating insights: {e}")
        return jsonify({"error": "Failed to generate financial insights."}), 500

@app.route('/api/total-mpesa-charges', methods=['GET'])
def get_total_mpesa_charges_api():
    """API endpoint to get total M-Pesa charges for a period."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    try:
        total_charges = database.get_total_mpesa_charges(start_date, end_date)
        return jsonify({"total_mpesa_charges": total_charges})
    except Exception as e:
        # In a real app, you'd log this error
        print(f"Error getting total mpesa charges: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/parse-pdf', methods=['POST'])
def parse_pdf_api():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            transactions = parse_mpesa_statement_pdf(filepath)
            return jsonify({"transactions": transactions})
        except Exception as e:
            return jsonify({"error": f"Failed to parse PDF: {e}"}), 500
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

    return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    # Use debug=True for development, which enables auto-reloading
    app.run(debug=True)