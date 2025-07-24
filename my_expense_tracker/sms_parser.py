# sms_parser.py
import re
from datetime import datetime

# --- IMPORTANT: REGEX PATTERNS ---
# These are examples. You MUST test and adjust these regex patterns
# using your actual M-Pesa SMS messages from your phone.
# M-Pesa messages can vary slightly based on phone model, Safaricom updates, etc.

# Helper function to clean and convert amount strings
def _clean_amount_str(amount_str: str) -> float:
    return float(amount_str.replace(",", ""))

# Pattern 1: Money Sent (e.g., "Confirmed. KshXXX.XX sent to JOHN DOE 07XX... on XX/XX/XX at XX:XX PM. New M-PESA balance is KshY,YYY.YY. Transaction cost, KshZ.ZZ. ...")
PATTERN_SENT = re.compile(
    r"Confirmed\. (?:Ksh|KES)\s?([\d,]+\.\d{2}) sent to (.+?) on (\d{1,2}/\d{1,2}/\d{2}) at (\d{1,2}:\d{2} (?:AM|PM))\.\s*New M-PESA balance is (?:Ksh|KES)\s?([\d,]+\.\d{2})\.?\s*(?:Transaction cost, (?:Ksh|KES)\s?([\d,]+\.\d{2}))?.*"
)

# Pattern 2: Money Received (e.g., "Confirmed. You have received KshXXX.XX from JANE DOE 07XX... on XX/XX/XX at XX:XX PM. New M-PESA balance is KshY,YYY.YY. ...")
PATTERN_RECEIVED = re.compile(
    r"Confirmed\. You have received (?:Ksh|KES)\s?([\d,]+\.\d{2}) from (.+?) on (\d{1,2}/\d{1,2}/\d{2}) at (\d{1,2}:\d{2} (?:AM|PM))\.\s*New M-PESA balance is (?:Ksh|KES)\s?([\d,]+\.\d{2})\.?.*"
)

# Pattern 3: Pay Bill/Buy Goods (e.g., "Confirmed. KshXXX.XX paid to BUSINESS NAME for account YYY on XX/XX/XX at XX:XX PM. New M-PESA balance is KshZ,ZZZ.ZZ. ...")
PATTERN_PAYBILL_BUYGOODS = re.compile(
    r"Confirmed\. (?:Ksh|KES)\s?([\d,]+\.\d{2}) paid to (.+?)(?: for account (.+?))? on (\d{1,2}/\d{1,2}/\d{2}) at (\d{1,2}:\d{2} (?:AM|PM))\.\s*New M-PESA balance is (?:Ksh|KES)\s?([\d,]+\.\d{2})\.?\s*(?:Transaction cost, (?:Ksh|KES)\s?([\d,]+\.\d{2}))?.*" # Added optional transaction cost
)

# Pattern 4: Withdrawal (e.g., "Confirmed. KshXXX.XX withdrawn from M-PESA by [Agent Name] Agent XXXXXX on XX/XX/XX at XX:XX PM. New M-PESA balance is KshY,YYY.YY. Transaction cost, KshZ.ZZ. ...")
PATTERN_WITHDRAWAL = re.compile(
    r"Confirmed\. (?:Ksh|KES)\s?([\d,]+\.\d{2}) withdrawn from M-PESA by (.+?) Agent (\d+) on (\d{1,2}/\d{1,2}/\d{2}) at (\d{1,2}:\d{2} (?:AM|PM))\.\s*New M-PESA balance is (?:Ksh|KES)\s?([\d,]+\.\d{2})\.?\s*Transaction cost, (?:Ksh|KES)\s?([\d,]+\.\d{2})\.?.*"
)

# Pattern 5: Airtime Purchase (e.g., "Confirmed. You bought KshXXX.XX airtime for your own number on XX/XX/XX at XX:XX PM. New M-PESA balance is KshY,YYY.YY. ...")
PATTERN_AIRTIME = re.compile(
    r"Confirmed\. You bought (?:Ksh|KES)\s?([\d,]+\.\d{2}) airtime for (.+?) on (\d{1,2}/\d{1,2}/\d{2}) at (\d{1,2}:\d{2} (?:AM|PM))\.\s*New M-PESA balance is (?:Ksh|KES)\s?([\d,]+\.\d{2})\.?.*"
)


def parse_mpesa_message(message: str) -> dict | None:
    """
    Parses an M-Pesa SMS message and extracts key transaction details.
    Returns a dictionary of parsed data or None if no pattern matches.
    """
    message = message.strip() # Clean whitespace

    # --- Try to match against different patterns ---

    match = PATTERN_SENT.search(message)
    if match:
        data = {
            "type": "Sent",
            "amount": _clean_amount_str(match.group(1)),
            "recipient": match.group(2).strip(),
            "date_str": match.group(3),
            "time_str": match.group(4),
            "balance": _clean_amount_str(match.group(5)),
            "transaction_cost": _clean_amount_str(match.group(6)) if match.group(6) else 0.0,
            "description": f"Money sent to {match.group(2).strip()}"
        }
        return _format_parsed_data(data)

    match = PATTERN_RECEIVED.search(message)
    if match:
        data = {
            "type": "Received", # Note: This is income, not an expense
            "amount": _clean_amount_str(match.group(1)),
            "sender": match.group(2).strip(),
            "date_str": match.group(3),
            "time_str": match.group(4),
            "balance": _clean_amount_str(match.group(5)),
            "transaction_cost": 0.0, # Usually no cost for receiving
            "description": f"Money received from {match.group(2).strip()}"
        }
        return _format_parsed_data(data)

    match = PATTERN_PAYBILL_BUYGOODS.search(message)
    if match:
        data = {
            "type": "Pay Bill/Buy Goods",
            "amount": _clean_amount_str(match.group(1)),
            "business": match.group(2).strip(),
            "account": match.group(3).strip() if match.group(3) else None,
            "date_str": match.group(4),
            "time_str": match.group(5),
            "balance": _clean_amount_str(match.group(6)),
            "transaction_cost": _clean_amount_str(match.group(7)) if match.group(7) else 0.0, # Added optional group for cost
            "description": f"Payment to {match.group(2).strip()}"
        }
        return _format_parsed_data(data)
    
    match = PATTERN_WITHDRAWAL.search(message)
    if match:
        data = {
            "type": "Withdrawal",
            "amount": _clean_amount_str(match.group(1)),
            "agent_name": match.group(2).strip(),
            "agent_no": match.group(3).strip(),
            "date_str": match.group(4),
            "time_str": match.group(5),
            "balance": _clean_amount_str(match.group(6)),
            "transaction_cost": _clean_amount_str(match.group(7)) if match.group(7) else 0.0,
            "description": f"Cash Withdrawal from {match.group(2).strip()} ({match.group(3).strip()})"
        }
        return _format_parsed_data(data)

    match = PATTERN_AIRTIME.search(message)
    if match:
        data = {
            "type": "Airtime Purchase",
            "amount": _clean_amount_str(match.group(1)),
            "for_number": match.group(2).strip(),
            "date_str": match.group(3),
            "time_str": match.group(4),
            "balance": _clean_amount_str(match.group(5)),
            "transaction_cost": 0.0, # Airtime usually has no separate cost
            "description": f"Airtime purchase for {match.group(2).strip()}"
        }
        return _format_parsed_data(data)

    # If no pattern matches
    return None

def _format_parsed_data(data: dict) -> dict:
    """Helper to format date and time to standard YYYY-MM-DD and HH:MM:SS."""
    try:
        # Assuming M-Pesa dates are DD/MM/YY and time is HH:MM AM/PM
        # Note: If M-Pesa sometimes sends DD/MM/YYYY, you might need to try multiple formats
        date_obj = datetime.strptime(f"{data['date_str']} {data['time_str']}", "%d/%m/%y %I:%M %p")
        data['full_date'] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        data['date'] = date_obj.strftime("%Y-%m-%d")
        data['time'] = date_obj.strftime("%H:%M:%S")
        
    except ValueError as e:
        print(f"Error formatting date/time in SMS parser: {e} for data: {data}")
        data['full_date'] = None
        data['date'] = data['date_str'] # Keep original string if parsing fails
        data['time'] = data['time_str']
    return data

# --- Example Usage (for testing your patterns, run this file directly) ---
if __name__ == "__main__":
    test_messages = [
        "Confirmed. Ksh250.00 sent to JOHN DOE 0712345678 on 20/07/25 at 9:30 AM. New M-PESA balance is Ksh5,000.00. Transaction cost, Ksh13.00. Funds are available for 7 days.To reverse, forward this message to 456.",
        "Confirmed. You have received Ksh1,500.00 from JANE DOE 0787654321 on 20/07/25 at 9:45 AM. New M-PESA balance is Ksh6,500.00.",
        "Confirmed. Ksh1,200.00 paid to ABC Supermarket for account groceries on 20/07/25 at 10:00 AM. New M-PESA balance is Ksh5,300.00. Transaction cost, Ksh0.00.",
        "Confirmed. Ksh500.00 withdrawn from M-PESA by Mama Mboga Agent 123456 on 20/07/25 at 10:15 AM. New M-PESA balance is Ksh4,800.00. Transaction cost, Ksh29.00.",
        "Confirmed. You bought Ksh100.00 airtime for your own number on 20/07/25 at 10:30 AM. New M-PESA balance is Ksh4,700.00.",
        "Confirmed. You bought Ksh500.00 airtime for 0711223344 on 20/07/25 at 10:45 AM. New M-PESA balance is Ksh4,200.00.",
        "This is not an M-Pesa message.",
        "Confirmed. RGF4K2L3 Confirmed. Ksh2,000.00 sent to Test User 0711111111 on 20/07/25 at 11:00 AM. New M-PESA balance is Ksh20,000.00. Transaction cost, Ksh33.00.", # Example with transaction code
        # Add your own real M-Pesa messages here to test!
    ]

    print("--- Running SMS Parser Test ---")
    for msg in test_messages:
        print(f"\n--- Parsing: '{msg}' ---")
        parsed = parse_mpesa_message(msg)
        if parsed:
            print("Parsed Successfully:")
            for key, value in parsed.items():
                print(f"  {key}: {value}")
        else:
            print("Could not parse message.")