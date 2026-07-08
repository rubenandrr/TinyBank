"""
This module manages the lifecycle of bank accounts: creation, freezing/unfreezing,
and updating daily spending limits.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from app.database import ACCOUNTS, USERS, BANK_TAX_USER_ID, db_lock
from app.config import (
    DEFAULT_DAILY_WITHDRAWAL_LIMIT,
    DEFAULT_DAILY_TRANSFER_LIMIT,
    DEFAULT_MAX_DAILY_TRANSFERS,
)
from app.models import AccountType, Currency, LimitUpdateRequest
from app.exceptions import EntityNotFoundException, InactiveUserException, BankException
from app.services.helpers import add_audit_log

def create_account_no_lock(user_id: str, account_type: AccountType, currency: Currency) -> Dict[str, Any]:
    """
    Creates a bank account in memory for a given user.
    (Must be executed within a 'with db_lock' block).
    """
    if user_id == BANK_TAX_USER_ID:
        raise BankException("The system tax collector user cannot possess additional bank accounts.", status_code=400)
    if user_id not in USERS:
        raise EntityNotFoundException(f"User with ID {user_id} does not exist.")
    if not USERS[user_id]["is_active"]:
        raise InactiveUserException("Cannot open an account for a deactivated user.")

    account_id = str(uuid.uuid4())
    now = datetime.now()

    account = {
        "id": account_id,
        "user_id": user_id,
        "account_type": account_type,
        "balance": 0.0,
        "currency": currency,
        "is_frozen": False,
        "daily_withdrawal_limit": DEFAULT_DAILY_WITHDRAWAL_LIMIT,
        "daily_transfer_limit": DEFAULT_DAILY_TRANSFER_LIMIT,
        "max_daily_transfers": DEFAULT_MAX_DAILY_TRANSFERS,
        "withdrawal_spent_today": 0.0,
        "transfer_spent_today": 0.0,
        "transfers_count_today": 0,
        "last_limit_reset": now,
        "created_at": now
    }

    ACCOUNTS[account_id] = account
    add_audit_log("ACCOUNT_CREATED", f"Account {account_id} ({account_type.value} in {currency.value}) opened for user {user_id}.")
    return account

def create_account(user_id: str, account_type: AccountType, currency: Currency) -> Dict[str, Any]:
    """
    Opens an additional bank account in the specified currency for an active user.
    """
    with db_lock:
        return create_account_no_lock(user_id, account_type, currency)

def freeze_account(account_id: str) -> Dict[str, Any]:
    """
    Freezes an individual account, blocking all future transactions.
    """
    with db_lock:
        if account_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Account with ID {account_id} does not exist.")
        ACCOUNTS[account_id]["is_frozen"] = True
        add_audit_log("ACCOUNT_FROZEN", f"Account {account_id} was frozen.")
        return ACCOUNTS[account_id]

def unfreeze_account(account_id: str) -> Dict[str, Any]:
    """
    Unfreezes a bank account to allow transaction flow again.
    """
    with db_lock:
        if account_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Account with ID {account_id} does not exist.")
        
        # Owner must be active to unfreeze
        user_id = ACCOUNTS[account_id]["user_id"]
        if not USERS[user_id]["is_active"]:
            raise InactiveUserException("Cannot unfreeze an account belonging to a deactivated user.")

        ACCOUNTS[account_id]["is_frozen"] = False
        add_audit_log("ACCOUNT_UNFROZEN", f"Account {account_id} was unfrozen.")
        return ACCOUNTS[account_id]

def update_account_limits(account_id: str, limit_update: LimitUpdateRequest) -> Dict[str, Any]:
    """
    Updates the daily spending limits and maximum transfer counts for a bank account.
    """
    with db_lock:
        if account_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Account with ID {account_id} does not exist.")
        
        acc = ACCOUNTS[account_id]
        if limit_update.daily_withdrawal_limit is not None:
            acc["daily_withdrawal_limit"] = limit_update.daily_withdrawal_limit
        if limit_update.daily_transfer_limit is not None:
            acc["daily_transfer_limit"] = limit_update.daily_transfer_limit
        if limit_update.max_daily_transfers is not None:
            acc["max_daily_transfers"] = limit_update.max_daily_transfers

        add_audit_log("LIMITS_UPDATED", f"Limits updated for account {account_id}.")
        return acc