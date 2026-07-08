"""
Routing module for financial transaction endpoints (deposits, withdrawals, transfers)
and administrative transfer approval requests.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, Header, status # type: ignore
from fastapi.responses import JSONResponse # type: ignore

from app.models import (
    AccountResponse,
    DepositWithdrawRequest,
    TransferRequest,
    TransactionResponse,
    TransferRequestResponse,
    TransferRequestApproval,
)
from app.services import (
    deposit,
    withdraw,
    transfer,
    list_pending_transfers,
    resolve_transfer_request,
    get_transaction_history,
    validate_admin_token,
)
from app.exceptions import BankException # type: ignore

router = APIRouter(tags=["Transactions"])

@router.post("/accounts/{account_id}/deposit", response_model=AccountResponse)
def make_deposit(account_id: str, request: DepositWithdrawRequest):
    """
    Deposits funds into an active bank account.
    """
    return deposit(account_id=account_id, amount=request.amount)

@router.post("/accounts/{account_id}/withdraw", response_model=AccountResponse)
def make_withdrawal(account_id: str, request: DepositWithdrawRequest):
    """
    Withdraws funds from a bank account, checking limits and applying taxes.
    """
    return withdraw(account_id=account_id, amount=request.amount)

@router.post("/transfers")
def make_transfer(request: TransferRequest):
    """
    Executes a transfer from one account to another.
    If the transaction exceeds daily limits, it creates a PENDING request 
    requiring administrative approval and returns HTTP 202.
    """
    src, tgt, pending_req = transfer(
        source_id=request.source_account_id,
        target_id=request.target_account_id,
        amount=request.amount,
    )
    
    if pending_req:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "PENDING",
                "message": "Transfer exceeds daily limit and requires administrative approval.",
                "request": {
                    "id": pending_req["id"],
                    "source_account_id": pending_req["source_account_id"],
                    "target_account_id": pending_req["target_account_id"],
                    "amount": pending_req["amount"],
                    "status": pending_req["status"],
                    "timestamp": pending_req["timestamp"].isoformat()
                }
            }
        )
        
    return {
        "message": "Transfer successful",
        "source_account": AccountResponse.model_validate(src),
        "target_account": AccountResponse.model_validate(tgt),
    }

@router.get("/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
def view_transaction_history(
    account_id: str,
    type: Optional[str] = Query(None, description="Filter by transaction type (DEPOSIT, WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT)"),
    from_date: Optional[datetime] = Query(None, description="Filter transactions starting from this date (ISO format)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of transactions to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Returns the paginated transaction history of a bank account.
    """
    return get_transaction_history(
        account_id=account_id,
        tx_type=type,
        from_date=from_date,
        limit=limit,
        offset=offset,
    )

# ==============================================================================
# 🛡️ ADMINISTRATIVE APPROVAL ENDPOINTS
# ==============================================================================

@router.get("/admin/transfers/requests", response_model=List[TransferRequestResponse])
def view_pending_transfers(x_admin_token: Optional[str] = Header(None)):
    """
    Lists all pending transfer requests. Only accessible by the administrator.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return list_pending_transfers()

@router.post("/admin/transfers/requests/{request_id}/resolve", response_model=TransferRequestResponse)
def resolve_pending_transfer(
    request_id: str,
    approval: TransferRequestApproval,
    x_admin_token: Optional[str] = Header(None)
):
    """
    Approves or rejects a pending transfer request.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return resolve_transfer_request(request_id=request_id, approve=approval.approve)