# Standart Library
from typing import List, Optional
import json
import csv
import io
import uuid
import logging
import os 
import shutil

# Third Party 
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status, Request 
from sqlalchemy import desc, asc, func, BigInteger, cast
from sqlalchemy.orm import Session
import redis

# Local Modules
from database import get_db
from worker import send_notification_email, record_stock_log 
from models import LogType
from schemas import InventorySchema, StockLogResponse, StockUpdateRequest, StockAdjustRequest
import schemas
import models 
import database 
import security


logger = logging.getLogger(__name__)
REDIS_URL =  os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses = True) 
os.makedirs("static/images", exist_ok=True) 

def check_rate_limit(request: Request):
    """Membatasi user maksimal 5 request per 60 detik berdasarkan IP Addres"""
    client_ip = request.client.host
    key = f"rate limit:{client_ip}"
    request_count = redis_client.get(key)

    if request_count and int(request_count) >= 5:
        logger.warning("Rate limit exceeded for IP: %s", client_ip)
        raise HTTPException(
            status_code= 429,
            detail="Terlalu banyak request! Server kelelahan. Silahkan coba lagi dalam 1 menit."
        )
    if not request_count:
        redis_client.setex(key, 60, 1)
    else:
        redis_client.incr(key)


def clear_inventory_cache():
    """Menghapus semua cache pencarian inventory agar tidak ada data basi"""

    for key in redis_client.scan_iter("inventory_search:*"):
        redis_client.delete(key)
    logger.info('Cache cleared: all stale inventory data removed')



router = APIRouter(
    prefix= "/inventory", # Semua URL otomatis diawali /inventory
    tags=["Inventory Management"] 
)


# =======================================
# EXPORT TO CSV (LAPORAN MANAJEER)
# =======================================
@router.get("/export/csv")
def export_inventory_csv(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user) 
):
    """Download seluruh data inventaris saat ini dalam format CSV (Excel)"""
    items = db.query(models.InventoryDB).all()
    stream = io.StringIO()
    writer = csv.writer(stream) 
    writer.writerow(["ID Barang", "Nama Barang", "Harga", "Sisa Stock", "Deskripsi", "Link Gambar"])
    for item in items:
        writer.writerow([
            item.id,
            item.name,
            item.price,
            item.stock,
            item.description,
            item.image_url if item.image_url else "Tidak Ada Gambar"
        ])
    stream.seek(0)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=Laporan_Stock_Gudang.csv"
    return response

# ========================================
# DASHBOARD STATISTICS (AGRERASI)
# ========================================
@router.get("/dashboard/stats")
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):

    """Mengambil rangkuman statisics untuk layar utama (Dashboard)"""
    total_items = db.query(func.count(models.InventoryDB.id)).scalar() or 0
    total_physical_count = db.query(func.sum(models.InventoryDB.stock)).scalar() or 0
    critical_stock_count = db.query(func.count(models.InventoryDB.id)).filter(models.InventoryDB.stock < 10).scalar() or 0
    total_asset_value = db.query(func.sum(cast(models.InventoryDB.price, BigInteger) * models.InventoryDB.stock)).scalar() or 0

    return {
        "status": "success",
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
    trending_data = redis_client.zrevrange("trending_search", 0, 4, withscores=True)
    result = []
    for item in trending_data:
        keyword, score = item
        result.append({
            "keyword": keyword,
            "search_count":int(score)
        })
    return {"trending_data":result}


#=============================
#         READ (GET)
#=============================
@router.get("/", response_model=List[InventorySchema])
def get_inventory(request: Request,
                  db: Session = Depends(get_db),
                  current_user : models.UserDB = Depends(security.get_current_user),
                  rate_limit : None = Depends(check_rate_limit), 
                  search: Optional[str] = "", 
                  skip: int = 0,
                  limit: int = 10, 

                  #   query parameters untuk filter 
                  min_price: Optional[int] = None, 
                  max_price: Optional[int] = None,
                  min_stock: int = 0,
                  sorted_by: Optional[str] = "id",
                  sorted_order: Optional[str] = "asc"
                  ):
    
    search_term = search.strip().lower() if search else "" 
    if search:
        redis_client.zincrby("trending_search", 1, search_term)
    
    cache_key = f'inventory_search:{search_term}_skip:{skip}_limit:{limit}_minP:{min_price}_maxP:{max_price}_minS:{min_stock}'
    cached_data = redis_client.get(cache_key)

    if cached_data:
        logger.info('Cache HIT for key: %s', cache_key)
        return json.loads(cached_data)
    logger.info("Cache MISS, querying PostgreSQL for keys %s", cache_key)
    query = db.query(models.InventoryDB).filter(models.InventoryDB.is_deleted == False)

    if search: 
        query = query.filter(models.InventoryDB.name.ilike(f"%{search}%"))
    
    if min_price is not None:
        query = query.filter(models.InventoryDB.price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.InventoryDB.price <= max_price)

    if min_stock is not None:
        query = query.filter(models.InventoryDB.stock >= min_stock)
    
    if sorted_by == "price":
        query = query.order_by(desc(models.InventoryDB.price) if sorted_order == "desc" else asc(models.InventoryDB.price))
    elif sorted_by == "name":
        query = query.order_by(desc(models.InventoryDB.name) if sorted_order == "desc" else asc(models.InventoryDB.name))
    elif sorted_by == "stock":
        query = query.order_by(desc(models.InventoryDB.stock) if sorted_order == "desc" else asc(models.InventoryDB.stock))
    else:
        """default mengurutkan berdasarkan ID"""
        query = query.order_by(desc(models.InventoryDB.id) if sorted_order == "desc" else asc(models.InventoryDB.id))
    
    #logika pagniaton
    items = query.offset(skip).limit(limit).all()
    items_dict = jsonable_encoder(items)
    redis_client.setex(cache_key, 60, json.dumps(items_dict))
    return items



#=============================
#        CREATE (POST)
#=============================

@router.post("/", status_code=201)
def create_inventory(inventory : InventorySchema, 
                     db : Session = Depends(get_db),
                     current_user : models.UserDB = Depends(security.get_current_user) 
                     ):
    cek_duplikasi = db.query(models.InventoryDB).filter(models.InventoryDB.id == inventory.id).first()
    if cek_duplikasi:
        raise HTTPException(status_code=400, detail="ID already registered")

    new_inventory = models.InventoryDB(
        name = inventory.name,
        price = inventory.price,
        stock = inventory.stock,
        description = inventory.description,
        owner_id = current_user.id 
    )
    logger.info('Saving new inventory item: %s', new_inventory.name)
    db.add(new_inventory)
    db.commit()
    logger.info('Item successfully committed to database: %s', new_inventory.name)
    db.refresh(new_inventory)

    """Pencatatan Transaksi awal"""
    new_transaction = models.TransactionDB(
        item_id= new_inventory.id,
        user_id= current_user.id,
        transaction_type = "IN", 
        quantity= new_inventory.stock,
        notes = "Stok awal saat pendaftaran barang baru"
    )

    db.add(new_transaction)
    db.commit()
    clear_inventory_cache()
    logger.info("Sending email notification via Celery for item: %s", new_inventory.name)
    send_notification_email.delay(new_inventory.name)
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
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
    
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not Found")
    '''mengecek kepemilika: jika ID memiliki barang BEDA dengan ID user yang login'''
    
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail= "Not authorized to update this item")
    
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
        db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
        if db_item is None or db_item.is_deleted == True:  
            raise HTTPException(status_code=404, detail="Item Not Found or Already deleted")
        
        if db_item.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail= "Not authorized to delete this item")

        '''Soft delete bernilai True'''
        db_item.is_deleted = True

        new_transaction = models.TransactionDB(
            item_id= db_item.id,
            user_id= current_user.id,
            transaction_type = "OUT", 
            quantity= db_item.stock,
            notes = "Barang dihapus (soft delete)"
        )
        db.add(new_transaction)
        db.commit() 
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
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
    
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan di database.")
    
    if db_item.is_deleted == False:
        return {"message": f"Barang dengan id {id} tidak ada di tong sampah (Status masih aktif)."}
    
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Kamu tidak berhak mengembalikan barang ini.")
    
    db_item.is_deleted = False
    db.commit()
    clear_inventory_cache()
    return {"message": f"Item with id {id} succesfully restored from trash!"}


#===========================
#   UPLOAD GAMBAR BARANG
#===========================
@router.post("/{id}/image")
def upload_item_image(
    id: int,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
): 
    """Mengunggah file gambar (JPG/PNG) untuk barang tertentu."""
    db_item = (db.query(models.InventoryDB)
               .filter(models.InventoryDB.id == id, models.InventoryDB.is_deleted == False)
               .first())
    
    if not db_item:
        raise HTTPException(status_code= 404, detail="Item not found")
    
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak berhak mengubah gambar barang ini")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail='File must be an image!')
    
    file_extention = file.filename.split(".")[-1]
    unique_filename = f"item_{id}_{uuid.uuid4().hex[:8]}.{file_extention}"
    file_location = f'static/images/{unique_filename}'

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
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
def update_stock(
    item_id: int, 
    payload: StockUpdateRequest,
    db: Session = Depends(get_db),
    current_user : models.UserDB = Depends(security.get_current_user)
    ): 

    change_amount = payload.change_amount
    item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    
    if item.stock + change_amount < 0:
        raise HTTPException(status_code=400, detail="Transaksi gagal: Stock tidak mencukupi (Minus)!")
    
    item.stock += change_amount
    db.commit()
    log_type = LogType.IN.value if change_amount > 0 else LogType.OUT.value

    record_stock_log.delay(item_id=item.id, 
                           change_amount=change_amount, 
                           log_type=log_type, 
                           user_id=current_user.id)
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

    item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    
    logs = db.query(models.StockLog)\
             .filter(models.StockLog.item_id == item_id)\
             .order_by(models.StockLog.created_at.desc())\
             .all()
             
    return logs


@router.patch("/{id}/stock")
def adjust_stock(
    id: int,
    payload: StockAdjustRequest,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    amount = payload.amount
    notes = payload.notes
    
    db_item = db.query(models.InventoryDB)\
    .filter(models.InventoryDB.id == id, models.InventoryDB.is_deleted == False)\
            .with_for_update().first()
    
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan atau sudah dihapus")
    
    if payload.amount < 0 and db_item.stock + payload.amount < 0:
        raise HTTPException(status_code=400,
                            detail = f'Stock tidak mencukupi! Sista stock saat ini hanya {db_item.stock}.')
    db_item.stock += payload.amount

    if payload.amount != 0:
        log_type = LogType.IN.value if payload.amount > 0 else LogType.OUT.value

        new_transaction = models.TransactionDB(
            item_id=db_item.id,
            user_id = current_user.id,
            transaction_type = log_type,
            quantity=abs(payload.amount),
            notes=notes
        )
        db.add(new_transaction)
    db.commit()
    clear_inventory_cache()

    return{
        "message": "Stock berhasil diupdate!",
        "item_name": db_item.name,
        "current_stock": db_item.stock,
        "transaction_logged": True if amount != 0 else False
    }
    
