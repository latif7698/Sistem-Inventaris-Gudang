from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status, Request #<-- Tambahkan File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas import InventorySchema
from database import get_db
from fastapi.encoders import jsonable_encoder
import shutil #<-- Untuj save file
import os #<-- tambahakan ini untuk bikin folder
import models 
import database 
import security
import redis
import json


# -----------------------------------------
# sambungkan ke meje resepsionis (Redis)
# -------------------------------------------
REDIS_URL =  os.getenv("REDIS_URL", "redis://localhost6379")
#decode_responses = True agae balasan redias langsung berupa teks (string) bukan bytes kasar
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses = True)

# tambahkan fungsi untuk pembersihan
def clear_inventory_cache():
    """Menghapus semua cache pencarian inventory agar tidak ada data basi"""
    # Mencari semua laci yang namanya berawalan "inventory_search:"
    for key in redis_client.scan_iter("inventory_search:*"):
        redis_client.delete(key)
    print("Cached Cleared: Semua data basi telah dihapus dari RAM!")


# Ganti 'app' menjadi 'router'
router = APIRouter(
    prefix= "/inventory", # Semua URL otomatis diawali /inventory
    tags=["Inventory Management"] # Biar rapi di Swagger UI
)

#buat folder khusus untuk menyimpan gambar
os.makedirs("static/images", exist_ok=True)

# ====== CRUD PINDAHAN =======

#=============================
#         READ (GET)
#=============================
@router.get("/", response_model=List[InventorySchema])
def get_inventory(db: Session = Depends(get_db),
                  # ditambah current_user: models.UserDB = Depends(get_current_user)
                  curent_user : models.UserDB = Depends(security.get_current_user), # <-- INI GEMBOKNYA
                  # --- QUERY PARAMETERS (Input Tambahan di URL) ---
                  search: Optional[str] = "", # boleh kosong. Kalau di isi jadi filter nama.
                  skip: int = 0, # Lewati berapa data awal? (Offset)
                  limit: int = 10 # Ambil berapa data? (Default 10 biar ringan)
                  ):
    
    #1. BUAT KUNCI LACI REDIS
    # Kuncinya harus spesifik! Kalau user nyari "Asus" di halaman 2, 
    # jangan sampai tertukar dengan pencarian "Asus" di halaman 1.
    cache_key = f'inventory_search:{search}_skip:{skip}_limit:{limit}'
    # 2.CEK MEJA RESEPSIONIS (CACHE HIT)
    cached_data = redis_client.get(cache_key)

    if cached_data:
        print("CACHE HIT: Mengambil data kilat dari RAM (Redis)!")
        return json.loads(cached_data)
    print(" CACHE MISS: Mengambil data dari PostgreSQL...")


    # 1. Mulai Query dasar (Belum dieksekusi)
    query = db.query(models.InventoryDB)

    # 2. Logika Search: Kalau user kirim kata kunci
    if search:
        # Filter nama yang MENGANDUNG kata kunci (Case Insensitive ilike/contains)
        # Note: Di SQLite/Postgres biasa .contains itu Case Sensitive. 
        # Kalau mau canggih pakai .ilike(f"%{search}%") tapi .contains cukup buat latihan.
        query = query.filter(models.InventoryDB.name.ilike(f"%{search}%"))
    
    # 3. Logika Pagination: Potong Datanya
    # .offset(skip) -> Langkahi X data pertama
    # .limit(limit) -> Ambil Y data saja
    items = query.offset(skip).limit(limit).all()

    # 4. FOTOKOPI & TITIPKAN KE REDIS
    # Redis tidak mengerti bentuk "Objek SQLAlchemy", dia cuma ngerti Teks (String).
    # Jadi kita ubah dulu jadi format kamus biasa pakai alat bawaan FastAPI.
    items_dict = jsonable_encoder(items)

    # Simpan ke Redis selama 60 detik (setex = Set with Expiration)
    # json.dumps() mengubah kamus Python jadi Teks Murni.
    redis_client.setex(cache_key, 60, json.dumps(items_dict))
    # 5. Kembalikan ke user 
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
    print(f'Mencoba menyimpan user: {new_inventory.name}')
    db.add(new_inventory)
    db.commit()
    print('Data berhasil di-commit ke database!')
    db.refresh(new_inventory)
    # panggil petugas kebersihan
    clear_inventory_cache()
    return new_inventory


#=============================
#         UPDATE (PUT)
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
    clear_inventory_cache()
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
        clear_inventory_cache()
        return {"message": f"Item with id {id} successfully deleted"}


#===========================
#       UPLOAD IMAGE
#===========================
@router.post("/{id}/image")
def upload_item_image(
    id: int,
    file: UploadFile = File(...), # <-- Ini akan membuat tombol "Choose File" di Swagger UI
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
): 
    # 1. Cari dulu barangnya, ada atau tidak?
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
    if not db_item:
        raise HTTPException(status_code= 404, detail="Item not found")
    # 2. Keamanan: Cek apakah yang diupload benar-benar gambar?
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail='File must be an image!')
    # 3. Tentukan nama dan lokasi file 
    # Format: static/images/item_1_laptop.jpg
    file_location = f'static/images/item_{id}_{file.filename}'

    # 4. Simpan file-nya ke dalam folder laptopmu
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ========================================
    # 5. TAMBAHAN DAY 28: SIMPAN URL KE DATABASE
    # ========================================
    # kita buat URL publiknya (tanpa titik awal, langsung /static/...)
    public_url = f'/static/images/item{id}_{file.filename}'

    #update kolom image_url di database
    db_item.image_url = public_url
    db.commit()
    db.refresh(db_item)

    return {
        'message': 'Gambar berhasil diupload dan disambungkan ke database!',
        'item_id': id,
        'file_path': public_url
    }



