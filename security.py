from passlib.context import CryptContext


#1. Konfigurasi Mesin Hitung
# Kita pakai algoritma "bcrypt" ( Standar Industri yang aman & lambat buat di-hack)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

# 2. Fungsi: Mengacak password (hashing)
def get_password_hash(password: str):
    return pwd_context.hash(password)

# 3. Fungsi: Cek Password (Verify)
# membandingkan password inputan user dengan hash di database
def verif_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)