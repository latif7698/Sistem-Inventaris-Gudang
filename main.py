#Standar Library
import os
import time
import asyncio
import logging

#Third Party
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

#Local Modules
from contextlib import asynccontextmanager
from routers import inventory, auth
from routers import inventory, transactions
from db.init_db import init_db



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



origins_env = os.getenv("CORS_ORIGINS", "")
origins = origins_env.split(",") if origins_env else ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,        
    allow_credentials=True,         
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db()
    yield
app = FastAPI(lifespan=lifespan)


app.mount('/static', StaticFiles(directory='static'), name='static')
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(transactions.router)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):

    start_time = time.time() # Catat jam kedatangan
    logger.info(f" {request.method} {request.url.path} - START")

    response = await call_next(request)

    process_time = time.time() - start_time # Hitung durasi
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# CONTROLER (Endpoint)
@app.get("/")
async def read_root():
    await asyncio.sleep(0.5)
    return {"message": "Inventory API - Modular Version"} # pesan ini harus sama dengan test_read_root di test_main.py
