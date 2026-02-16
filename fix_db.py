import os
from dotenv import load_dotenv

# 1. BACA .ENV DULU (WAJIB DI ATAS!)
load_dotenv()

# Cek apakah link awan (Neon) sudah terbaca?
url = os.getenv("DATABASE_URL")
print(f"Mencoba connect ke: {url}")

# 2. BARU IMPORT DATABASE SETELAH .ENV TERBACA
from database import engine, Base
import models 

print("Memulai proses pembuatan tabel di awan...")

# 3. PALU GODAM BEKERJA
Base.metadata.create_all(bind=engine)

print("EKSEKUSI SELESAI! Cek Dashboard Neon sekarang.")