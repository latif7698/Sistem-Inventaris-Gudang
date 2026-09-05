from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime

class InventoryBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    price: int = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    image_url: Optional[str] = None

class InventoryCreate(InventoryBase):
    id: Optional[int] = None

class InventorySchema(InventoryBase):
    id: int = Field(..., ge=1)
    owner_id: Optional[int] = None
    is_deleted: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True)

# ---- USER -----
class UserSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3, max_length=100)
    model_config = ConfigDict(from_attributes=True)

# ---- LOGIN ----
class LoginSchema(BaseModel):
    username: str
    password: str
    model_config = ConfigDict(from_attributes=True)

# ---- Untuk Mengirim Data Riwayat ----
class StockLogResponse(BaseModel):
    id: int
    item_id: int
    change_amount: int
    log_type: str
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class StockUpdateRequest(BaseModel):
    new_stock: int
    notes: Optional[str] = None

class StockAdjustRequest(BaseModel):
    amount: int
    type: str = "IN"
    notes: Optional[str] = None

"""Schemas untuk Transaksi"""
class TransactionBase(BaseModel):
    item_id: int
    transaction_type: str
    quantity: int
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass 

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
