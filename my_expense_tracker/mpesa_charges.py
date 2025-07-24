# mpesa_charges.py

# DISCLAIMER: MPESA tariffs are subject to change.
# Always refer to the official Safaricom M-PESA tariffs for the most current rates.
# (As of 2024/2025, these are a close approximation but verify with Safaricom's official site)

MPESA_TARIFFS_P2P = [
    (0, 49, 0),    # Free
    (50, 100, 0),  # Free
    (101, 500, 7),
    (501, 1000, 13),
    (1001, 1500, 23),
    (1501, 2500, 33),
    (2501, 3500, 53),
    (3501, 5000, 57),
    (5001, 7500, 78),
    (7501, 10000, 90),
    (10001, 15000, 100),
    (15001, 20000, 105),
    (20001, 35000, 108),
    (35001, 50000, 108),
    (50001, 250000, 108), # Assuming max 250k for single transaction
]

MPESA_TARIFFS_WITHDRAWAL = [
    (10, 100, 11), # Smallest withdrawal amount often has a charge
    (101, 500, 29),
    (501, 1000, 29),
    (1001, 1500, 29),
    (1501, 2500, 29),
    (2501, 3500, 52),
    (3501, 5000, 69),
    (5001, 7500, 87),
    (7501, 10000, 115),
    (10001, 15000, 167),
    (15001, 20000, 185),
    (20001, 35000, 197),
    (35001, 50000, 278),
    (50001, 250000, 309),
]

def calculate_mpesa_charge(amount: float, transaction_type: str = 'P2P') -> float:
    """
    Calculates the M-Pesa transaction charge based on amount and transaction type.
    transaction_type: 'P2P' (Person-to-Person) or 'WITHDRAWAL'.
    For 'Pay Bill'/'Buy Goods' (Till Number), often the recipient pays or it's free for sender.
    """
    tariffs = []
    if transaction_type.upper() == 'P2P':
        tariffs = MPESA_TARIFFS_P2P
    elif transaction_type.upper() == 'WITHDRAWAL':
        tariffs = MPESA_TARIFFS_WITHDRAWAL
    else:
        # Default to no charge for other types (e.g., Pay Bill/Buy Goods, Airtime)
        return 0.0

    for min_amt, max_amt, charge in tariffs:
        if min_amt <= amount <= max_amt:
            return float(charge)
    
    # If amount is outside defined ranges (e.g., too small or too large)
    return 0.0