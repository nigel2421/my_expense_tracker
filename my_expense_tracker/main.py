# main.py
from datetime import datetime
import database
from mpesa_charges import calculate_mpesa_charge
from sms_parser import parse_mpesa_message
from financial_agent import FinancialAgent

# --- Configuration ---
# Define your budgeted amounts. This can eventually be loaded from a config file or database.
BUDGETED_AMOUNTS = {
    'Rent (Incl. Utilities)': 10000,
    'Food': 11000,
    'Mobile Data/Airtime': 1000,
    'Bike Maintenance/Transport': 1000,
    'Personal Care & Misc.': 4500,
    'Discretionary/Flex': 2000,
    'Contingency': 500,
    'Savings Fund': 10000,
    'Investment (e.g., Sacco)': 0 # Assuming 0 for now, but you can set a target
}

# --- CLI Menu Functions ---

def display_menu():
    """Displays the main menu options to the user."""
    print("\n--- Expense Tracker Menu ---")
    print("1. Add New Expense")
    print("2. View All Expenses")
    print("3. View Expenses by Category")
    print("4. View Monthly Summary")
    print("5. Total M-Pesa Charges")
    print("6. Get Financial Insights & Suggestions")
    print("7. Exit")

def add_expense_flow():
    """Guides the user through adding a new expense, including SMS parsing."""
    print("\n--- Add New Expense ---")
    
    parsed_data = None
    use_sms = input("Do you want to paste an M-Pesa SMS message for auto-detection? (y/n, default n): ")
    
    if use_sms.lower() == 'y':
        sms_message = input("Paste your M-Pesa SMS message here:\n")
        parsed_data = parse_mpesa_message(sms_message)
        
        if parsed_data:
            print("\n--- SMS Parsed Successfully! ---")
            print(f"Type: {parsed_data.get('type')}")
            print(f"Amount: Ksh {parsed_data.get('amount'):.2f}")
            print(f"Date: {parsed_data.get('date')}")
            print(f"Description: {parsed_data.get('description')}")
            print(f"Transaction Cost: Ksh {parsed_data.get('transaction_cost'):.2f}")
            
            confirm = input("Use this parsed data? (y/n, default y): ") or 'y'
            if confirm.lower() == 'n':
                parsed_data = None # User wants to enter manually
        else:
            print("Could not parse M-Pesa message. Please enter details manually.")

    # --- Expense Data Input (Manual or Pre-filled from SMS) ---
    
    date = parsed_data.get('date') if parsed_data else input("Enter date (YYYY-MM-DD, leave blank for today): ")
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    description = parsed_data.get('description') if parsed_data else input("Enter description: ")
    
    # Suggest a category based on SMS type, or ask for manual
    suggested_category = ""
    if parsed_data and parsed_data.get('type') in ["Sent", "Pay Bill/Buy Goods", "Airtime Purchase", "Withdrawal"]:
        if "airtime" in parsed_data.get('description', '').lower():
            suggested_category = "Mobile Data/Airtime"
        elif "withdrawal" in parsed_data.get('description', '').lower() or "agent" in parsed_data.get('description', '').lower():
            suggested_category = "Contingency" # Or create a "Cash Withdrawal" category
        elif parsed_data.get('business', '').lower() in ['kplc', 'zuku', 'safaricom home']: # Add common billers
             suggested_category = "Rent (Incl. Utilities)" # If part of your bundled utility or specific biller
        else: # Default for other sent/paid transactions
            suggested_category = "Food" # A common general expense
        
    category = input(f"Enter category (e.g., Food, Transport, Personal Care) [{suggested_category}]: ") or suggested_category
    
    while True:
        try:
            amount_str = str(parsed_data.get('amount')) if parsed_data else input("Enter amount: ")
            amount = float(amount_str)
            if amount < 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid amount. Please enter a positive number.")

    payment_method = parsed_data.get('payment_method', 'MPESA') if parsed_data and parsed_data.get('type') in ["Sent", "Pay Bill/Buy Goods", "Withdrawal", "Airtime Purchase"] else input("Enter payment method (e.g., MPESA, Cash, Bank Transfer): ")

    mpesa_charge = parsed_data.get('transaction_cost', 0.0) if parsed_data else 0.0
    
    # Calculate charge only if MPESA and not already parsed from SMS
    if payment_method.upper() == 'MPESA' and not parsed_data: 
        mpesa_type = input("Is this a 'P2P' (person-to-person) transfer or 'WITHDRAWAL'? (P2P/WITHDRAWAL, default P2P): ") or 'P2P'
        mpesa_charge = calculate_mpesa_charge(amount, mpesa_type)
        print(f"Calculated M-Pesa charge: Ksh {mpesa_charge:.2f}")
        confirm_charge = input("Confirm M-Pesa charge (y/n, default y): ") or 'y'
        if confirm_charge.lower() == 'n':
            try:
                mpesa_charge = float(input("Enter actual M-Pesa charge if different: "))
            except ValueError:
                print("Invalid input, using calculated charge.")
    elif payment_method.upper() != 'MPESA':
        mpesa_charge = 0.0 # Ensure charge is zero for non-MPESA methods

    database.add_expense(date, description if description is not None else "", category, amount, payment_method, mpesa_charge)

def view_expenses_flow():
    """Allows viewing expenses with optional filters."""
    start_date = input("Enter start date (YYYY-MM-DD, optional): ") or None
    end_date = input("Enter end date (YYYY-MM-DD, optional): ") or None
    category = input("Enter category to filter by (optional): ") or ""

    expenses = database.get_expenses(start_date=start_date, end_date=end_date, category=category)
    if not expenses:
        print("No expenses found for the given criteria.")
        return

    print("\n--- Your Expenses ---")
    print(f"{'Date':<12} {'Category':<15} {'Amount':<10} {'Charge':<8} {'Total':<10} {'Payment':<10} {'Description':<25}")
    print("-" * 100)
    for exp in expenses:
        # Assuming exp is (date, description, category, amount, payment_method, mpesa_charge, total_outflow)
        print(f"{exp[0]:<12} {exp[2]:<15} {exp[3]:<10.2f} {exp[5]:<8.2f} {exp[6]:<10.2f} {exp[4]:<10} {exp[1]:<25}")
    print("-" * 100)

def view_monthly_summary_flow():
    """Displays a summary of spending by category for a selected month."""
    year_month = input("Enter year and month (YYYY-MM, e.g., 2025-07, leave blank for current month): ")
    if not year_month:
        year_month = datetime.now().strftime("%Y-%m")
    
    start_date = f"{year_month}-01"
    # Calculate end date for the month
    from calendar import monthrange
    try:
        days_in_month = monthrange(int(year_month[:4]), int(year_month[5:]))[1]
        end_date = f"{year_month}-{days_in_month:02d}"
    except ValueError:
        print("Invalid month format. Using current month's end date.")
        end_date = datetime.now().strftime("%Y-%m-%d")


    summary = database.get_summary_by_category(start_date, end_date)
    total_spent = sum(item[1] for item in summary) if summary else 0

    print(f"\n--- Monthly Summary for {year_month} ---")
    print(f"{'Category':<20} {'Total Spent (Ksh)':<20}")
    print("-" * 40)
    if summary:
        for cat, total in summary:
            print(f"{cat:<20} {total:<20.2f}")
    else:
        print("No spending recorded for this month.")
    print("-" * 40)
    print(f"{'GRAND TOTAL':<20} {total_spent:<20.2f}")

def total_mpesa_charges_flow():
    """Calculates and displays total M-Pesa charges for a period."""
    start_date = input("Enter start date (YYYY-MM-DD, optional): ") or None
    end_date = input("Enter end date (YYYY-MM-DD, optional): ") or None
    total_charges = database.get_total_mpesa_charges(start_date, end_date)
    print(f"\nTotal M-Pesa charges between {start_date or 'beginning'} and {end_date or 'today'}: Ksh {total_charges:.2f}")


def main():
    """Main function to run the expense tracker application."""
    database.init_db() # Initialize the database
    agent = FinancialAgent(budgeted_amounts=BUDGETED_AMOUNTS) # Initialize the financial agent

    while True:
        display_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            add_expense_flow()
        elif choice == '2':
            view_expenses_flow()
        elif choice == '3': # This option is redundant as view_expenses_flow already handles category filtering
            # This is partly covered by view_expenses_flow with category filter
            # Could add a dedicated "summary by category" option without date range initially
            view_expenses_flow() # For now, re-use with category prompt
        elif choice == '4':
            view_monthly_summary_flow()
        elif choice == '5':
            total_mpesa_charges_flow()
        elif choice == '6':
            insights = agent.analyze_current_month()
            print("\n--- AI Agent's Financial Insights and Suggestions ---")
            for insight in insights:
                print(insight)
        elif choice == '7':
            print("Exiting Expense Tracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()