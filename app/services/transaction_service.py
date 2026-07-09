"""
This module manages financial operations: deposits, withdrawals, transfers,
transaction history, and administrative transfer approval requests.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.database import (
    ACCOUNTS,
    USERS,
    TRANSACTIONS,
    BANK_TAX_USER_ID,
    BANK_TAX_ACCOUNT_ID,
    TRANSFER_REQUESTS,
    db_lock,
)
from app.config import EXCHANGE_RATES
from app.models import TransactionType
from app.exceptions import (
    EntityNotFoundException,
    FrozenAccountException,
    InactiveUserException,
    LimitExceededException,
    InsufficientFundsException,
    BankException,
)
from app.services.helpers import (
    reset_daily_limits_if_needed,
    add_audit_log,
)

# ==============================================================================
# 💵 SECTION 1: DEPOSITS & WITHDRAWALS
# ==============================================================================

def deposit(account_id: str, amount: float, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Credits a specified bank account if it is active and not frozen.
    """
    with db_lock:
        if account_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Account with ID {account_id} does not exist.")
        
        acc = ACCOUNTS[account_id]
        if acc["is_frozen"]:
            raise FrozenAccountException(f"Operation rejected: account {account_id} is frozen.")
        
        user_id = acc["user_id"]
        if not USERS[user_id]["is_active"]:
            raise InactiveUserException("Operation rejected: account owner is inactive.")

        acc["balance"] = round(acc["balance"] + amount, 2)
        
        tx = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": account_id,
            "type": TransactionType.DEPOSIT,
            "amount": amount,
            "currency": acc["currency"],
            "related_account_id": None,
            "description": description,
            "timestamp": datetime.now()
        }
        TRANSACTIONS.append(tx)
        
        add_audit_log("DEPOSIT", f"Deposited {amount} {acc['currency']} into account {account_id}. New balance: {acc['balance']}.")
        return acc

def withdraw(account_id: str, amount: float) -> Dict[str, Any]:
    """
    Debits a specified account after checking balance and daily limits,
    while collecting a withdrawal tax credited to the bank tax account in CHF.
    """
    with db_lock:
        if account_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Account with ID {account_id} does not exist.")
        
        acc = ACCOUNTS[account_id]
        if acc["is_frozen"]:
            raise FrozenAccountException(f"Operation rejected: account {account_id} is frozen.")
        
        user_id = acc["user_id"]
        if user_id == BANK_TAX_USER_ID:
            raise BankException("Cannot withdraw from the bank system tax collection account.", status_code=400)
        
        if not USERS[user_id]["is_active"]:
            raise InactiveUserException("Operation rejected: account owner is inactive.")

        # Reset spending limits if local date changed
        reset_daily_limits_if_needed(acc)

        # Check daily withdrawal limits
        if acc["withdrawal_spent_today"] + amount > acc["daily_withdrawal_limit"]:
            raise LimitExceededException(
                f"Daily withdrawal limit exceeded. Remaining limit for today: "
                f"{acc['daily_withdrawal_limit'] - acc['withdrawal_spent_today']} {acc['currency']}."
            )

        # Calculate banking withdrawal tax (3 CHF for CHF account, 6 CHF equivalent for other currencies)
        if acc["currency"].value == "CHF":
            tax_in_chf = 3.0
            tax_in_acc_currency = 3.0
        else:
            tax_in_chf = 6.0
            tax_in_acc_currency = round(6.0 / EXCHANGE_RATES["CHF"] * EXCHANGE_RATES[acc["currency"].value], 2)

        # Verify sufficient balance to cover amount + withdrawal tax
        total_debit = round(amount + tax_in_acc_currency, 2)
        if acc["balance"] < total_debit:
            raise InsufficientFundsException(
                f"Insufficient funds to cover the withdrawal and banking taxes. "
                f"Required: {total_debit} {acc['currency']} (Withdrawal: {amount}, Tax: {tax_in_acc_currency}). "
                f"Available: {acc['balance']} {acc['currency']}."
            )

        # Perform debit
        acc["balance"] = round(acc["balance"] - total_debit, 2)
        acc["withdrawal_spent_today"] = round(acc["withdrawal_spent_today"] + amount, 2)

        # Credit bank tax collector account in CHF
        bank_acc = ACCOUNTS[BANK_TAX_ACCOUNT_ID]
        bank_acc["balance"] = round(bank_acc["balance"] + tax_in_chf, 2)

        now = datetime.now()

        # Customer withdrawal entry
        tx = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": account_id,
            "type": TransactionType.WITHDRAWAL,
            "amount": amount,
            "currency": acc["currency"],
            "related_account_id": None,
            "description": None,
            "timestamp": now
        }
        TRANSACTIONS.append(tx)

        # Customer tax debit entry
        tx_tax_out = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": account_id,
            "type": TransactionType.WITHDRAWAL,
            "amount": tax_in_acc_currency,
            "currency": acc["currency"],
            "related_account_id": BANK_TAX_ACCOUNT_ID,
            "description": "Bank taxes",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_tax_out)

        # Bank tax credit entry
        tx_tax_in = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": BANK_TAX_ACCOUNT_ID,
            "type": TransactionType.DEPOSIT,
            "amount": tax_in_chf,
            "currency": "CHF",
            "related_account_id": account_id,
            "description": "Bank taxes",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_tax_in)

        add_audit_log(
            "WITHDRAWAL_TAXED",
            f"Withdrawal of {amount} {acc['currency']} executed on {account_id}. "
            f"Bank tax collected: {tax_in_acc_currency} {acc['currency']} ({tax_in_chf} CHF)."
        )
        return acc


# ==============================================================================
# 💱 SECTION 2: MONEY TRANSFERS (WITH LIMIT LIMITATION FLOW)
# ==============================================================================

def transfer(source_id: str, target_id: str, amount: float) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Executes a transfer from the source account to the target account, applying taxes.
    If the transaction exceeds the daily transfer limit or maximum transfers count, 
    a PENDING request is created instead of failing, provided the source account has sufficient funds.
    """
    with db_lock:
        if source_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Source account {source_id} not found.")
        if target_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Target account {target_id} not found.")

        src = ACCOUNTS[source_id]
        tgt = ACCOUNTS[target_id]

        if src["is_frozen"]:
            raise FrozenAccountException(f"Operation rejected: source account {source_id} is frozen.")
        if tgt["is_frozen"]:
            raise FrozenAccountException(f"Operation rejected: target account {target_id} is frozen.")

        src_user = USERS[src["user_id"]]
        tgt_user = USERS[tgt["user_id"]]

        if src_user["id"] == BANK_TAX_USER_ID:
            raise BankException("The system tax collector account cannot perform outgoing transfers.", status_code=400)

        if not src_user["is_active"]:
            raise InactiveUserException("The owner of the source account is deactivated.")
        if not tgt_user["is_active"]:
            raise InactiveUserException("The owner of the target account is deactivated.")

        # Reset daily limits if date changed
        reset_daily_limits_if_needed(src)

        # Calculate taxes (same currency: 2 units, cross currency: 5 units + 5%)
        is_same_currency = src["currency"] == tgt["currency"]
        if is_same_currency:
            tax_in_source = 2.0
            tax_in_chf = round(tax_in_source / EXCHANGE_RATES[src["currency"].value] * EXCHANGE_RATES["CHF"], 2)
            net_target = amount
        else:
            tax_in_source = round(5.0 + 0.05 * amount, 2)
            tax_in_chf = round(tax_in_source / EXCHANGE_RATES[src["currency"].value] * EXCHANGE_RATES["CHF"], 2)
            amount_in_eur = amount / EXCHANGE_RATES[src["currency"].value]
            raw_target_amount = amount_in_eur * EXCHANGE_RATES[tgt["currency"].value]
            net_target = round(raw_target_amount, 2)

        # Verify sufficient balance to cover amount + transfer tax
        total_debit = round(amount + tax_in_source, 2)
        if src["balance"] < total_debit:
            raise InsufficientFundsException(
                f"Insufficient funds to cover the transfer and taxes. "
                f"Required: {total_debit} {src['currency']} (Transfer: {amount}, Tax: {tax_in_source}). "
                f"Available: {src['balance']} {src['currency']}."
            )

        # Check if the transfer exceeds daily limits
        exceeds_amount_limit = src["transfer_spent_today"] + amount > src["daily_transfer_limit"]
        exceeds_count_limit = src["transfers_count_today"] + 1 > src["max_daily_transfers"]

        if exceeds_amount_limit or exceeds_count_limit:
            # Create a PENDING request instead of throwing an error immediately
            req_id = str(uuid.uuid4())
            transfer_req = {
                "id": req_id,
                "source_account_id": source_id,
                "target_account_id": target_id,
                "amount": amount,
                "status": "PENDING",
                "timestamp": datetime.now()
            }
            TRANSFER_REQUESTS.append(transfer_req)
            add_audit_log(
                "TRANSFER_REQUESTED", 
                f"Transfer request {req_id} ({amount} {src['currency']} from {source_id} to {target_id}) created "
                f"because it exceeds daily limits (limit: {src['daily_transfer_limit']}, max count: {src['max_daily_transfers']})."
            )
            return None, None, transfer_req

        # Execute transfer immediately
        src["balance"] = round(src["balance"] - total_debit, 2)
        tgt["balance"] = round(tgt["balance"] + net_target, 2)

        # Credit bank tax account in CHF
        bank_acc = ACCOUNTS[BANK_TAX_ACCOUNT_ID]
        bank_acc["balance"] = round(bank_acc["balance"] + tax_in_chf, 2)

        # Update spent limits
        src["transfer_spent_today"] = round(src["transfer_spent_today"] + amount, 2)
        src["transfers_count_today"] += 1

        # Record transactions
        now = datetime.now()
        tx_id_out = str(uuid.uuid4())
        tx_id_in = str(uuid.uuid4())

        tx_out = {
            "id": tx_id_out,
            "sequence": len(TRANSACTIONS),
            "account_id": source_id,
            "type": TransactionType.TRANSFER_OUT,
            "amount": amount,
            "currency": src["currency"],
            "related_account_id": target_id,
            "description": None,
            "timestamp": now
        }
        TRANSACTIONS.append(tx_out)

        tx_in = {
            "id": tx_id_in,
            "sequence": len(TRANSACTIONS),
            "account_id": target_id,
            "type": TransactionType.TRANSFER_IN,
            "amount": net_target,
            "currency": tgt["currency"],
            "related_account_id": source_id,
            "description": None,
            "timestamp": now
        }
        TRANSACTIONS.append(tx_in)

        # Client tax debit entry
        tx_tax_out = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": source_id,
            "type": TransactionType.WITHDRAWAL,
            "amount": tax_in_source,
            "currency": src["currency"],
            "related_account_id": BANK_TAX_ACCOUNT_ID,
            "description": "Bank taxes",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_tax_out)

        # Bank tax credit entry
        tx_tax_in = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": BANK_TAX_ACCOUNT_ID,
            "type": TransactionType.DEPOSIT,
            "amount": tax_in_chf,
            "currency": "CHF",
            "related_account_id": source_id,
            "description": "Bank taxes",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_tax_in)

        add_audit_log(
            "TRANSFER_TAXED",
            f"Transfer of {amount} {src['currency']} from {source_id} to {target_id} executed immediately. "
            f"Bank tax collected: {tax_in_source} {src['currency']} ({tax_in_chf} CHF)."
        )

        return src, tgt, None


# ==============================================================================
# 🛡️ SECTION 3: ADMINISTRATIVE TRANSFER APPROVALS (PENDING QUEUE)
# ==============================================================================

def list_pending_transfers() -> List[Dict[str, Any]]:
    """
    Lists all pending transfer requests for admin overview.
    """
    with db_lock:
        return [req for req in TRANSFER_REQUESTS if req["status"] == "PENDING"]

def resolve_transfer_request(request_id: str, approve: bool) -> Dict[str, Any]:
    """
    Approves or rejects a pending transfer request.
    If approved, executes the transfer (bypassing daily limits, but checking balance and applying taxes).
    """
    with db_lock:
        # Find request
        req = next((r for r in TRANSFER_REQUESTS if r["id"] == request_id), None)
        if not req:
            raise EntityNotFoundException(f"Transfer request {request_id} not found.")
        if req["status"] != "PENDING":
            raise BankException("This request is already resolved.", status_code=400)

        if not approve:
            req["status"] = "REJECTED"
            add_audit_log("TRANSFER_REJECTED", f"Transfer request {request_id} was rejected by the admin.")
            
            # Record rejected transaction entry for history
            source_id = req["source_account_id"]
            target_id = req["target_account_id"]
            amount = req["amount"]
            if source_id in ACCOUNTS:
                src = ACCOUNTS[source_id]
                tx_rej = {
                    "id": str(uuid.uuid4()),
                    "sequence": len(TRANSACTIONS),
                    "account_id": source_id,
                    "type": TransactionType.TRANSFER_REJECTED,
                    "amount": amount,
                    "currency": src["currency"],
                    "related_account_id": target_id,
                    "description": "Rejected by the bank",
                    "timestamp": datetime.now()
                }
                TRANSACTIONS.append(tx_rej)
            return req

        # Executing approval
        source_id = req["source_account_id"]
        target_id = req["target_account_id"]
        amount = req["amount"]

        if source_id not in ACCOUNTS or target_id not in ACCOUNTS:
            req["status"] = "REJECTED"
            add_audit_log("TRANSFER_REJECTED", f"Transfer request {request_id} rejected automatically (account deleted).")
            raise EntityNotFoundException("One of the accounts involved in the request no longer exists.")

        src = ACCOUNTS[source_id]
        tgt = ACCOUNTS[target_id]

        if src["is_frozen"] or tgt["is_frozen"]:
            raise FrozenAccountException("Cannot approve transfer because one of the accounts is frozen.")

        # Recalculate taxes
        is_same_currency = src["currency"] == tgt["currency"]
        if is_same_currency:
            tax_in_source = 2.0
            tax_in_chf = round(tax_in_source / EXCHANGE_RATES[src["currency"].value] * EXCHANGE_RATES["CHF"], 2)
            net_target = amount
        else:
            tax_in_source = round(5.0 + 0.05 * amount, 2)
            tax_in_chf = round(tax_in_source / EXCHANGE_RATES[src["currency"].value] * EXCHANGE_RATES["CHF"], 2)
            amount_in_eur = amount / EXCHANGE_RATES[src["currency"].value]
            raw_target_amount = amount_in_eur * EXCHANGE_RATES[tgt["currency"].value]
            net_target = round(raw_target_amount, 2)

        total_debit = round(amount + tax_in_source, 2)
        if src["balance"] < total_debit:
            raise InsufficientFundsException(
                f"Cannot approve transfer. Source account has insufficient funds: {src['balance']} {src['currency']}."
            )

        # Debit & credit (bypassing spending limits)
        src["balance"] = round(src["balance"] - total_debit, 2)
        tgt["balance"] = round(tgt["balance"] + net_target, 2)

        # Credit bank tax account in CHF
        bank_acc = ACCOUNTS[BANK_TAX_ACCOUNT_ID]
        bank_acc["balance"] = round(bank_acc["balance"] + tax_in_chf, 2)

        # Record transactions
        now = datetime.now()
        tx_id_out = str(uuid.uuid4())
        tx_id_in = str(uuid.uuid4())

        tx_out = {
            "id": tx_id_out,
            "sequence": len(TRANSACTIONS),
            "account_id": source_id,
            "type": TransactionType.TRANSFER_OUT,
            "amount": amount,
            "currency": src["currency"],
            "related_account_id": target_id,
            "description": "Approved by the bank",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_out)

        tx_in = {
            "id": tx_id_in,
            "sequence": len(TRANSACTIONS),
            "account_id": target_id,
            "type": TransactionType.TRANSFER_IN,
            "amount": net_target,
            "currency": tgt["currency"],
            "related_account_id": source_id,
            "description": "Approved by the bank",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_in)

        # Client tax debit entry
        tx_tax_out = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": source_id,
            "type": TransactionType.WITHDRAWAL,
            "amount": tax_in_source,
            "currency": src["currency"],
            "related_account_id": BANK_TAX_ACCOUNT_ID,
            "description": "Bank taxes",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_tax_out)

        # Bank tax credit entry
        tx_tax_in = {
            "id": str(uuid.uuid4()),
            "sequence": len(TRANSACTIONS),
            "account_id": BANK_TAX_ACCOUNT_ID,
            "type": TransactionType.DEPOSIT,
            "amount": tax_in_chf,
            "currency": "CHF",
            "related_account_id": source_id,
            "description": "Bank taxes",
            "timestamp": now
        }
        TRANSACTIONS.append(tx_tax_in)

        # Update request status
        req["status"] = "APPROVED"

        add_audit_log(
            "TRANSFER_APPROVED",
            f"Transfer request {request_id} approved and executed. "
            f"Bank tax collected: {tax_in_source} {src['currency']} ({tax_in_chf} CHF)."
        )
        return req


# ==============================================================================
# 📜 SECTION 4: TRANSACTION HISTORY
# ==============================================================================

def get_transaction_history(
    account_id: str,
    tx_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Returns the sorted and paginated transaction history for a given account.
    """
    with db_lock:
        if account_id not in ACCOUNTS:
            raise EntityNotFoundException(f"Account with ID {account_id} does not exist.")

        account_txs = [tx for tx in TRANSACTIONS if tx["account_id"] == account_id]
        account_txs.sort(key=lambda x: (x["timestamp"], x.get("sequence", 0)), reverse=True)

        if tx_type:
            account_txs = [tx for tx in account_txs if tx["type"].value == tx_type]

        if from_date:
            account_txs = [tx for tx in account_txs if tx["timestamp"] >= from_date]

        return account_txs[offset: offset + limit]