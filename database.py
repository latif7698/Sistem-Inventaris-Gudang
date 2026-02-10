from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# password hrus sesuai dengan yang di PostgreSQL
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin123@host.docker.internal/inventory-api"
# Ganti ujungnya jadi inventory_db
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:mydonutgua123@host.docker.internal/inventory_db"

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