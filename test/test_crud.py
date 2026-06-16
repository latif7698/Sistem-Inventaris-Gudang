def test_create_item(client):
    client.post("/register", json={"username": "juragan", "password": "123"})
    login_res = client.post("/login", data={"username": "juragan", "password": "123"})
    token = login_res.json()["access_token"]

    response = client.post(
        "/inventory",
        json={
            "id": 99,
            "name": "Barang Test",
            "price":5000,
            "stock": 10,
            "description": "Ini barang simulasi"
        },
        headers={"Authorization": f"Bearer {token}"} 
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Barang Test"
    assert response.json()["owner_id"] is not None 