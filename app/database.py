"""
This module handles in-memory data storage for the application.
It uses a threading.Lock to ensure thread-safety and consistency
during concurrent API access.
"""

import threading
from datetime import datetime
from typing import Dict, List, Any

# System identifiers for the bank's tax collector account
BANK_TAX_USER_ID = "bank-tax-user"
BANK_TAX_ACCOUNT_ID = "bank-tax-account"

# Global lock to secure concurrent read/write operations
db_lock = threading.Lock()

# User storage
# Key: user_id (str) -> Value: dict containing user details
USERS: Dict[str, Dict[str, Any]] = {}

# Bank account storage
# Key: account_id (str) -> Value: dict detailing balances, currencies, and limits
ACCOUNTS: Dict[str, Dict[str, Any]] = {}

# Chronological list of completed financial transactions (Deposits, Withdrawals, Transfers)
TRANSACTIONS: List[Dict[str, Any]] = []

# Chronological list of administrative actions and system security logs
AUDIT_LOGS: List[Dict[str, Any]] = []

def seed_bank_tax():
    """
    Pre-registers the system tax collector user and its associated CHF current account.
    """
    USERS[BANK_TAX_USER_ID] = {
        "id": BANK_TAX_USER_ID,
        "name": "Tiny Bank - Taxes",
        "is_active": True,
        "created_at": datetime.now(),
    }
    ACCOUNTS[BANK_TAX_ACCOUNT_ID] = {
        "id": BANK_TAX_ACCOUNT_ID,
        "user_id": BANK_TAX_USER_ID,
        "account_type": "CURRENT",
        "balance": 0.0,
        "currency": "CHF",
        "is_frozen": False,
        "daily_withdrawal_limit": 999999999.0,
        "daily_transfer_limit": 999999999.0,
        "max_daily_transfers": 999999999,
        "withdrawal_spent_today": 0.0,
        "transfer_spent_today": 0.0,
        "transfers_count_today": 0,
        "created_at": datetime.now(),
    }

# Seed tax collector on startup
seed_bank_tax()

def reset_db():
    """
    Resets and clears the entire in-memory storage.
    Mainly used to guarantee test isolation.
    """
    with db_lock:
        USERS.clear()
        ACCOUNTS.clear()
        TRANSACTIONS.clear()
        AUDIT_LOGS.clear()
        seed_bank_tax()