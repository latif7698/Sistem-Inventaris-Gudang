from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request
from routers import inventory, auth
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import inventory, transactions
from db.init_db import init_db
import os
import time
import asyncio
import logging
load_dotenv()

deskripsi_api = """
**Sistem Inventaris Gudang API** membantu perusahaan mencatat dan melacak keluar masuk barang secara *real-time*. 🚀

## 📦Fitur Utama:
* **Authentikasi**: Sistem *Login* dan *Register* berlapis keamanan JWT Token.
* **Manajemen Barang**: Operasi CRUD (Create, Read, Update, Delete) untuk data inventaris.

*Dibuat dengan Python, FastAPI dan Postgresql (Neon Cloud).*

* API ini dikembangkan dengan fokus pada keamanan, skalabilitas, dan maintainability.
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

#logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")


                        # ======= CORS ==========


# 1. Daftarkan  (Domain) frontend yang diizinkan masuk
origins_env = os.getenv("CORS_ORIGINS", "")
origins = origins_env.split(",") if origins_env else ["http://localhost:3000"]


# 2. Pasang security CORS ke dalam aplikasi
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,        # Siapa saja yang boleh masuk? (Sesuai deftar origins)
    allow_credentials=True,         # 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# ---- DAFTARKAN ROUTER (MENGHUBUNGKAN KABEL) ----
#Jadikan folder "static" sebagai etalase publik
app.mount('/static', StaticFiles(directory='static'), name='static')
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(transactions.router)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # ---------------------------------------------------------
    # FASE 1: TAMU DATANG (REQUEST MASUK)
    # ---------------------------------------------------------
    start_time = time.time() # Catat jam kedatangan
    logger.info(f" {request.method} {request.url.path} - START")

    # ---------------------------------------------------------
    # FASE 2: TAMU MASUK KE RUANGAN (EKSEKUSI ENDPOINT)
    # ---------------------------------------------------------
    # call_next artinya: "Silakan masuk ke fungsi endpoint tujuanmu"
    response = await call_next(request)

    # ---------------------------------------------------------
    # FASE 3: TAMU KELUAR (RESPONSE SIAP DIKIRIM)
    # ---------------------------------------------------------
    process_time = time.time() - start_time # Hitung durasi
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    # print(f"REQUEST SELESAI DALAM WAKTU: {process_time:.4f} detik")
    
    # Kita bisa menyisipkan data rahasia di Header Response
    # Header custom biasanya diawali dengan 'X-'
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# CONTROLER (Endpoint)
@app.get("/")
async def read_root():
    await asyncio.sleep(0.5)
    return {"message": "Inventory API - Modular Version"} # pesan ini harus sama dengan test_read_root di test_main.py
