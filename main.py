import os
import models
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from database import SessionLocal, engine
from routers import inventory, auth
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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


                        # ======= CORS ==========


# 1. Daftarkan "Plat Nomor (Domain) frontend yang diizinkan masuk"
origins = [
    "http://localhost",
    "http://localhost:3000", #biasanya dipakai oleh React / Next.js
    "http://localhost:5173", # biasanya dipakai oleh vite/vue
    "*"                      # Bintang (*) = Izinkan SEMUA (Hanya untuk mode Developemnt/Belajar!)
]

# 2. Pasang Satpam CORS ke dalam aplikasi
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,        # Siapa saja yang boleh masuk? (Sesuai deftar origins)
    allow_credentials=True,         # 
    allow_methods=["*"],
    allow_headers=["*"],
)


#Jadikan folder "static" sebagai etalase publik
app.mount('/static', StaticFiles(directory='static'), name='static')
# ---- DAFTARKAN ROUTER (MENGHUBUNGKAN KABEL) ----
app.include_router(auth.router)
app.include_router(inventory.router)


# CONTROLER (Endpoint)
@app.get("/")
def read_root():
    return {"message": "Inventory API - Modular Version"} # pesan ini harus sama dengan test_read_root di test_main.py



