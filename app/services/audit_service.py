"""
This module manages system audit operations, allowing tracking of all
administrative actions and financial transactions.
"""

from typing import List, Dict, Any
from app.database import AUDIT_LOGS, db_lock

def get_audit_logs() -> List[Dict[str, Any]]:
    """
    Returns the complete list of system audit logs, sorted in descending chronological order.
    """
    with db_lock:
        return sorted(AUDIT_LOGS, key=lambda x: x["timestamp"], reverse=True)