"""
Routing module for authentication endpoints.
"""

from fastapi import APIRouter # type: ignore
from app.models import LoginRequest, LoginResponse
from app.services.auth_service import verify_admin_login

router = APIRouter(prefix="/login", tags=["Authentication"])

@router.post("", response_model=LoginResponse)
def login(login_in: LoginRequest):
    """
    Authenticates administrative users and returns a dynamic session token.
    """
    result = verify_admin_login(login_in.username, login_in.password)
    return {
        "success": True,
        "message": result["message"],
        "user_id": result["user_id"],
        "token": result["token"]
    }