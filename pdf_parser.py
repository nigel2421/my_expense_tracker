# pdf_parser.py
import pdfplumber
import re
from datetime import datetime

def parse_mpesa_statement_pdf(pdf_file_path):
    """
    Parses an M-Pesa statement PDF to extract transactions.

    Disclaimer: PDF statement formats can vary significantly. This parser uses
    regular expressions to find common patterns and may need to be adjusted
    for your specific statement layout. It's designed to be a starting point.
    """
    transactions = []
    full_text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return []

    # Regex to find transaction lines. This is the part that is most likely to need adjustment.
    # It looks for a transaction ID, a date/time, a description, and then amounts.
    # Example line: "QGA4S2D8F1 18/07/24, 10:30 PM Pay Bill to KPLC ... 1,000.00  5,000.00"
    transaction_pattern = re.compile(
        r"([A-Z0-9]{10})\s+"  # 1. Transaction ID (e.g., QGA4S2D8F1)
        r"(\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s+[AP]M)\s+"  # 2. Date and Time
        r"(.+?)\s+"  # 3. Details (non-greedy)
        r"([\d,]+\.\d{2})?\s*"  # 4. Paid In (optional)
        r"([\d,]+\.\d{2})?\s*"  # 5. Withdrawn (optional)
        r"([\d,]+\.\d{2})"  # 6. Balance
    )

    for line in full_text.split('\n'):
        match = transaction_pattern.match(line.strip())
        if match:
            transaction_id, datetime_str, details, paid_in_str, withdrawn_str, _ = match.groups()

            try:
                # We are an expense tracker, so we only care about money going out.
                if not withdrawn_str:
                    continue

                amount = float(withdrawn_str.replace(",", ""))

                # Try to parse different date formats
                try:
                    dt_obj = datetime.strptime(datetime_str, "%d/%m/%y, %I:%M %p")
                except ValueError:
                    dt_obj = datetime.strptime(datetime_str, "%d/%m/%Y, %I:%M %p")
                date_str = dt_obj.strftime("%Y-%m-%d")

                transactions.append({
                    "transaction_id": transaction_id,
                    "date": date_str,
                    "description": details.strip(),
                    "amount": amount,
                })
            except (ValueError, TypeError):
                continue # Skip lines that can't be parsed

    return transactions