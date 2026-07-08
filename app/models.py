from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict # type: ignore

class AccountType(str, Enum):
    """
    Represents the type of bank account available (Current or Savings).
    """
    CURRENT = "CURRENT"      # Current Account
    SAVINGS = "SAVINGS"      # Savings Account
    
class Currency(str, Enum):
    """
    Represents the currencies supported by the bank (CHF, EUR, USD).
    """
    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"

class TransactionType(str, Enum):
    """
    Represents the types of financial transactions recorded.
    """
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    
class UserCreate(BaseModel):
    """
    Validation schema for creating a user.
    """
    name: str = Field(..., min_length=2, max_length=50, description="Full name of the user")
    
class AccountResponse(BaseModel):
    """
    Data structure model for the response containing account details.
    """
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    account_type: AccountType
    balance: float
    currency: Currency
    is_frozen: bool
    daily_withdrawal_limit: float
    daily_transfer_limit: float
    max_daily_transfers: int
    withdrawal_spent_today: float
    transfer_spent_today: float
    transfers_count_today: int
    created_at: datetime
    
class UserResponse(BaseModel):
    """
    Data structure model for the response detailing a user and their accounts.
    """
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    is_active: bool
    created_at: datetime
    accounts: List[AccountResponse] = []
    
class AccountCreate(BaseModel):
    """
    Validation schema for opening an additional bank account.
    """
    user_id: str
    account_type: AccountType
    currency: Currency = Currency.CHF
    
class DepositWithdrawRequest(BaseModel):
    """
    Validation schema for deposit and withdrawal operations.
    """
    account_id: str
    amount: float = Field(..., gt=0, description="Amount to deposit or withdraw")
    
class TransferRequest(BaseModel):
    """
    Validation schema for transferring money between accounts.
    """
    from_account_id: str
    to_account_id: str
    amount: float = Field(..., gt=0, description="Amount to transfer")

class LimitUpdateRequest(BaseModel):
    """
    Validation schema for updating daily account limits.
    """
    daily_withdrawal_limit: Optional[float] = Field(None, gt=0, description="New daily withdrawal limit")
    daily_transfer_limit: Optional[float] = Field(None, gt=0, description="New daily transfer limit")
    max_daily_transfers: Optional[int] = Field(None, gt=0, description="New maximum daily transfer count")
    
class TransactionResponse(BaseModel):
    """
    Response schema detailing a bank transaction.
    """
    model_config = ConfigDict(from_attributes=True)
    id: str
    account_id: str
    type: TransactionType
    amount: float
    currency: Currency
    related_account_id: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime
    
class AuditLogResponse(BaseModel):
    """
    Response schema detailing a system audit log entry.
    """
    model_config = ConfigDict(from_attributes=True)
    id: str
    action: str
    details: str
    timestamp: datetime
    
class LoginRequest(BaseModel):
    """
    Validation schema for admin authentication.
    """
    username: str = Field(..., description="Username of the user")
    password: str = Field(..., description="Raw password of the user")

class LoginResponse(BaseModel):
    """
    Response schema returning authentication outcome.
    """
    success: bool
    message: str
    user_id: str

class TransferRequestStatus(str, Enum):
    """
    Represents the status of a pending transfer request.
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class TransferRequestResponse(BaseModel):
    """
    Response schema detailing a pending limit transfer request.
    """
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_account_id: str
    target_account_id: str
    amount: float
    status: TransferRequestStatus
    timestamp: datetime

class TransferRequestApproval(BaseModel):
    """
    Validation schema for approving or rejecting a pending transfer.
    """
    approve: bool = Field(..., description="True to approve, False to reject")