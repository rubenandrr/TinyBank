"""
Routing module for bank account-related endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Header # type: ignore

from app.models import AccountCreate, AccountResponse, LimitUpdateRequest
from app.services import create_account, freeze_account, unfreeze_account, update_account_limits, validate_admin_token, delete_account
from app.exceptions import BankException # type: ignore

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("", response_model=AccountResponse, status_code=201)
def create_new_account(account_in: AccountCreate, x_admin_token: Optional[str] = Header(None)):
    """
    Opens an additional bank account (Current or Savings) in the specified currency
    for an active user. Only administrative users can trigger account openings.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return create_account(
        user_id=account_in.user_id,
        account_type=account_in.account_type,
        currency=account_in.currency,
    )

@router.post("/{account_id}/freeze", response_model=AccountResponse)
def freeze_existing_account(account_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Freezes a bank account. Blocks all future withdrawals, deposits, and transfers.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return freeze_account(account_id=account_id)

@router.post("/{account_id}/unfreeze", response_model=AccountResponse)
def unfreeze_existing_account(account_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Unfreezes a frozen account to restore normal banking operations.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return unfreeze_account(account_id=account_id)

@router.put("/{account_id}/limits", response_model=AccountResponse)
def update_limits(account_id: str, limit_in: LimitUpdateRequest, x_admin_token: Optional[str] = Header(None)):
    """
    Updates daily withdrawal/transfer thresholds and spent counts for a account.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return update_account_limits(account_id=account_id, limit_update=limit_in)

@router.delete("/{account_id}", response_model=AccountResponse)
def delete_existing_account(account_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Deletes an additional account, automatically transferring any remaining balance to the user's primary base account.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return delete_account(account_id=account_id)