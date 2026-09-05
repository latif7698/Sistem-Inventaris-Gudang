from fastapi.testclient import TestClient
from main import app 

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Inventory API - Modular Version"}

def test_page_not_found():
    response = client.get("/halaman-ghaib")
    assert response.status_code == 404

def test_read_inventory_without_token():
    response = client.get("/inventory/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
