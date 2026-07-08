"""
Routing module for user-related endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Header # type: ignore

from app.models import UserCreate, UserResponse
from app.services import create_user, list_users, get_user, deactivate_user, validate_admin_token
from app.exceptions import BankException # type: ignore

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=UserResponse, status_code=201)
def create_new_user(user_in: UserCreate):
    """
    Creates a new active user.
    Automatically associates one Current and one Savings account in CHF.
    """
    return create_user(name=user_in.name)

@router.get("", response_model=List[UserResponse])
def get_all_users(x_admin_token: Optional[str] = Header(None)):
    """
    Returns the list of all registered users and their accounts.
    Filters out system users unless authorized as admin.
    """
    users = list_users()
    if x_admin_token and validate_admin_token(x_admin_token):
        return users
    # Filter out system and admin accounts from normal views
    return [u for u in users if u["id"] not in ("bank-tax-user", "admin-user")]

@router.get("/{user_id}", response_model=UserResponse)
def get_user_details(user_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Returns detailed information of a specific user.
    """
    if user_id in ("bank-tax-user", "admin-user"):
        if not x_admin_token or not validate_admin_token(x_admin_token):
            raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return get_user(user_id=user_id)

@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_existing_user(user_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Deactivates a user and automatically freezes all associated accounts.
    """
    if not x_admin_token or not validate_admin_token(x_admin_token):
        raise BankException("Access denied. Administrative authorization required.", status_code=403)
    return deactivate_user(user_id=user_id)