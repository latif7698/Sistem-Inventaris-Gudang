import os
from dotenv import load_dotenv
from database import SessionLocal
from sqlalchemy import text
from database import engine, Base
import models 

# 1. BACA .ENV DULU (WAJIB DI ATAS!)
load_dotenv()

# Cek apakah link awan (Neon) sudah terbaca?
url = os.getenv("DATABASE_URL")
print(f"Mencoba connect ke: {url}")

# 2. BARU IMPORT DATABASE SETELAH .ENV TERBACA
print("Memulai proses pembuatan tabel di awan...")

# 3. PALU GODAM BEKERJA
Base.metadata.create_all(bind=engine)
print("EKSEKUSI SELESAI! Cek Dashboard Neon sekarang.")


def fix_sequence():
    print("🔧 Memperbaiki mesin penghitung ID (Sequence) PostgreSQL...")
    db = SessionLocal()
    try:
        # Perintah SQL asli untuk menyinkronkan ulang ID
        query = text("SELECT setval('inventory_id_seq', (SELECT MAX(id) FROM inventory));")
        db.execute(query)
        db.commit()
        print("✅ PENYEMBUHAN SUKSES! Mesin penghitung sudah normal kembali!")
    except Exception as e:
        print(f"❌ Gagal: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_sequence()