from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status, Request 
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas import InventorySchema
from database import get_db
from fastapi.encoders import jsonable_encoder
from worker import send_notification_email
from worker import record_stock_log 
from models import LogType
from schemas import InventorySchema, StockLogResponse
from sqlalchemy import desc, asc, func, BigInteger, cast
from fastapi.responses import StreamingResponse
import schemas
import shutil
import os 
import models 
import database 
import security
import redis
import json
import csv
import io
import uuid


"""folder untuk menyimpan gambar"""
os.makedirs("static/images", exist_ok=True)

"""Penggunaan Redis dalam Caching"""
REDIS_URL =  os.getenv("REDIS_URL", "redis://localhost6379")
# REDIS_URL = os.environ["REDIS_URL"]

"""mengguanakan decode_responses dengan nilai true menghasilkan string bukan bytes"""
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses = True)

"""Rate Limiter untuk mencegah spam"""
def check_rate_limit(request: Request):
    """Membatasi user maksimal 5 request per 60 detik berdasarkan IP Addres"""
    # 1. Ambil IP Address pengunjung
    client_ip = request.client.host

    # 2. Buat "Buku catatan" khusus untuk IP ini di Redis
    key = f"rate limit:{client_ip}"

    # 3. Cek apakah dia sudah punya catatan kunjungan
    request_count = redis_client.get(key)

    # 4. SANG HAKIM: kalai catatanya sudah 5 kali atau lebih, TENDANG!
    if request_count and int(request_count) >= 5:
        print(f"🚨BLOKIR: IP {client_ip} terdeteksi melakukan spam/DDoS!")
        raise HTTPException(
            status_code= 429, # 429 = Too Many Request
            detail="Terlalu banyak request! Server kelelahan. Silahkan coba lagi dalam 1 menit."
        )
    
    # 5. Kalau belum diblokir, catat kedatangannya
    if not request_count:
        #Jika ini kedatangan pertama, catat angka 1 dan set alarm hancur dalam 1 menit
        redis_client.setex(key, 60, 1)
    else:
        # Jika kedatangan ke 2,3,4 tambah saja angkanya (+1)
        redis_client.incr(key)


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


# =======================================
# EXPORT TO CSV (LAPORAN MANAJEER)
# =======================================
@router.get("/export/csv")
def export_inventory_csv(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user) # wajib login
):
    """Download seluruh data inventaris saat ini dalam format CSV (Excel)"""
    #1. Ambil semua data barang dari Postgresql
    items = db.query(models.InventoryDB).all()
    # 2. siapkan ruang kosong di memori RAM (bukan harddisk server)
    stream = io.StringIO()
    # 3. siapkan pencatatan dengan format CSV
    writer = csv.writer(stream) 
    # 4. Tulis baris judul (header excel)
    writer.writerow(["ID Barang", "Nama Barang", "Harga", "Sisa Stock", "Deskripsi", "Link Gambar"])
    # tulis isi datanya baris demi baris menggunakan looping
    for item in items:
        writer.writerow([
            item.id,
            item.name,
            item.price,
            item.stock,
            item.description,
            item.image_url if item.image_url else "Tidak Ada Gambar"
        ])
    # Kembalikan kursor ke baris pertama sebelum file dikirim
    stream.seek(0)
    # bungkus menjadi file dan kirim ke browser pengguna
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    # Perintah 'attachment' ini yang memaksa browser untuk mendownload file, bukan menampilkannya
    response.headers["Content-Disposition"] = "attachment; filename=Laporan_Stock_Gudang.csv"
    return response

# ========================================
# DASHBOARD STATISTICS (AGRERASI)
# ========================================
@router.get("/dashboard/stats")
def get_dashboard_statiscis(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):

    """Mengambil rangkuman statisics untuk layar utama (Dashboard)"""
    # 1. Hitung total JENIS barang (Berapa baris di tabel?)
    total_items = db.query(func.count(models.InventoryDB.id)).scalar() or 0
    # 2. Hitung total FISIK stok (Tambahkan semua angka di kolom 'stock')
    total_physical_count = db.query(func.count(models.InventoryDB.stock)).scalar() or 0
    # 3. Hitung jumlah barang yang statusnya KRITIS (Stok di bawah 10)
    critical_stock_count = db.query(func.count(models.InventoryDB.id)).filter(models.InventoryDB.stock < 10).scalar() or 0
    # 4. (Bonus Industri) Hitung Total Nilai Aset (Harga x Stok)
    # Ini sangat disukai manajer keuangan!
    total_asset_value = db.query(func.sum(cast(models.InventoryDB.price, BigInteger) * models.InventoryDB.stock)).scalar() or 0

    return {
        "status": "succes",
        "data":{
            "total_jenis_barang": total_items,
            "total_stock_fisik": total_physical_count,
            "barang_stock_kritis": critical_stock_count,
            "estimasi_nilai_aset_rp": total_asset_value
        }
    }

#=======================================
# ENDPOINT: PENCARIAN POPULER (TRENDING)
#=======================================
@router.get("/trending")
def get_trending_searches():
    """Mengambil 5 kata kunci yang paling sering dicari oleh user"""

    # zrevrange = Z-Set Reverse Range (Ambil dari skor tertinggi ke terendah)
    # 0, 4 = Ambil index ke-0 sampai ke-4 (Total 5 data teratas)
    # withscores=True = Tampilkan juga jumlah pencariannya
    trending_data = redis_client.zrevrange("trending_search", 0, 4, withscores=True)
    

    #Rapihkan datanya agar format JSON-nya cantik saat dikirim ke frontend
    result = []
    for item in trending_data:
        keyword, score = item
        result.append({
            "keyword": keyword,
            "search_count":int(score)
        })
    return {"trending_data":result}



                            # ====== CRUD  =======

#=============================
#         READ (GET)
#=============================
@router.get("/", response_model=List[InventorySchema])
def get_inventory(request: Request,
                  db: Session = Depends(get_db),
                  # ditambah current_user: models.UserDB = Depends(get_current_user)
                  current_user : models.UserDB = Depends(security.get_current_user), # <-- INI GEMBOKNYA
                  #   pasang satpam redisnya disini 
                  rate_limit : None = Depends(check_rate_limit), #satpamnya disini
                  # --- QUERY PARAMETERS (Input Tambahan di URL) ---
                  search: Optional[str] = "", # boleh kosong. Kalau di isi jadi filter nama.
                  skip: int = 0, # Lewati berapa data awal? (Offset)
                  limit: int = 10, # Ambil berapa data? (Default 10 biar ringan)

                  #   query parameters untuk filter 
                  min_price: Optional[int] = None, 
                  max_price: Optional[int] = None,
                  min_stock: int = 0,
                  sorted_by: Optional[str] = "id",
                  sorted_order: Optional[str] = "asc"
                  ):
    
    search_term = search.strip().lower() if search else " " #rapihkan huruf kecil semua
    if search:
        redis_client.zincrby("trending_search", 1, search_term)
    
    #1. BUAT KUNCI LACI REDIS
    # Kuncinya harus spesifik! Kalau user nyari "Asus" di halaman 2, 
    # jangan sampai tertukar dengan pencarian "Asus" di halaman 1.
    cache_key = f'inventory_search:{search_term}_skip:{skip}_limit:{limit}_minP:{min_price}_maxP:{max_price}_minS:{min_stock}'
    # 2.CEK MEJA RESEPSIONIS (CACHE HIT)
    cached_data = redis_client.get(cache_key)

    if cached_data:
        print("CACHE HIT: Mengambil data kilat dari RAM (Redis)!")
        return json.loads(cached_data)
    print(" CACHE MISS: Mengambil data dari PostgreSQL...")


    # 1. Mulai Query dasar (Belum dieksekusi)
    # Selalu filter barang yang is_deleted == False (yang belum dihapus)
    query = db.query(models.InventoryDB).filter(models.InventoryDB.is_deleted == False)

    # 2. Logika Search: Kalau user kirim kata kunci
    if search:
        # Filter nama yang MENGANDUNG kata kunci (Case Insensitive ilike/contains)
        # Note: Di SQLite/Postgres biasa .contains itu Case Sensitive. 
        query = query.filter(models.InventoryDB.name.ilike(f"%{search}%"))
    
    if min_price is not None:
        query = query.filter(models.InventoryDB.price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.InventoryDB.price <= max_price)

    if min_stock is not None:
        query = query.filter(models.InventoryDB.price >= min_stock)
    
    if sorted_by == "price":
        query = query.order_by(desc(models.InventoryDB.price) if sorted_order == "desc" else asc(models.InventoryDB.price))
    elif sorted_by == "name":
        query = query.order_by(desc(models.InventoryDB.name) if sorted_order == "desc" else asc(models.InventoryDB.name))
    elif sorted_by == "stock":
        query = query.order_by(desc(models.InventoryDB.stock) if sorted_order == "desc" else asc(models.InventoryDB.stock))
    else:
        """default mengurutkan berdasarkan ID"""
        query = query.order_by(desc(models.InventoryDB.id) if sorted_order == "desc" else asc(models.InventoryDB.id))
    
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

    #Lempar tugas berat ke CELERY (Kode Baru day 37)
    #PERHATIKAN KATA KUNCI ".delay()" Ini sangat krusial!
    print("FastAPI: Melempar tugas kirim email ke Celery..")
    send_notification_email.delay(new_inventory.name)
    print("FastAPI: Tugas dilempar! Melanjutkan pelayanan user tanpa menunggu email selesai...")
    return new_inventory


#=============================
# UPDATE (PUT{id}) untuk barang aktif 
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
    # panggil petugas kebersihan
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
        if db_item is None or db_item.is_deleted == True:  #jadi yang is del == True untuu soft del
            raise HTTPException(status_code=404, detail="Item Not Found or Already deleted")
        

        # ======== LOGIKA DAY 12: CEK KEPEMILIKAN ========
        # jika ID memiliki barang BEDA dengan ID user yang login
        if db_item.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail= "Not authorized to delete this item")

        # --------------------------------------------

        db_item.is_deleted = True
        db.commit() 
        # panggil petugas kebersihan
        clear_inventory_cache()
        return {"message": f"Item with id {id} successfully moved to trash (Soft Deleted)"}


# ===========================
# RESTORE (MENGEMBALIKAN BARANG)
# ===========================
@router.put("/{id}/restore")
def restore_item(
    id: int,
    db : Session = Depends(get_db),
    current_user : models.UserDB = Depends(security.get_current_user)
):
    # 1. Cari barangnya di database (apapun statusnya)
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
    
    # Jika secara fisik memang tidak ada di database
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan di database.")
    
    # 2. Cek apakah barangnya memang sedang terhapus
    if db_item.is_deleted == False:
        return {"message": f"Barang dengan id {id} tidak ada di tong sampah (Status masih aktif)."}
    
    # 3. Cek Kepemilikan (Tetap harus aman!)
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Kamu tidak berhak mengembalikan barang ini.")
    
    # 4. MANTRA RESTORE: Ubah is_deleted kembali menjadi False!
    db_item.is_deleted = False
    db.commit()

    # 5. Bersihkan cache Redis karena barang kembali muncul
    clear_inventory_cache()

    return {"message": f"Item with id {id} succesfully restored from trash!"}



    
    
#===========================
#   UPLOAD GAMBAR BARANG
#===========================
@router.post("/{id}/image")
async def upload_item_image(
    id: int,
    file: UploadFile = File(...), # <-- Ini akan membuat tombol "Choose File" di Swagger UI
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
): 
    """Mengunggah file gambar (JPG/PNG) untuk barang tertentu."""
    # 1. Cari dulu barangnya, ada atau tidak dan pastikan tidak masuk ke sampah
    db_item = (db.query(models.InventoryDB)
               .filter(models.InventoryDB.id == id, models.InventoryDB.is_deleted == False)
               .first())
    
    if not db_item:
        raise HTTPException(status_code= 404, detail="Item not found")
    
    # cek kempemilikan barang (hanya pemilik yang bisa ganti gambar)
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak berhak mengubah gambar barang ini")
    
    # 2. Keamanan: Cek apakah yang diupload benar-benar gambar / validasi tipe file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail='File must be an image!')
    
    # 3. Tentukan nama dan lokasi file 
    # Buat Nama File Unik (Agar kalau namanya sama, tidak saling menimpa)
    # Format: static/images/item_1_laptop.jpg
    file_extention = file.filename.split(".")[-1]
    unique_filename = f"item_{id}_{uuid.uuid4().hex[:8]}.{file_extention}"
    file_location = f'static/images{unique_filename}'

    # 4. Simpan File Asli ke Dalam Harddisk Server (Folder static/images)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update kolom image_url di Database PostgreSQL
    db_item.image_url = f"/{file_location}"
    db.commit()
    clear_inventory_cache()

    return{
        "message": "Gambar berhasil diunggah",
        "filename": unique_filename,
        "image_url": db_item.image_url
    }

# ==============================
# PUT UNTUK UPDATE STOCK / {item_id}
# ==============================

@router.put("/{item_id}/stock")
def update_stock(item_id: int, 
                 change_amount: int,
                 db: Session = Depends(get_db),
                 current_user : models.UserDB = Depends(security.get_current_user)): # This JWT
    # 1. Cari barangnya
    item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    
    # 2. validasi logika untuk tidak sampai minus pada barang
    if item.stock + change_amount < 0:
        raise HTTPException(status_code=400, detail="Transaksi gagal: Stock tidak mencukupi (Minus)!")
    
    # update stock barang
    item.stock += change_amount
    db.commit()
    
    # 3. Tentukan log type ("IN" jika nambah, "OUT" jika ngurang)
    log_type = LogType.IN.value if change_amount > 0 else LogType.OUT.value
    
    # 4. SURUH CELERY MENCATAT DI BELAKANG LAYAR (Mulai Magic-nya di sini )
    record_stock_log.delay(item_id=item.id, 
                           change_amount=change_amount, 
                           log_type=log_type, 
                           user_id=current_user.id)
    # mebersihkan data karena perubahan oleh redis 
    clear_inventory_cache()
    
    return {"message": "Stok berhasil diupdate!", "current_stock": item.stock}



# ===========================
# GET{item_id} untuk riwayat keluar masuk barang 
# ===========================
@router.get("/{item_id}/logs", response_model=List[schemas.StockLogResponse])
def get_item_stock_logs(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    """Melihat riwayat keluar-masuk stok untuk satu barang spesifik."""
    
    #  Pastikan barangnya ada
    item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    
    #  Ambil semua log untuk barang ini, urutkan dari yang PALING BARU (descending)
    logs = db.query(models.StockLog)\
             .filter(models.StockLog.item_id == item_id)\
             .order_by(models.StockLog.created_at.desc())\
             .all()
             
    return logs
