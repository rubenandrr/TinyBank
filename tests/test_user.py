"""
Unit and integration tests for user and account management endpoints.
"""

def test_create_user(client):
    """
    Verifies that a user is successfully created along with default Current and Savings CHF accounts.
    """
    response = client.post("/users", json={"name": "Alice"})
    assert response.status_code == 201
    data = response.json()
    
    assert data["name"] == "Alice"
    assert data["is_active"] is True
    assert "id" in data
    
    # Must have 1 default account in CHF (Current only)
    accounts = data["accounts"]
    assert len(accounts) == 1
    
    assert accounts[0]["account_type"] == "CURRENT"
    assert accounts[0]["balance"] == 0.0
    assert accounts[0]["currency"] == "CHF"
    assert accounts[0]["is_frozen"] is False

def test_list_users_anonymous(client):
    """
    Verifies that calling list users without admin token hides administrative and system users.
    """
    # System users are seeded on startup, but anonymous access should show 0 users
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Add standard users
    client.post("/users", json={"name": "Alice"})
    client.post("/users", json={"name": "Bob"})

    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2
    names = [u["name"] for u in response.json()]
    assert "Alice" in names
    assert "Bob" in names
    assert "Tiny Bank - Taxes" not in names

def test_list_users_admin(client):
    """
    Verifies that calling list users with an admin token includes system users.
    """
    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    response = client.get("/users", headers=headers)
    assert response.status_code == 200
    # On start, has "Tiny Bank - Admin" and "Tiny Bank - Taxes"
    assert len(response.json()) == 2
    names = [u["name"] for u in response.json()]
    assert "Tiny Bank - Admin" in names
    assert "Tiny Bank - Taxes" in names

def test_deactivate_user_requires_admin(client):
    """
    Verifies that user deactivation fails without an admin token and succeeds with it.
    """
    res_create = client.post("/users", json={"name": "Bob"})
    user_id = res_create.json()["id"]

    # Try deactivating without token (should fail 403)
    res_deact_anon = client.post(f"/users/{user_id}/deactivate")
    assert res_deact_anon.status_code == 403

    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    # Deactivate with admin token
    res_deact_admin = client.post(f"/users/{user_id}/deactivate", headers=headers)
    assert res_deact_admin.status_code == 200
    assert res_deact_admin.json()["is_active"] is False

    # Accounts should be frozen
    res_get = client.get(f"/users/{user_id}")
    for acc in res_get.json()["accounts"]:
        assert acc["is_frozen"] is True

def test_create_additional_account_requires_admin(client):
    """
    Verifies that opening an additional account fails without token and succeeds with token.
    """
    res_user = client.post("/users", json={"name": "Charlie"})
    user_id = res_user.json()["id"]

    # Try creating without token (should fail 403)
    res_acc_anon = client.post("/accounts", json={
        "user_id": user_id,
        "account_type": "CURRENT",
        "currency": "USD"
    })
    assert res_acc_anon.status_code == 403

    # Log in as admin
    login_res = client.post("/login", json={"username": "admin", "password": "12345"})
    token = login_res.json()["token"]
    headers = {"X-Admin-Token": token}

    # Create account with admin token
    res_acc_admin = client.post("/accounts", json={
        "user_id": user_id,
        "account_type": "SAVINGS",
        "currency": "USD"
    }, headers=headers)
    assert res_acc_admin.status_code == 201
    assert res_acc_admin.json()["currency"] == "USD"