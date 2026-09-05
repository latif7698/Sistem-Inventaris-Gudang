def test_create_and_read_item(client):
    client.post("/register", json={"username": "juragan", "password": "123"})
    login_res = client.post("/login", data={"username": "juragan", "password": "123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create item
    response = client.post(
        "/inventory",
        json={
            "name": "Barang Test",
            "price": 5000,
            "stock": 10,
            "description": "Ini barang simulasi"
        },
        headers=headers 
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Barang Test"
    item_id = data["id"]

    # 2. Read items
    read_res = client.get("/inventory/", headers=headers)
    assert read_res.status_code == 200
    items = read_res.json()
    assert len(items) >= 1

    # 3. Adjust stock
    adjust_res = client.patch(f"/inventory/{item_id}/stock", json={"amount": 5, "type": "IN"}, headers=headers)
    assert adjust_res.status_code == 200
    assert adjust_res.json()["new_stock"] == 15

    # 4. Update item
    update_res = client.put(
        f"/inventory/{item_id}",
        json={
            "name": "Barang Test Updated",
            "price": 6000,
            "stock": 15,
            "description": "Sudah diupdate"
        },
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Barang Test Updated"

    # 5. Soft Delete
    del_res = client.delete(f"/inventory/{item_id}", headers=headers)
    assert del_res.status_code == 200

    # 6. Read again - should not appear in default list
    read_after_del = client.get("/inventory/", headers=headers)
    assert not any(i["id"] == item_id for i in read_after_del.json())

def test_unauthorized_access_forbidden(client):
    # Register user 1 and user 2
    client.post("/register", json={"username": "user1", "password": "123"})
    client.post("/register", json={"username": "user2", "password": "123"})

    token1 = client.post("/login", data={"username": "user1", "password": "123"}).json()["access_token"]
    token2 = client.post("/login", data={"username": "user2", "password": "123"}).json()["access_token"]

    # User 1 creates an item
    res = client.post(
        "/inventory",
        json={"name": "Barang User 1", "price": 1000, "stock": 5},
        headers={"Authorization": f"Bearer {token1}"}
    )
    item_id = res.json()["id"]

    # User 2 tries to delete User 1 item
    del_res = client.delete(f"/inventory/{item_id}", headers={"Authorization": f"Bearer {token2}"})
    assert del_res.status_code == 403
