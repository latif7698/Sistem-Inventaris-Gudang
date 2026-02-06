from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

import models 
import database 
import security
from schemas import InventorySchema
from database import get_db

# # Perhatikan titik dua (..) artinya "keluar satu folder ke atas"
# from .. import models, database, security
# from .. main import InventorySchema, get_db # Kita  import schema & dependency dari main (sementara)

# Ganti 'app' menjadi 'router'

router = APIRouter(
    prefix= "/inventory", # Semua URL otomatis diawali /inventory
    tags=["Inventory"] # Biar rapi di Swagger UI
)

# ====== CRUD PINDAHAN =======

#=============================
#         READ (GET)
#=============================
@router.get("/", response_model=List[InventorySchema])
def get_inventory(db: Session = Depends(get_db),
                  # ditambah current_user: models.UserDB = Depends(get_current_user)
                  curent_user : models.UserDB = Depends(security.get_current_user), # <-- INI GEMBOKNYA
                  # --- QUERY PARAMETERS (Input Tambahan di URL) ---
                  search: Optional[str] = None, # boleh kosong. Kalau di isi jadi filter nama.
                  skip: int = 0, # Lewati berapa data awal? (Offset)
                  limit: int = 10 # Ambil berapa data? (Default 10 biar ringan)
                  ):
    
    # 1. Mulai Query dasar (Belum dieksekusi)
    query = db.query(models.InventoryDB)

    # 2. Logika Search: Kalau user kirim kata kunci
    if search:
        # Filter nama yang MENGANDUNG kata kunci (Case Insensitive ilike/contains)
        # Note: Di SQLite/Postgres biasa .contains itu Case Sensitive. 
        # Kalau mau canggih pakai .ilike(f"%{search}%") tapi .contains cukup buat latihan.
        query = query.filter(models.InventoryDB.name.contains(search))
    
    # 3. Logika Pagination: Potong Datanya
    # .offset(skip) -> Langkahi X data pertama
    # .limit(limit) -> Ambil Y data saja
    items = query.offset(skip).limit(limit).all()
    return items


#=============================
#        CREATE (POST)
#=============================

@router.post("/", status_code=201)
def create_inventory(inventory : InventorySchema, 
                     db : Session = Depends(get_db),
                     # Tambahkan: current_user: models.UserDB = Depends(get_current_user)
                     current_user : models.UserDB = Depends(security.get_current_user) # <-- INI GEMBOKNYA 
                     ):
    # Pastikan nama modelnya benar (InventoryDB atau InventoryBD? Cek models.py)
    # Disini saya asumsikan InventoryDB yang benar.
    #Cek ID Baranf (Validasi Manualmu)
    cek_duplikasi = db.query(models.InventoryDB).filter(models.InventoryDB.id == inventory.id).first()
    if cek_duplikasi:
        raise HTTPException(status_code=400, detail="ID already registered")
    

    # SIMPAN KE DATABASE (DENGAN STEMPEL PEMILIK)
    new_inventory = models.InventoryDB(
        id = inventory.id,
        name = inventory.name,
        price = inventory.price,
        stock = inventory.stock,
        description = inventory.description,
        owner_id = current_user.id #  <-- INI KUNCI DAY 11! Ambil ID dari user yang sedang login
    )
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    return new_inventory


#=============================
#           UPDATE
#=============================

@router.put("/{id}", response_model=InventorySchema)
def update_inventory(id:int, 
                      inventory_update: InventorySchema,
                      db: Session= Depends(get_db),
                      current_user: models.UserDB = Depends(security.get_current_user)
                      ):
    # Perbaikan: Variabel jadi db_item, dan pakai .first()
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not Found")
    

    # ======== LOGIKA DAY 12: CEK KEPEMILIKAN ========
    # jika ID memiliki barang BEDA dengan ID user yang login
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail= "Not authorized to delete this item")

    # --------------------------------------------


    db_item.name = inventory_update.name
    db_item.price = inventory_update.price
    db_item.stock = inventory_update.stock
    db_item.description = inventory_update.description

    db.commit()
    db.refresh(db_item)

    return db_item


#=============================
#           DELETE
#=============================


@router.delete("/{id}")
def delete_item(id: int, 
                db: Session=Depends(get_db),
                current_user: models.UserDB = Depends(security.get_current_user)
                ):
        # 1. Cari barangnya dulu
        db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

        # 2. Kalau barang gak ada
        if db_item is None:
            raise HTTPException(status_code=404, detail="Item Not Found")
        

        # ======== LOGIKA DAY 12: CEK KEPEMILIKAN ========
        # jika ID memiliki barang BEDA dengan ID user yang login
        if db_item.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail= "Not authorized to delete this item")

        # --------------------------------------------

        db.delete(db_item)
        db.commit() 

        return {"message": f"Item with id {id} successfully deleted"}







