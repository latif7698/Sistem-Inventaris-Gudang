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

app = FastAPI()

# ---- DAFTARKAN ROUTER (MENGHUBUNGKAN KABEL) ----
app.include_router(auth.router)
app.include_router(inventory.router)


# CONTROLER (Endpoint)
@app.get("/")
def read_root():
    return {"message": "Inventory API - Modular Version"}



