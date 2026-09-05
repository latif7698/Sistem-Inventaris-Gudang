def test_register_user(client):
    response = client.post(
        "/register",
        json={"username": "tester_latif", "password": "passwordrahasia"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "tester_latif"

def test_register_duplicate_user(client):
    client.post("/register", json={"username": "duplicate_user", "password": "password123"})
    response = client.post("/register", json={"username": "duplicate_user", "password": "password123"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

def test_login_user(client):
    client.post(
        "/register",
        json={"username": "tester_login", "password": "123"}
    )

    response = client.post(
        "/login",
        data={"username": "tester_login", "password": "123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post("/register", json={"username": "user_wrong_pass", "password": "correct_pass"})
    response = client.post("/login", data={"username": "user_wrong_pass", "password": "wrong_password"})
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower() or "password" in response.json()["detail"].lower()
