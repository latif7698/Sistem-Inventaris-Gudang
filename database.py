from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os


import os

# --- SETTINGAN DINAMIS ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")       # <--- Perbaikan: Nama variabel benar
DB_PASS = os.getenv("DB_PASS", "mydonutgua123")  # <--- Password default kamu
DB_NAME = os.getenv("DB_NAME", "inventory_db")

# Gabungkan jadi URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# password hrus sesuai dengan yang di PostgreSQL
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin123@host.docker.internal/inventory-api"
# Ganti ujungnya jadi inventory_db
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:mydonutgua123@host.docker.internal/inventory_db"

# mesin koneksi
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#sesi kerja
SessionLocal = sessionmaker(autocommit=False, autoflush = False, bind=engine)

Base = declarative_base()

# --DEPENDENCY--
# Tetap disini agar file routers bisa import "from ..main import get_db"
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()