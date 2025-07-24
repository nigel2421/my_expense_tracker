# financial_agent.py
import pandas as pd
from datetime import datetime
import database # Your existing database module

class FinancialAgent:
    """
    An AI-like agent that analyzes spending data and provides insights and suggestions.
    """
    def __init__(self, budgeted_amounts: dict):
        """
        Initializes the agent with the user's monthly budgeted amounts.

        Args:
            budgeted_amounts (dict): A dictionary mapping category names to budgeted amounts (Ksh).
                                     e.g., {'Food': 11000, 'Mobile Data/Airtime': 1000, ...}
        """
        self.budgeted_amounts = budgeted_amounts

    def get_spending_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches historical spending data from the database for a given date range
        and converts it into a pandas DataFrame.
        """
        # get_expenses returns a tuple (rows, total_count). We need the rows.
        # Set a very high limit to fetch all records for analysis.
        expenses_data, _ = database.get_expenses(start_date=start_date, end_date=end_date, limit=100000)
        
        # Convert list of Row objects to pandas DataFrame for easier analysis
        if not expenses_data:
            return pd.DataFrame(columns=['date', 'description', 'category', 'amount', 'payment_method', 'mpesa_charge', 'total_outflow'])
        
        # sqlite3.Row objects are dict-like, so pandas can create a DataFrame directly.
        df = pd.DataFrame(expenses_data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def analyze_current_month(self) -> list[str]:
        """
        Analyzes spending for the current month against the budget and historical data.
        Returns a list of insightful strings and suggestions.
        """
        today = datetime.now()
        current_month_start = today.replace(day=1).strftime("%Y-%m-%d")
        current_month_end = today.strftime("%Y-%m-%d") # Up to today's date

        df_current_month = self.get_spending_data(current_month_start, current_month_end)
        
        suggestions = []

        if df_current_month.empty:
            suggestions.append("No spending data yet for this month. Start tracking your expenses to get insights!")
            return suggestions

        # Calculate spending by category for the current month
        current_spending = df_current_month.groupby('category')['total_outflow'].sum().to_dict()

        # --- Level 1: Rule-Based / Threshold-Based Analysis ---
        suggestions.append("\n--- Current Month Spending Analysis ---")
        
        from calendar import monthrange
        try:
            days_in_current_month = monthrange(today.year, today.month)[1]
        except ValueError: # Fallback for edge cases or if month/year are somehow invalid
            days_in_current_month = 30 # Default to 30 days
            
        current_day_of_month = today.day
        
        # Iterate over budgeted categories for direct comparison
        for category, budgeted_amount in self.budgeted_amounts.items():
            if category in ['Rent (Incl. Utilities)', 'Savings Fund', 'Investment (e.g., Sacco)']:
                # These are often fixed or target-based, handled separately if needed
                # For savings, we'll check overall progress later
                continue 

            spent = current_spending.get(category, 0.0)
            
            # Estimate expected spending for the current day of the month
            # Assumes linear spending, which isn't always true but provides a benchmark
            expected_spent_proportion = current_day_of_month / days_in_current_month
            expected_spent_up_to_today = budgeted_amount * expected_spent_proportion

            if budgeted_amount > 0: # Only compare if there's a budget for it
                if spent > budgeted_amount * 1.05: # More than 5% over full monthly budget
                    suggestions.append(f"🚨 Urgent: Your '{category}' spending (Ksh {spent:,.2f}) is already OVER your entire monthly budget (Ksh {budgeted_amount:,.2f}). Extreme caution needed.")
                elif spent > expected_spent_up_to_today * 1.20: # More than 20% over expected for this time of month
                    suggestions.append(f"❗ Alert: Your '{category}' spending (Ksh {spent:,.2f}) is {((spent / expected_spent_up_to_today) - 1)*100:.0f}% higher than expected for this point in the month (expected: Ksh {expected_spent_up_to_today:,.2f}). Review recent expenses.")
                elif spent < expected_spent_up_to_today * 0.80 and current_day_of_month > (days_in_current_month / 2): # Significantly under expected halfway through
                    suggestions.append(f"✅ Good: Your '{category}' spending (Ksh {spent:,.2f}) is well under track for the month. Keep up the good work!")
            else: # If a category has no budget but has spending
                if spent > 0:
                    suggestions.append(f"ℹ Info: You've spent Ksh {spent:,.2f} in '{category}', but no budget is set. Consider allocating a budget or reviewing if this is a recurring expense.")


        total_mpesa_charges_current_month = df_current_month['mpesa_charge'].sum()
        if total_mpesa_charges_current_month > 150: # Example threshold
            suggestions.append(f"💰 M-Pesa Charges: Your total M-Pesa charges this month are Ksh {total_mpesa_charges_current_month:,.2f}. For small amounts, consider cash or consolidating transactions.")

        # Check Savings Fund progress
        savings_budget_target = self.budgeted_amounts.get('Savings Fund', 0)
        actual_savings_recorded = current_spending.get('Savings Fund', 0.0)
        if savings_budget_target > 0:
            if actual_savings_recorded < savings_budget_target * 0.50 and current_day_of_month > (days_in_current_month / 2):
                suggestions.append(f"🎯 Savings Goal: You've only saved Ksh {actual_savings_recorded:,.2f} towards your monthly goal of Ksh {savings_budget_target:,.2f}. Consider prioritizing this.")
            elif actual_savings_recorded >= savings_budget_target:
                 suggestions.append(f"🎉 Excellent! You've met or exceeded your monthly savings goal of Ksh {savings_budget_target:,.2f}! Keep building your financial future.")


        # --- Level 2: Data-Driven Insights (Last 3 Full Months) ---
        suggestions.append("\n--- Historical Spending Trends (Last 3 Months) ---")
        
        # Calculate start date for last 3 full months + current partial month
        three_months_ago_start = (today - pd.DateOffset(months=3)).replace(day=1).strftime("%Y-%m-%d")
        df_past = self.get_spending_data(three_months_ago_start, current_month_end)
        
        if not df_past.empty:
            # Group by month and category
            monthly_spending_by_cat = df_past.groupby([df_past['date'].dt.to_period('M'), 'category'])['total_outflow'].sum().unstack(fill_value=0)
            
            if len(monthly_spending_by_cat.index) >= 2: # Need at least 2 monthly data points for trends
                suggestions.append("Here's how your spending patterns look over the last few months:")
                for category in monthly_spending_by_cat.columns:
                    if category in self.budgeted_amounts and self.budgeted_amounts[category] > 0: # Only analyze budgeted items
                        avg_spend_past_months = monthly_spending_by_cat[category].mean()
                        budget = self.budgeted_amounts[category]

                        if avg_spend_past_months > budget * 1.10: # Consistently over budget by >10%
                            suggestions.append(f"📈 Trend: Your average monthly spending on '{category}' (Ksh {avg_spend_past_months:,.2f}) has consistently been {((avg_spend_past_months / budget) - 1)*100:.0f}% above your budget (Ksh {budget:,.2f}). Consider adjusting the budget or spending habits.")
                        elif avg_spend_past_months < budget * 0.90: # Consistently under budget by >10%
                            suggestions.append(f"📉 Trend: You consistently spend less on '{category}' (avg Ksh {avg_spend_past_months:,.2f}) than budgeted (Ksh {budget:,.2f}). Good opportunity to increase savings or another goal!")
                
                # Identify top spending categories historically
                total_past_spending_overall = df_past.groupby('category')['total_outflow'].sum().nlargest(3)
                if not total_past_spending_overall.empty:
                    top_spenders_str = ', '.join([f'{cat} (Ksh {amount:,.2f})' for cat, amount in total_past_spending_overall.items()])
                    suggestions.append(f"Your top 3 overall spending categories over the last few months: {top_spenders_str}.")
        else:
            suggestions.append("Not enough historical data yet for detailed trend analysis (need at least 2 full months).")


        # --- Level 3: Basic Recommendations ---
        suggestions.append("\n--- Forward-Looking Recommendations ---")
        
        # Identify categories where you are significantly over budget this month (non-essentials)
        over_budget_non_essentials = []
        for category, spent in current_spending.items():
            if category in ['Discretionary/Flex', 'Personal Care & Misc.']: # These are categories often flexible
                budget = self.budgeted_amounts.get(category, 0.0)
                if budget > 0 and spent > budget * 1.10: # 10% over budget
                    over_budget_non_essentials.append(category)
        
        if over_budget_non_essentials:
            suggestions.append(f"💡 Actionable: To improve your monthly financial health, try to reduce spending in: {', '.join(over_budget_non_essentials)}. Small cuts here can have a big impact.")
        
        # Suggest where to potentially increase spending (if very under budget on essentials or for goals)
        under_budget_essentials = []
        for category, spent in current_spending.items():
            if category in ['Food'] and self.budgeted_amounts.get(category, 0.0) > 0:
                budget = self.budgeted_amounts[category]
                if spent < budget * 0.70 and current_day_of_month > (days_in_current_month * 0.75): # 70% of budget by 75% of month
                    under_budget_essentials.append(category)
        
        if under_budget_essentials:
            suggestions.append(f"Considered increasing: You are well under budget in {', '.join(under_budget_essentials)}. This might free up funds for more savings or other goals.")

        # Check overall budget vs. actual for the month
        total_budgeted = sum(self.budgeted_amounts.values())
        total_spent_actual = df_current_month['total_outflow'].sum()
        
        if total_spent_actual > total_budgeted * 1.05:
            suggestions.append(f"🛑 Overall: Your total spending (Ksh {total_spent_actual:,.2f}) is exceeding your total monthly budget (Ksh {total_budgeted:,.2f}). Review all categories for potential cuts.")
        elif total_spent_actual < total_budgeted * 0.95 and current_day_of_month == days_in_current_month:
            suggestions.append(f"🎉 Fantastic! You ended the month under your total budget! Keep up this great discipline and consider increasing your savings goal.")

        return suggestions