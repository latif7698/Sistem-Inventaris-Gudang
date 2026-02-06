from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# password hrus sesuai dengan yang di PostgreSQL
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin123@localhost/inventory-api"
# Ganti ujungnya jadi inventory_db
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:mydonutgua123@localhost/inventory_db"
# mesin koneksi
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#sesi kerja
SessionLocal = sessionmaker(autocommit=False, autoflush = False, bind=engine)

Base = declarative_base()