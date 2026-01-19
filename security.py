from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext


SECRET_KEY = "rahasia_super_negara_api_backend_bootcamp"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

#1. Konfigurasi Mesin Hitung
# Kita pakai algoritma "bcrypt" ( Standar Industri yang aman & lambat buat di-hack)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto") #Setup hashing

# 2. Fungsi: Mengacak password (hashing)
def get_password_hash(password: str):
    return pwd_context.hash(password)

# 3. Fungsi: Cek Password (Verify)
# membandingkan password inputan user dengan hash di database
def verif_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- Fungsi baru: Bikin Token (JWT) ---
def create_acces_token(data: dict, expires_delta: Optional[timedelta]=None):
    to_encode = data.copy()

    #Tentukan kapan token kadaluarsa
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # masukan info kadaluarsa ke dalam token
    to_encode.update({"exp": expire})

    #KUNCI JAWABAN: Enkripsi data pakai SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt