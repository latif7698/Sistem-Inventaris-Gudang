def test_create_item(client):
    # 1. Reegister & Login untuk dapat token
    client.post("/register", json={"username": "juragan", "password": "123"})
    login_res = client.post("/login", data={"username": "juragan", "password": "123"})
    token = login_res.json()["access_token"]

    # 2. Create Barang (Pakai Header Authorization)
    response = client.post(
        "/inventory",
        json={
            "id": 99,
            "name": "Barang Test",
            "price":5000,
            "stock": 10,
            "description": "Ini barang simulasi"
        },
        headers={"Authorization": f"Bearer {token}"} #<-- Kunci masuk    
    )

    # harapan
    assert response.status_code == 201
    assert response.json()["name"] == "Barang Test"
    assert response.json()["owner_id"] is not None # Pastikan ada pemiliknya