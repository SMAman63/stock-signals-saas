import pytest


@pytest.mark.asyncio
async def test_signup_success(client, test_user_data):
    """Test successful user signup."""
    response = await client.post("/auth/signup", json=test_user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client, test_user_data):
    """Test signup with duplicate email fails."""
    # First signup
    await client.post("/auth/signup", json=test_user_data)
    
    # Second signup with same email
    response = await client.post("/auth/signup", json=test_user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client, test_user_data):
    """Test successful login."""
    # First signup
    await client.post("/auth/signup", json=test_user_data)
    
    # Then login
    response = await client.post("/auth/login", json=test_user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user_data):
    """Test login with wrong password."""
    # First signup
    await client.post("/auth/signup", json=test_user_data)
    
    # Login with wrong password
    response = await client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client, test_user_data):
    """Test getting current user when authenticated."""
    # Signup and get token
    signup_response = await client.post("/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["is_paid"] == False


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    """Test getting current user without authentication fails."""
    response = await client.get("/auth/me")
    
    assert response.status_code == 403  # No auth header


@pytest.mark.asyncio
async def test_signals_free_user(client, test_user_data):
    """Test free user gets limited signals."""
    # Signup and get token
    signup_response = await client.post("/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    
    # Get signals
    response = await client.get(
        "/signals",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_limited"] == True
    assert len(data["signals"]) == 3  # Free user limit
    assert data["total_count"] == 8  # Total signals available
