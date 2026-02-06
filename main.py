from fastapi import FastAPI, Depends
from database import SessionLocal, engine
import models

from routers import inventory, auth

# setup DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ---- DAFTARKAN ROUTER (MENGHUBUNGKAN KABEL) ----
app.include_router(auth.router)
app.include_router(inventory.router)


# CONTROLER (Endpoint)
@app.get("/")
def read_root():
    return {"message": "Inventory API - Modular Version"}

