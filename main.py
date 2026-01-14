from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine

# setup DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()