from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError #pastikan import JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db # Ambil dari database.py
import models


SECRET_KEY = "rahasia_super_negara_api_backend_bootcamp"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

#1. Konfigurasi Mesin Hitung (setup hashing)
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    # masukan info kadaluarsa ke dalam token
    to_encode.update({"exp": expire})

    #KUNCI JAWABAN: Enkripsi data pakai SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


from fastapi import HTTPException, status
from jose import JWTError, jwt #pastikan import JWTError

# ====== DAY 10 =======
# --- FUNGSI BARU: CEK TOKEN (DECODE) ---

def verify_token(token: str):
    try:
        #coba buka segel tokeenya
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        #ambil data username dari dalam token
        username: str = payload.get("sub")

        if username is None:
            #kalau tokennya kebuka tapi sisina kosong
            return None
        
        return username
    except JWTError:
        # kalai tokennya palsi, expired, atau rusak
        return None
    


# ini memberi tahu swagger: "Eh, kalau mau login, kirim data ke url/login ya"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    #1. Panggil security.py untuk cek token valid/tidak
    username = verify_token(token)

    #2. kalau token tidak valid
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= "Cloud not Validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    #3. Kalau valid, cek apakah usernya masih ada di database?
    user = db.query(models.UserDB).filter(models.UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user # Lolos! Silahkan masuk.