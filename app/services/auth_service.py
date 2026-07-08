"""
This module manages administrative authentication, password verification,
and active session token generation.
"""

import hashlib
import secrets
from typing import Optional
from app.database import ADMIN_USER_ID, ADMIN_PASSWORD_HASH
from app.exceptions import BankException # type: ignore

# Global variable to store the currently active administrative session token
ACTIVE_ADMIN_TOKEN: Optional[str] = None

def verify_admin_login(username: str, password_raw: str) -> dict:
    """
    Verifies admin credentials by hashing the raw password with salt
    and comparing it against the stored admin password hash.
    Generates a cryptographically secure random session token upon success.
    """
    global ACTIVE_ADMIN_TOKEN
    
    if username.lower() != "admin":
        raise BankException("Invalid administrative credentials.", status_code=401)

    # Hash password using same algorithm and salt as seeded in database
    salted_pwd = (password_raw + "-salt-tiny-bank").encode()
    hashed_attempt = hashlib.sha256(salted_pwd).hexdigest()

    if hashed_attempt != ADMIN_PASSWORD_HASH:
        raise BankException("Invalid administrative credentials.", status_code=401)

    # Generate a cryptographically secure random 64-char hex token
    ACTIVE_ADMIN_TOKEN = secrets.token_hex(32)

    return {
        "success": True,
        "message": "Authentication successful.",
        "user_id": ADMIN_USER_ID,
        "token": ACTIVE_ADMIN_TOKEN
    }

def validate_admin_token(token: str) -> bool:
    """
    Validates the incoming token against the currently active admin token.
    """
    global ACTIVE_ADMIN_TOKEN
    return ACTIVE_ADMIN_TOKEN is not None and token == ACTIVE_ADMIN_TOKEN