# sms_parser.py
import re
from datetime import datetime

# A simplified parser focusing on a few common M-Pesa message types.
# A real-world implementation would be more robust and cover more cases.

def _parse_date(date_str):
    """Parses M-Pesa's date format into YYYY-MM-DD."""
    try:
        # Handles formats like "24/7/24 at 7:30 PM"
        dt_obj = datetime.strptime(date_str, '%d/%m/%y at %I:%M %p')
        return dt_obj.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Handles formats like "24/7/2024 at 7:30 PM"
            dt_obj = datetime.strptime(date_str, '%d/%m/%Y at %I:%M %p')
            return dt_obj.strftime('%Y-%m-%d')
        except ValueError:
            # Fallback for unexpected formats
            return datetime.now().strftime('%Y-%m-%d')

def parse_mpesa_message(sms_text):
    """
    Parses an M-Pesa SMS and extracts transaction details.
    Returns a
    dictionary with the parsed data or None if it fails.
    """
    # Regex for "Sent to" and "Pay Bill/Buy Goods"
    # Example: SBB0123ABC Confirmed. Ksh1,200.00 sent to John Doe 0712345678 on 24/7/24 at 7:30 PM. New M-PESA balance is Ksh5,000.00. Transaction cost, Ksh23.00.
    # Example: SBB0123ABC Confirmed. Ksh1,200.00 paid to KPLC PREPAID. on 24/7/24 at 7:30 PM. New M-PESA balance is Ksh5,000.00. Transaction cost, Ksh0.00.
    sent_pattern = re.compile(
        r"^(?P<transaction_id>[A-Z0-9]{10})\sConfirmed\.\s"
        r"Ksh(?P<amount>[\d,]+\.\d{2})\s"
        r"(?:sent to|paid to)\s(?P<recipient>.+?)\s"
        r"(?:on|at)\s(?P<date>[\d/]+\s+at\s+\d{1,2}:\d{2}\s+[AP]M)\."
        r".*Transaction cost,\sKsh(?P<transaction_cost>[\d,]+\.\d{2})\.",
        re.IGNORECASE | re.DOTALL
    )

    # Regex for "Withdrawal"
    # Example: SBB0123ABC Confirmed. on 24/7/24 at 7:30 PM Give Ksh1,000.00 cash to John Doe. New M-PESA balance is Ksh4,000.00. Transaction cost, Ksh29.00.
    withdrawal_pattern = re.compile(
        r"^(?P<transaction_id>[A-Z0-9]{10})\sConfirmed\.\s"
        r"on\s(?P<date>[\d/]+\s+at\s+\d{1,2}:\d{2}\s+[AP]M)\s"
        r"Give\sKsh(?P<amount>[\d,]+\.\d{2})\scash to\s(?P<agent>.+?)\."
        r".*Transaction cost,\sKsh(?P<transaction_cost>[\d,]+\.\d{2})\.",
        re.IGNORECASE | re.DOTALL
    )

    for pattern, type_name in [(sent_pattern, "Sent/Paid"), (withdrawal_pattern, "Withdrawal")]:
        match = pattern.search(sms_text)
        if match:
            data = match.groupdict()
            recipient = data.get("recipient") or data.get("agent", "Agent")
            is_payment = "paid to" in match.group(0).lower()
            return {
                "transaction_id": data["transaction_id"],
                "type": "Pay Bill/Buy Goods" if is_payment else type_name,
                "amount": float(data["amount"].replace(",", "")),
                "date": _parse_date(data["date"]),
                "description": f"Payment to {recipient.strip()}" if is_payment else f"{type_name} to {recipient.strip()}",
                "business": recipient.strip() if is_payment else "",
                "transaction_cost": float(data["transaction_cost"].replace(",", "")),
                "payment_method": "MPESA"
            }

    return None