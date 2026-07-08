"""
Routing module for system audit logs.
"""

from typing import List, Optional
from fastapi import APIRouter, Header

from app.models import AuditLogResponse
from app.services import get_audit_logs, validate_admin_token
from app.exceptions import BankException # type: ignore

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_trail(x_admin_token: Optional[str] = Header(None)):
    """
    Returns the complete system audit logs. Only accessible by the administrator.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return get_audit_logs()