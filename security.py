from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError 
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db 
import models
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_rahasia_lokal")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto") 

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verif_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_acces_token(data: dict, expires_delta: Optional[timedelta]=None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


from fastapi import HTTPException, status
from jose import JWTError, jwt #pastikan import JWTError


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            return None
        
        return username
    except JWTError:
        return None
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_token(token)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= "Cloud not Validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.UserDB).filter(models.UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user 