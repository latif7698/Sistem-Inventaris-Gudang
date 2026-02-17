def test_register_user(client):
    # Skenario: daftar user baru
    response = client.post(
        "/register",
        json={"username": "tester_latif", "password": "passwordrahasia"}
    )
    # harapan
    # 1. status 201 created (berhasil)
    assert response.status_code == 201
    # balasannya harus ada usernamenya
    assert response.json()["username"] == "tester_latif"

def test_login_user(client):
    # 1. daftar dulu karena db nya selalu bersih kosong tiap test
    client.post(
        "/register",
        json={"username": "tester_login", "password": "123"}
    )

    # 2. coba login (ingat! login pakai Form Data, bukan JSON)
    response = client.post(
        "/login",
        data = {"username": "tester_login", "password": "123"}
    )

    # harapan
    # 1. status 200 OK
    assert response.status_code == 200
    # 2. harus dapat token
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

