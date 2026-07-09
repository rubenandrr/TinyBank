"""
Unit and integration tests for financial transaction endpoints,
including limits, automatic taxes, and administrative approval requests.
"""

from datetime import datetime
import app.config

def test_deposit(client):
    """
    Verifies that a deposit successfully credits the account without any tax.
    """
    res_user = client.post("/users", json={"name": "Alice"})
    acc_id = res_user.json()["accounts"][0]["id"]

    # Deposit 250.50 CHF
    res_dep = client.post(f"/accounts/{acc_id}/deposit", json={"amount": 250.50})
    assert res_dep.status_code == 200
    assert res_dep.json()["balance"] == 250.50

    # Negative amount deposits must be blocked by Pydantic (422 error)
    res_invalid = client.post(f"/accounts/{acc_id}/deposit", json={"amount": -50.0})
    assert res_invalid.status_code == 422

def test_withdrawal_and_limits(client):
    """
    Verifies withdrawals, balance provision checks (including tax),
    and daily withdrawal limits.
    """
    # Log in as admin to update limits
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    res_user = client.post("/users", json={"name": "Bob"})
    acc_id = res_user.json()["accounts"][0]["id"]

    # Deposit 2000 CHF
    client.post(f"/accounts/{acc_id}/deposit", json={"amount": 2000.0})

    # Withdraw 500 CHF (default limit = 1000 CHF)
    # Tax = 3.0 CHF. Total debited = 503.0 CHF. Balance = 1497.0 CHF.
    res_wit1 = client.post(f"/accounts/{acc_id}/withdraw", json={"amount": 500.0})
    assert res_wit1.status_code == 200
    assert res_wit1.json()["balance"] == 1497.0
    assert res_wit1.json()["withdrawal_spent_today"] == 500.0

    # Withdrawal of 600 CHF more must fail (500 + 600 = 1100 > 1000 limit)
    res_wit2 = client.post(f"/accounts/{acc_id}/withdraw", json={"amount": 600.0})
    assert res_wit2.status_code == 400
    assert "limit" in res_wit2.json()["detail"].lower()

    # Update limit to 1500 CHF (requires admin token)
    res_lim = client.put(f"/accounts/{acc_id}/limits", json={"daily_withdrawal_limit": 1500.0}, headers=headers)
    assert res_lim.status_code == 200
    assert res_lim.json()["daily_withdrawal_limit"] == 1500.0

    # Withdrawal of 600 CHF now succeeds
    # Tax = 3.0 CHF. Debit = 603.0 CHF. Balance = 1497.0 - 603.0 = 894.0 CHF.
    res_wit3 = client.post(f"/accounts/{acc_id}/withdraw", json={"amount": 600.0})
    assert res_wit3.status_code == 200
    assert res_wit3.json()["balance"] == 894.0
    assert res_wit3.json()["withdrawal_spent_today"] == 1100.0

    # Raise limit high to test balance check bypassing limits
    client.put(f"/accounts/{acc_id}/limits", json={"daily_withdrawal_limit": 5000.0}, headers=headers)

    # Attempt to withdraw more than remaining balance
    # Balance is 894 CHF, requesting 892 CHF + 3 CHF tax = 895 CHF required (should fail)
    res_insufficient = client.post(f"/accounts/{acc_id}/withdraw", json={"amount": 892.0})
    assert res_insufficient.status_code == 400
    assert "insufficient" in res_insufficient.json()["detail"].lower()

def test_freeze_and_unfreeze_account(client):
    """
    Verifies that a frozen account blocks operations.
    """
    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    res_user = client.post("/users", json={"name": "Charlie"})
    acc_id = res_user.json()["accounts"][0]["id"]

    # Freeze account (requires admin token)
    client.post(f"/accounts/{acc_id}/freeze", headers=headers)

    # Withdrawal fails
    res_wit = client.post(f"/accounts/{acc_id}/withdraw", json={"amount": 50.0})
    assert res_wit.status_code == 400
    assert "frozen" in res_wit.json()["detail"].lower()

    # Unfreeze (requires admin token)
    client.post(f"/accounts/{acc_id}/unfreeze", headers=headers)

    # Deposit works now
    res_dep = client.post(f"/accounts/{acc_id}/deposit", json={"amount": 100.0})
    assert res_dep.status_code == 200
    assert res_dep.json()["balance"] == 100.0

def test_transfer_same_currency(client):
    """
    Verifies standard transfer between two accounts of the same currency (CHF -> CHF).
    Alice sends 200 CHF. Pays 2 CHF tax. Total debit = 202 CHF.
    """
    user_a = client.post("/users", json={"name": "Alice"}).json()
    user_b = client.post("/users", json={"name": "Bob"}).json()

    acc_a_id = user_a["accounts"][0]["id"]
    acc_b_id = user_b["accounts"][0]["id"]

    # Deposit 500 CHF to Alice
    client.post(f"/accounts/{acc_a_id}/deposit", json={"amount": 500.0})

    # Alice sends 200 CHF to Bob (within 5000 CHF limit)
    res_transfer = client.post("/transfers", json={
        "source_account_id": acc_a_id,
        "target_account_id": acc_b_id,
        "amount": 200.0
    })
    assert res_transfer.status_code == 200
    data = res_transfer.json()
    
    assert data["source_account"]["balance"] == 298.0  # 500 - 200 - 2 tax
    assert data["target_account"]["balance"] == 200.0
    assert data["source_account"]["transfer_spent_today"] == 200.0
    assert data["source_account"]["transfers_count_today"] == 1

def test_transfer_multi_currency(client):
    """
    Verifies cross-currency transfers (CHF -> USD).
    """
    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    app.config.EXCHANGE_RATES.clear()
    app.config.EXCHANGE_RATES.update({
        "EUR": 1.0,
        "CHF": 0.96,
        "USD": 1.08,
    })

    user_a = client.post("/users", json={"name": "Alice"}).json()
    acc_a_id = user_a["accounts"][0]["id"]

    user_b = client.post("/users", json={"name": "Bob"}).json()
    
    # Create Bob's USD account (requires admin token)
    acc_b_usd = client.post("/accounts", json={
        "user_id": user_b["id"],
        "account_type": "SAVINGS",
        "currency": "USD"
    }, headers=headers).json()
    acc_b_id = acc_b_usd["id"]

    # Deposit 200 CHF to Alice
    client.post(f"/accounts/{acc_a_id}/deposit", json={"amount": 200.0})

    # Alice sends 100 CHF to Bob
    # Tax = 5 CHF + 5% = 10 CHF. Alice debited 110 CHF.
    # Bob receives: 100 CHF / 0.96 * 1.08 = 112.50 USD
    res_transfer = client.post("/transfers", json={
        "source_account_id": acc_a_id,
        "target_account_id": acc_b_id,
        "amount": 100.0
    })
    assert res_transfer.status_code == 200
    data = res_transfer.json()
    
    assert data["source_account"]["balance"] == 90.0
    assert data["target_account"]["balance"] == 112.50

def test_transaction_history(client):
    """
    Verifies transaction history query with pagination.
    """
    res_user = client.post("/users", json={"name": "Alice"}).json()
    acc_id = res_user["accounts"][0]["id"]

    client.post(f"/accounts/{acc_id}/deposit", json={"amount": 100.0})
    client.post(f"/accounts/{acc_id}/withdraw", json={"amount": 40.0})
    client.post(f"/accounts/{acc_id}/deposit", json={"amount": 200.0})

    res_hist = client.get(f"/accounts/{acc_id}/transactions")
    assert res_hist.status_code == 200
    txs = res_hist.json()
    assert len(txs) == 4

def test_audit_trail(client):
    """
    Verifies audit logs query (requires admin token).
    """
    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    res_user = client.post("/users", json={"name": "AuditUser"}).json()
    acc_id = res_user["accounts"][0]["id"]
    client.post(f"/accounts/{acc_id}/deposit", json={"amount": 100.0})

    # Query without token should fail
    res_audit_anon = client.get("/audit")
    assert res_audit_anon.status_code == 403

    # Query with token succeeds
    res_audit_admin = client.get("/audit", headers=headers)
    assert res_audit_admin.status_code == 200
    assert len(res_audit_admin.json()) >= 3

# ==============================================================================
# 🛡️ NEW FEATURE TEST: TRANSFER LIMIT REQUESTS & APPROVAL
# ==============================================================================

def test_transfer_exceeding_limits_requires_approval(client):
    """
    Verifies that a transfer exceeding the daily limit creates a PENDING request
    and can be approved/rejected by the admin.
    """
    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    user_a = client.post("/users", json={"name": "Alice"}).json()
    user_b = client.post("/users", json={"name": "Bob"}).json()

    acc_a_id = user_a["accounts"][0]["id"]
    acc_b_id = user_b["accounts"][0]["id"]

    # Deposit 6000 CHF to Alice
    client.post(f"/accounts/{acc_a_id}/deposit", json={"amount": 6000.0})

    # Alice sends 5500 CHF (exceeds default daily transfer limit of 5000.0 CHF)
    # Provision is OK (6000 >= 5500 + 2 tax)
    res_transfer = client.post("/transfers", json={
        "source_account_id": acc_a_id,
        "target_account_id": acc_b_id,
        "amount": 5500.0
    })
    
    # Must return 202 Accepted
    assert res_transfer.status_code == 202
    data = res_transfer.json()
    assert data["status"] == "PENDING"
    assert "limit" in data["message"].lower()
    
    req_id = data["request"]["id"]
    assert req_id is not None
    
    # Check pending list as admin
    res_pending = client.get("/admin/transfers/requests", headers=headers)
    assert res_pending.status_code == 200
    pending_ids = [r["id"] for r in res_pending.json()]
    assert req_id in pending_ids

    # Approve request as admin
    res_resolve = client.post(
        f"/admin/transfers/requests/{req_id}/resolve",
        json={"approve": True},
        headers=headers
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "APPROVED"

    # Verify balances: Alice debited 5502 CHF, Bob credited 5500 CHF
    res_user_a = client.get(f"/users/{user_a['id']}")
    res_user_b = client.get(f"/users/{user_b['id']}")
    
    assert res_user_a.json()["accounts"][0]["balance"] == 498.0
    assert res_user_b.json()["accounts"][0]["balance"] == 5500.0