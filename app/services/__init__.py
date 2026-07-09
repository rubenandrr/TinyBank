"""
Exposes service modules as a unified package.
Allows importing all functions directly via 'from app.services import ...'
"""

from app.services.user_service import (
    create_user,
    get_user,
    list_users,
    deactivate_user,
)

from app.services.account_service import (
    create_account,
    freeze_account,
    unfreeze_account,
    update_account_limits,
    delete_account,
)

from app.services.transaction_service import (
    deposit,
    withdraw,
    transfer,
    list_pending_transfers,
    resolve_transfer_request,
    get_transaction_history,
)

from app.services.auth_service import (
    verify_admin_login,
    validate_admin_token,
)

from app.services.audit_service import (
    get_audit_logs,
)