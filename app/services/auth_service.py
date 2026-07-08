"""
This module manages administrative authentication and password verification.
"""

import hashlib
from app.database import ADMIN_USER_ID, ADMIN_PASSWORD_HASH
from app.exceptions import BankException # type: ignore

def verify_admin_login(username: str, password_raw: str) -> dict:
    """
    Verifies admin credentials by hashing the raw password with salt
    and comparing it against the stored admin password hash.
    """
    if username.lower() != "admin":
        raise BankException("Invalid administrative credentials.", status_code=401)

    # Hash password using same algorithm and salt as seeded in database
    salted_pwd = (password_raw + "-salt-tiny-bank").encode()
    hashed_attempt = hashlib.sha256(salted_pwd).hexdigest()

    if hashed_attempt != ADMIN_PASSWORD_HASH:
        raise BankException("Invalid administrative credentials.", status_code=401)

    return {
        "success": True,
        "message": "Authentication successful.",
        "user_id": ADMIN_USER_ID
    }