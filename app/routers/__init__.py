"""
Exposition of the different routing modules as a unified package.
"""

from app.routers.user_router import router as user_router
from app.routers.account_router import router as account_router
from app.routers.transaction_router import router as transaction_router
from app.routers.audit_router import router as audit_router
from app.routers.auth_router import router as auth_router