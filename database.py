from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
#from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
# Cek apakah ada link langsung (dari Neon)?
DATABASE_URL = os.getenv("DATABASE_URL")

# --- SETTINGAN DINAMIS ---
if DATABASE_URL: 
    # kalau ada (misal di cloud), pakai ini
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    # kalau gak ada pakai cara lama (localhost/docker compose)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")       
    DB_PASS = os.getenv("DB_PASS", "mydonutgua123")  # <--- Password default kamu
    DB_NAME = os.getenv("DB_NAME", "inventory_db")
    # Gabungkan jadi URL
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# password hrus sesuai dengan yang di PostgreSQL

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