from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

# --- PERBAIKAN IMPORT (JANGAN PAKAI TITIK DUA '..') ---
import models
import security
import database
from schemas import UserSchema  # Ambil dari schemas.py (bukan main)
from database import get_db     # Ambil dari database.py (bukan main)


router = APIRouter(tags=["Authentication & Users"]) # Gak pake prefix biar URL tetap /login dan /register

#=============================
#          REGISTER
#=============================
@router.post("/register", status_code=201)
def register_user(user: UserSchema, db: Session = Depends(get_db)):
    # 1. Cek User (Perbaikan: .first() bukan .frist())
    cek_user = db.query(models.UserDB).filter(models.UserDB.username==user.username).first()
    if cek_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. HASH PASSWORD
    hashed_pwd = security.get_password_hash(user.password)

    # 3. Masukan ke Database
    new_user = models.UserDB(
        username = user.username,
        hashed_password = hashed_pwd 
    )
    print(f"Mencoba menyimpan user: {new_user.username}")
    db.add(new_user)
    db.commit()
    print("Data berhasil di-commit ke database!")
    db.refresh(new_user)

    return {"message": "User created succesfully", "username": new_user.username}

#=============================
#           LOGIN
#=============================

@router.post("/login")
def login(form_data : OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)
          ):
    #1. Cek, apakah username ada di database?
    user = db.query(models.UserDB).filter(models.UserDB.username == form_data.username).first()

    #user gak ketemu atau user salah
    if not user or not security.verif_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    #2. Kalau lolos, bikin token
    acces_token_expires = timedelta(minutes=30)
    acces_token = security.create_acces_token(
        data = {"sub": user.username}, #'sub' adalah standar jwt untuk Subjek (siapa pemilik token)
        expires_delta=acces_token_expires
    )

    #3. Kasih token ke user
    return {"access_token": acces_token, "token_type": "bearer"}



