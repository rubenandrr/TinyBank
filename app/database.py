"""
This module handles in-memory data storage for the application.
It uses a threading.Lock to ensure thread-safety and consistency
during concurrent API access.
"""

import threading
import hashlib
from datetime import datetime
from typing import Dict, List, Any

# System identifiers for the bank's system accounts
BANK_TAX_USER_ID = "bank-tax-user"
BANK_TAX_ACCOUNT_ID = "bank-tax-account"
ADMIN_USER_ID = "admin-user"

# Hashed password for the admin account (password is "12345" + static salt)
ADMIN_PASSWORD_HASH = hashlib.sha256(b"12345-salt-tiny-bank").hexdigest()

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

# List of pending transfer requests exceeding daily limits
TRANSFER_REQUESTS: List[Dict[str, Any]] = []

def seed_bank_system():
    """
    Pre-registers the admin user, the system tax collector user,
    and the associated CHF current tax account.
    """
    now = datetime.now()
    
    # 1. Seed Admin User
    USERS[ADMIN_USER_ID] = {
        "id": ADMIN_USER_ID,
        "name": "Tiny Bank - Admin",
        "password_hash": ADMIN_PASSWORD_HASH,
        "is_active": True,
        "created_at": now,
    }
    
    # 2. Seed Tax Collector User
    USERS[BANK_TAX_USER_ID] = {
        "id": BANK_TAX_USER_ID,
        "name": "Tiny Bank - Taxes",
        "is_active": True,
        "created_at": now,
    }
    
    # 3. Seed Tax Collector Account
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
        "created_at": now,
    }

# Seed bank system on startup
seed_bank_system()

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
        TRANSFER_REQUESTS.clear()
        seed_bank_system()