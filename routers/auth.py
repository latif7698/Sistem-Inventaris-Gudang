from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import models
import security
import database
from schemas import UserSchema  
from database import get_db    


router = APIRouter(tags=["Authentication & Users"]) 

#=============================
#          REGISTER
#=============================
@router.post("/register", status_code=201)
def register_user(user: UserSchema, db: Session = Depends(get_db)):
    cek_user = db.query(models.UserDB).filter(models.UserDB.username==user.username).first()
    if cek_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pwd = security.get_password_hash(user.password)

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
    user = db.query(models.UserDB).filter(models.UserDB.username == form_data.username).first()

    if not user or not security.verif_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    acces_token_expires = timedelta(minutes=30)
    acces_token = security.create_acces_token(
        data = {"sub": user.username}, 
        expires_delta=acces_token_expires
    )

    return {"access_token": acces_token, "token_type": "bearer"}



