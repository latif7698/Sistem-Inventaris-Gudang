from fastapi.testclient import TestClient
from main import app # import aplikasi utama kita

#ini adalah robot penguji (Client palsu)
client = TestClient(app)

# -- SKENARIO 1: CEK HALAMAN UTAMA --
def test_read_root():
    #Robot mencoba akses GET/ (root)
    response = client.get("/")

    #harapan kita:
    #1. Status harus 200 OK
    assert response.status_code == 200

    # 2. Pesan harus sesuai (Cek main.py kamu, pesannya apa)
    # kalau di main.py kamu return {"message": "Inventory API..."}, sesuaikan teksnya
    assert response.json() == {"message": "Inventory API - Modular Version"}

# -- SKENARIO 2: CEK HALAMAN YANG GAK ADA --
def tetst_page_not_found():
    # Robot mencoba akses halaman ngawur
    response = client.get("/halaman-ghaib")

    #Harapan: Harus Error 404
    assert response.status_code == 404

# -- SKENARIO 3: CEK SCURITY (MALING MASUK) ---
def test_read_inventory_without_token():
    # Robot mencoba akses GET/inventory tanpa bawa token login
    response = client.get("/inventory")

    #Harapan: DITOLAK (401 Unauthorized)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}