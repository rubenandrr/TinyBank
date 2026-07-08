"""
This module provides utility functions shared across different services,
such as currency conversions, daily limits reset, and audit log generation.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from app.database import AUDIT_LOGS, db_lock
from app.config import EXCHANGE_RATES, BANK_MARGIN

def reset_daily_limits_if_needed(account: Dict[str, Any]):
    """
    Resets account daily spending limits if the current date is past 
    the date of the last limit reset.
    """
    now = datetime.now()
    last_reset = account.get("last_limit_reset")
    if not last_reset:
        account["last_limit_reset"] = now
        return

    if now.date() > last_reset.date():
        account["withdrawal_spent_today"] = 0.0
        account["transfer_spent_today"] = 0.0
        account["transfers_count_today"] = 0
        account["last_limit_reset"] = now

def add_audit_log(action: str, details: str):
    """
    Appends a uniquely identified, timestamped entry to the bank's audit logs.
    """
    log_entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    }
    AUDIT_LOGS.append(log_entry)

def convert_currency_with_margin(amount: float, from_currency: str, to_currency: str) -> tuple[float, float, float]:
    """
    Converts an amount from a source currency to a target currency.
    Applies the banking commission fee margin (0.5%).
    Returns: (raw_target_amount, bank_commission, net_target_amount)
    """
    if from_currency == to_currency:
        return amount, 0.0, amount

    # Conversion using Euro as the base pivot currency
    amount_in_eur = amount / EXCHANGE_RATES[from_currency]
    raw_target_amount = amount_in_eur * EXCHANGE_RATES[to_currency]

    # Apply banking margin (0.5%)
    margin = raw_target_amount * BANK_MARGIN
    net_target_amount = raw_target_amount - margin

    return round(raw_target_amount, 2), round(margin, 2), round(net_target_amount, 2)