from fastapi import FastAPI, HTTPException, Depends,status #tambahakan 'status' di import fastapi
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from security import get_password_hash, verif_password, create_acces_token, verify_token # import verify_token yang baru dibuat
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # tambahkan OAuth2PasswordBearer
from datetime import timedelta
import models

# setup DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ini memberi tahu swagger: "Eh, kalau mau login, kirim data ke url/login ya"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --DEPENDENCY--
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    

#--- View (Schema) ---
class InventorySchema(BaseModel):
    # ID biasanya otomatis (autoincrement), tapi kalau kamu mau input manual, oke.
    id : int = Field(..., ge=1) 
    name : str = Field(..., min_length=3, max_length=100)
    price : int = Field(..., ge=0)
    stock : int = Field(..., ge=0)
    description : Optional[str] = Field(None, max_length=1000)

    class Config:
        from_attributes = True # PENTING: Biar bisa baca data dari ORM Database

class UserSchema(BaseModel):
    username: str
    password: str 

class LoginSchema(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True

# CONTROLER (Endpoint)

@app.get("/")
def read_root():
    return {"message": "Inventory Telah Diaktivasi"}


# ======== CREATE (POST) ==========

@app.post("/inventory", status_code=201)
def create_inventory(inventory : InventorySchema, 
                     db : Session = Depends(get_db),
                     # Tambahkan: current_user: models.UserDB = Depends(get_current_user)
                     current_user : models.UserDB = Depends(get_current_user) # <-- INI GEMBOKNYA 
                     ):
    # Pastikan nama modelnya benar (InventoryDB atau InventoryBD? Cek models.py)
    # Disini saya asumsikan InventoryDB yang benar.
    cek_duplikasi = db.query(models.InventoryDB).filter(models.InventoryDB.id == inventory.id).first()
    if cek_duplikasi:
        raise HTTPException(status_code=400, detail="ID already registered")
    
    new_inventory = models.InventoryDB(
        id = inventory.id,
        name = inventory.name,
        price = inventory.price,
        stock = inventory.stock,
        description = inventory.description
    )
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    return new_inventory

# -- END POINT BARU: REGISTER (DAY 8) --
@app.post("/register", status_code=201)
def register_user(user: UserSchema, db: Session = Depends(get_db)):
    # 1. Cek User (Perbaikan: .first() bukan .frist())
    cek_user = db.query(models.UserDB).filter(models.UserDB.username==user.username).first()
    if cek_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. HASH PASSWORD
    hashed_pwd = get_password_hash(user.password)

    # 3. Masukan ke Database
    new_user = models.UserDB(
        username = user.username,
        hashed_password = hashed_pwd 
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created succesfully", "username": new_user.username}


# ---- ENDPOINT BARU: LOGIN (DAY 9) ----
# ---- UPDATE ENDPOINT LOGIN ----

@app.post("/login")
def login(form_data : OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)
          ):
    #1. Cek, apakah username ada di database?
    user = db.query(models.UserDB).filter(models.UserDB.username == form_data.username).first()

    #user gak ketemu atau user salah
    if not user or not verif_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    #2. Kalau lolos, bikin token
    acces_token_expires = timedelta(minutes=30)
    acces_token = create_acces_token(
        data = {"sub": user.username}, #'sub' adalah standar jwt untuk Subjek (siapa pemilik token)
        expires_delta=acces_token_expires
    )

    #3. Kasih token ke user
    return {"access_token": acces_token, "token_type": "bearer"}



# ============ READ (GET) ============


@app.get("/inventory", response_model=List[InventorySchema])
def get_inventory(db: Session = Depends(get_db),
                  # ditambah current_user: models.UserDB = Depends(get_current_user)
                  curent_user : models.UserDB = Depends(get_current_user), # <-- INI GEMBOKNYA
                  ):
    return db.query(models.InventoryDB).all()



# ============= UPDATE =================



# Perbaikan: Tambah "/" sebelum {id}
@app.put("/inventory/{id}", response_model=InventorySchema)
def update_inventory(id:int, 
                      inventory_update: InventorySchema,
                      db: Session= Depends(get_db),
                      current_user: models.UserDB = Depends(get_current_user)
                      ):
    # Perbaikan: Variabel jadi db_item, dan pakai .first()
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not Found")
    
    db_item.name = inventory_update.name
    db_item.price = inventory_update.price
    db_item.stock = inventory_update.stock
    db_item.description = inventory_update.description

    db.commit()
    db.refresh(db_item)

    return db_item



# =============== DELETE ==================


# Perbaikan: Tambah "/" sebelum {id}
@app.delete("/inventory/{id}")
def delete_item(id: int, 
                db: Session=Depends(get_db),
                current_user: models.UserDB = Depends(get_current_user)
                ):
        db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

        if db_item is None:
            raise HTTPException(status_code=404, detail="Item Not Found")
        
        db.delete(db_item)
        db.commit() 

        return {"message": f"Item with id {id} successfully deleted"}


