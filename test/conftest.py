import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from main import app
from database import get_db
from database import Base

# 1. SETUP DATABASE PALSU (SQLite di Memory)
# "check_same_thread": False dibutuhkan khusus sqlite
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. SETUP FIXTURE (Persiapan sebelum tes)
@pytest.fixture(scope="function")
def db():
    #buat tabel baru (kosong)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # hancurkan tabel setelah test selesai (bersih-bersih)
        Base.metadata.drop_all(bind=engine)

# 3. SETUP CLIENT (Robot Pengetes)
@pytest.fixture(scope="function")
def client(db):
    # FUNGSI AJAIB: Dependency Override
    # kita paksa aplikasi pakai DB palsu, bukan DB asli
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # Reset override setelah selesai
    app.dependency_overrides.clear()