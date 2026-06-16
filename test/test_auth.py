def test_register_user(client):
    response = client.post(
        "/register",
        json={"username": "tester_latif", "password": "passwordrahasia"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "tester_latif"

def test_login_user(client):
    client.post(
        "/register",
        json={"username": "tester_login", "password": "123"}
    )

    response = client.post(
        "/login",
        data = {"username": "tester_login", "password": "123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

