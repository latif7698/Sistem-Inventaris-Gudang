from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
import security

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(security.get_current_user)]
)

@router.get("/", response_model=List[schemas.TransactionResponse])
def get_all_transactions(
    limit: int = 50, 
    skip: int = 0, 
    db: Session = Depends(get_db)
):
    """Melihat semua riwayat pergerakan barang (Global)."""
    transactions = db.query(models.TransactionDB)\
                     .order_by(models.TransactionDB.timestamp.desc())\
                     .offset(skip).limit(limit).all()
    return transactions

@router.get("/item/{item_id}", response_model=List[schemas.TransactionResponse])
def get_item_transactions(
    item_id: int, 
    db: Session = Depends(get_db)
):
    """Melihat riwayat transaksi spesifik untuk SATU barang saja."""
    # Pastikan barangnya ada dulu
    item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    transactions = db.query(models.TransactionDB)\
                     .filter(models.TransactionDB.item_id == item_id)\
                     .order_by(models.TransactionDB.timestamp.desc())\
                     .all()
    return transactions