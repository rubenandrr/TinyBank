"""
This module manages the lifecycle of users: creation (with default accounts),
fetching information, and deactivation.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any

from app.database import USERS, ACCOUNTS, db_lock
from app.models import AccountType, Currency
from app.exceptions import EntityNotFoundException # type: ignore
from app.services.helpers import add_audit_log
from app.services.account_service import create_account_no_lock # type: ignore

def create_user(name: str) -> Dict[str, Any]:
    """
    Creates a new user and automatically opens two default accounts 
    (Current and Savings) in CHF.
    """
    with db_lock:
        user_id = str(uuid.uuid4())
        now = datetime.now()
        
        user = {
            "id": user_id,
            "name": name,
            "is_active": True,
            "created_at": now,
            "accounts": []
        }
        
        USERS[user_id] = user
        add_audit_log("USER_CREATED", f"User '{name}' (ID: {user_id}) created.")

        # Automatically open default account in CHF (Current only)
        create_account_no_lock(user_id, AccountType.CURRENT, Currency.CHF)

        return get_user_no_lock(user_id)

def get_user_no_lock(user_id: str) -> Dict[str, Any]:
    """
    Retrieves a user and their associated accounts without acquiring the lock.
    (Must be executed within a 'with db_lock' block).
    """
    if user_id not in USERS:
        raise EntityNotFoundException(f"User with ID {user_id} does not exist.")
    
    user = USERS[user_id].copy()
    user["accounts"] = [
        acc for acc in ACCOUNTS.values() if acc["user_id"] == user_id
    ]
    return user

def get_user(user_id: str) -> Dict[str, Any]:
    """
    Retrieves a user and their associated accounts.
    """
    with db_lock:
        return get_user_no_lock(user_id)

def list_users() -> List[Dict[str, Any]]:
    """
    Returns a list of all registered users.
    """
    with db_lock:
        return [get_user_no_lock(uid) for uid in USERS.keys()]

def deactivate_user(user_id: str) -> Dict[str, Any]:
    """
    Deactivates a user and freezes all of their associated accounts.
    """
    with db_lock:
        if user_id not in USERS:
            raise EntityNotFoundException(f"User with ID {user_id} does not exist.")
        
        USERS[user_id]["is_active"] = False
        add_audit_log("USER_DEACTIVATED", f"User {user_id} was deactivated.")

        # Freeze all associated accounts
        for acc in ACCOUNTS.values():
            if acc["user_id"] == user_id:
                acc["is_frozen"] = True
                add_audit_log("ACCOUNT_FROZEN", f"Account {acc['id']} frozen due to user deactivation.")

        return get_user_no_lock(user_id)