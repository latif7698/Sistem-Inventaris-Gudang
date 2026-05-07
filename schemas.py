from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

#--- View (Schema) ---
# Tetap disini agar file routers bisa import "from ..main import UserSchema"
class InventorySchema(BaseModel):
    # ID biasanya otomatis (autoincrement), tapi kalau kamu mau input manual, oke.
    id : int = Field(..., ge=1) 
    name : str = Field(..., min_length=3, max_length=100)
    price : int = Field(..., ge=0)
    stock : int = Field(..., ge=0)
    description : Optional[str] = Field(None, max_length=1000)
    image_url : Optional[str] = None
    model_config = ConfigDict(from_attributes=True) # PENTING: Biar bisa baca data dari ORM Database


# ---- USER -----
class UserSchema(BaseModel):
    username: str
    password: str 

    model_config = ConfigDict(from_attributes=True)

# ---- LOGIN ----
class LoginSchema(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(from_attributes=True)

# ---- Untuk Mengirim Data Riwayat ----
class StockLogResponse(BaseModel):
    id: int
    item_id : int
    change_amount: int
    log_type : str
    user_id : Optional[int]=None

    model_config = ConfigDict(from_attributes=True)




