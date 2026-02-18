import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from database import SessionLocal, engine
import models
from routers import inventory, auth

# panggil ini SEBELUM setup DB agar variable .env terbaca
load_dotenv()
# setup DB (akan otomatis membuat tabel di neon)
print("Sedang mencoba membuat tabel...")
models.Base.metadata.create_all(bind=engine)
print("Proses pembuatan table selesai")


# 1. Buat deskripsi panjang yang elegan (Bisa pakai Markdown!)
deskripsi_api = """
**Sistem Inventaris Gudang API** membantu perusahaan mencatat dan melacak keluar masuk barang secara *real-time*. 🚀

## 📦Fitur Utama:
* **Authentikasi**: Sistem *Login* dan *Register* berlapis keamanan JWT Token.
* **Manajemen Barang**: Operasi CRUD (Create, Read, Update, Delete) untuk data inventaris.

*Dibuat dengan Python, FastAPI dan Postgresql (Neon Cloud).*
"""

app = FastAPI(
    title="Warehouse Inventory API",
    description=deskripsi_api,
    version="1.0.0",
    contact={
        "name": "Latif - Backend Engineer",
        "url": "https://github.com/latif7698",
        "email": "email.profesional.aasepabdullatip@gmail.com",
    },
    license_info={
        "name": "MIT License",
    }
)

# ---- DAFTARKAN ROUTER (MENGHUBUNGKAN KABEL) ----
app.include_router(auth.router)
app.include_router(inventory.router)


# CONTROLER (Endpoint)
@app.get("/")
def read_root():
    return {"message": "Inventory API - Modular Version"} # pesan ini harus sama dengan test_read_root di test_main.py



