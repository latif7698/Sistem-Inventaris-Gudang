from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# password hrus sesuai dengan yang di PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:My13!n1ghua@localhost/inventory-api"

# mesin koneksi
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#sesi kerja
SessionLocal = sessionmaker(autocommit=False, autoflush = False, bind=engine)

Base = declarative_base()