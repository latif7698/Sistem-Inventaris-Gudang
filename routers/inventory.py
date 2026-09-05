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
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Failed to initialize Redis client: {e}")
    redis_client = None

os.makedirs("static/images", exist_ok=True) 

def check_rate_limit(request: Request):
    """Membatasi user maksimal 5 request per 60 detik berdasarkan IP Address"""
    if not redis_client:
        return
    try:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"
        request_count = redis_client.get(key)

        if request_count and int(request_count) >= 60:
            logger.warning("Rate limit exceeded for IP: %s", client_ip)
            raise HTTPException(
                status_code=429,
                detail="Terlalu banyak request! Server kelelahan. Silahkan coba lagi dalam 1 menit."
            )
        if not request_count:
            redis_client.setex(key, 60, 1)
        else:
            redis_client.incr(key)
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"Redis rate limit check bypassed: {e}")

def clear_inventory_cache():
    """Menghapus semua cache pencarian inventory agar tidak ada data basi"""
    if not redis_client:
        return
    try:
        for key in redis_client.scan_iter("inventory_search:*"):
            redis_client.delete(key)
        logger.info("Cache cleared: all stale inventory data removed")
    except Exception as e:
        logger.debug(f"Redis cache clear bypassed: {e}")

def log_transaction(db: Session, item_id: int, user_id: int, transaction_type: str, quantity: int, notes: str = None):
    """Helper method untuk mencatat riwayat transaksi ke database"""
    transaksi = models.TransactionDB(
        item_id=item_id,
        user_id=user_id,
        transaction_type=transaction_type,
        quantity=quantity,
        notes=notes
    )
    db.add(transaksi)

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory Management"] 
)

# =======================================
# EXPORT TO CSV (LAPORAN MANAJER)
# =======================================
@router.get("/export/csv")
def export_inventory_csv(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user) 
):
    """Download seluruh data inventaris saat ini dalam format CSV (Excel)"""
    items = db.query(models.InventoryDB).filter(models.InventoryDB.is_deleted == False).all()
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
# DASHBOARD STATISTICS (AGREGASI)
# ========================================
@router.get("/dashboard/stats")
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user) 
):
    """Menampilkan ringkasan data inventaris (Total barang, total nilai aset, dan barang dengan stok menipis)"""
    total_items = db.query(models.InventoryDB).filter(models.InventoryDB.is_deleted == False).count()

    total_asset_value = db.query(
        func.sum(models.InventoryDB.price * cast(models.InventoryDB.stock, BigInteger))
    ).filter(models.InventoryDB.is_deleted == False).scalar() or 0

    low_stock_items = db.query(models.InventoryDB).filter(
        models.InventoryDB.is_deleted == False,
        models.InventoryDB.stock <= 5 
    ).all()

    return {
        "summary": {
            "total_active_items": total_items,
            "total_asset_value_idr": total_asset_value,
            "low_stock_alert_count": len(low_stock_items)
        },
        "low_stock_items": low_stock_items
    }

# ====================================================
# TRENDING KEYWORD SEARCH (FITUR UNGGULAN REDIS)
# ====================================================
@router.get("/trending")
def get_trending_searches():
    """Mengambil 5 kata kunci pencarian paling populer dari Redis"""
    if not redis_client:
        return []
    try:
        trending_data = redis_client.zrevrange("trending_search", 0, 4, withscores=True)
        results = []
        for keyword, score in trending_data:
            results.append({
                "keyword": keyword,
                "search_count": int(score) 
            })
        return results
    except Exception as e:
        logger.debug(f"Redis trending search bypassed: {e}")
        return []

# ========================================
# READ ALL & SEARCH INVENTORY (DENGAN CACHING)
# ========================================
@router.get("/", response_model=List[InventorySchema])
def read_all_inventory(
    search: Optional[str] = None,
    min_price: Optional[int] = None, 
    max_price: Optional[int] = None,
    limit: int = 10,
    skip: int = 0,
    sort_by: Optional[str] = "id", 
    order: Optional[str] = "asc",
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    request: Request = None,
    current_user: models.UserDB = Depends(security.get_current_user)
):
    if request:
        check_rate_limit(request)

    cache_key = f"inventory_search:{search}:{min_price}:{max_price}:{limit}:{skip}:{sort_by}:{order}:{include_deleted}"

    if redis_client:
        try:
            if search:
                search_term = search.strip().lower()
                redis_client.zincrby("trending_search", 1, search_term)

            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Serving data from Redis Cache")
                return json.loads(cached_data)
        except Exception as e:
            logger.debug(f"Redis cache get bypassed: {e}")

    query = db.query(models.InventoryDB)

    if not include_deleted:
        query = query.filter(models.InventoryDB.is_deleted == False)

    if search:
        query = query.filter(models.InventoryDB.name.ilike(f"%{search}%"))

    if min_price is not None:
        query = query.filter(models.InventoryDB.price >= min_price)

    if max_price is not None:
        query = query.filter(models.InventoryDB.price <= max_price)

    sort_column = getattr(models.InventoryDB, sort_by, models.InventoryDB.id)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    items = query.offset(skip).limit(limit).all()

    if redis_client:
        try:
            items_dict = jsonable_encoder(items)
            redis_client.setex(cache_key, 60, json.dumps(items_dict))
        except Exception as e:
            logger.debug(f"Redis cache set bypassed: {e}")

    return items

# =========================================
# CREATE INVENTORY
# =========================================
@router.post("/", status_code=201)
def create_inventory(
    item: schemas.InventoryCreate, 
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    new_item = models.InventoryDB(
        name=item.name,
        price=item.price,
        stock=item.stock,
        description=item.description,
        owner_id=current_user.id
    )
    if hasattr(item, "id") and item.id is not None:
        new_item.id = item.id

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    log_transaction(
        db=db,
        item_id=new_item.id,
        user_id=current_user.id,
        transaction_type="IN",
        quantity=new_item.stock,
        notes="Stok awal barang baru dibuat"
    )
    db.commit()

    try:
        send_notification_email.delay(new_item.name)
    except Exception as e:
        logger.warning(f"Celery task send_notification_email skipped: {e}")

    clear_inventory_cache()
    return new_item

# ==========================================
# UPDATE INVENTORY
# ==========================================
@router.put("/{id}", response_model=InventorySchema)
def update_item(
    id: int,
    item_update: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak mengupdate barang ini")

    db_item.name = item_update.name
    db_item.price = item_update.price
    db_item.stock = item_update.stock
    db_item.description = item_update.description

    db.commit()
    db.refresh(db_item)

    log_transaction(
        db=db,
        item_id=db_item.id,
        user_id=current_user.id,
        transaction_type="UPDATE",
        quantity=db_item.stock,
        notes="Data barang diperbarui"
    )
    db.commit()

    clear_inventory_cache()
    return db_item

# ============================================
# SOFT DELETE INVENTORY
# ============================================
@router.delete("/{id}")
def delete_item(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: models.UserDB = Depends(security.get_current_user)
):
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak menghapus barang ini")

    if db_item.is_deleted:
        raise HTTPException(status_code=400, detail="Barang ini sudah dihapus sebelumnya")

    db_item.is_deleted = True 
    db.commit()

    log_transaction(
        db=db,
        item_id=db_item.id,
        user_id=current_user.id,
        transaction_type="OUT",
        quantity=db_item.stock,
        notes="Barang dihapus (soft delete)"
    )
    db.commit()

    clear_inventory_cache()
    return {"message": f"Barang {db_item.name} berhasil dinonaktifkan (Soft Delete)"}

# =============================================
# RESTORE INVENTORY
# =============================================
@router.put("/{id}/restore")
def restore_item(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: models.UserDB = Depends(security.get_current_user)
):
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak memulihkan barang ini")

    if not db_item.is_deleted:
        raise HTTPException(status_code=400, detail="Barang ini aktif, tidak perlu di-restore")

    db_item.is_deleted = False 
    db.commit()

    log_transaction(
        db=db,
        item_id=db_item.id,
        user_id=current_user.id,
        transaction_type="IN",
        quantity=db_item.stock,
        notes="Barang dipulihkan (restore)"
    )
    db.commit()

    clear_inventory_cache()
    return {"message": f"Barang {db_item.name} berhasil dipulihkan"}

# =============================================
# UPLOAD IMAGE
# =============================================
@router.post("/{id}/image")
def upload_item_image(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/jpg"}
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya format gambar (JPEG/JPG/PNG) yang diperbolehkan!"
        )

    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak mengubah gambar barang ini")

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"item_{id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_location = f"static/images/{unique_filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_item.image_url = f"/static/images/{unique_filename}"
    db.commit()
    db.refresh(db_item)

    clear_inventory_cache()
    return {
        "message": "Gambar barang berhasil diunggah",
        "image_url": db_item.image_url
    }

# =============================================
# UPDATE / ADJUST STOCK
# =============================================
@router.put("/{item_id}/stock")
def update_stock(
    item_id: int,
    payload: schemas.StockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak mengubah stok barang ini")

    old_stock = db_item.stock
    new_stock = payload.new_stock
    difference = new_stock - old_stock

    if difference == 0:
        return {"message": "Stok tidak mengalami perubahan", "current_stock": db_item.stock}

    db_item.stock = new_stock
    db.commit()
    db.refresh(db_item)

    log_type = "IN" if difference > 0 else "OUT"
    log_transaction(
        db=db,
        item_id=db_item.id,
        user_id=current_user.id,
        transaction_type=log_type,
        quantity=abs(difference),
        notes=payload.notes or f"Update manual stok dari {old_stock} menjadi {new_stock}"
    )
    db.commit()

    try:
        record_stock_log.delay(
            item_id=item_id,
            change_amount=abs(difference),
            log_type=log_type,
            user_id=current_user.id
        )
    except Exception as e:
        logger.warning(f"Celery task record_stock_log skipped: {e}")

    clear_inventory_cache()
    return {
        "message": "Stok berhasil diperbarui",
        "item_id": item_id,
        "old_stock": old_stock,
        "new_stock": new_stock
    }

@router.patch("/{id}/stock")
def adjust_stock(
    id: int,
    payload: schemas.StockAdjustRequest,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    db_item = db.query(models.InventoryDB).filter(models.InventoryDB.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Anda tidak berhak mengubah stok barang ini")

    old_stock = db_item.stock
    amount = payload.amount
    log_type = payload.type.upper()

    if log_type == "IN":
        new_stock = old_stock + amount
    elif log_type == "OUT":
        if old_stock < amount:
            raise HTTPException(status_code=400, detail="Stok tidak mencukupi untuk pengurangan ini")
        new_stock = old_stock - amount
    else:
        raise HTTPException(status_code=400, detail="Tipe mutasi tidak valid. Harus IN atau OUT")

    db_item.stock = new_stock
    db.commit()
    db.refresh(db_item)

    log_transaction(
        db=db,
        item_id=db_item.id,
        user_id=current_user.id,
        transaction_type=log_type,
        quantity=amount,
        notes=payload.notes or f"Penyesuaian stok ({log_type})"
    )
    db.commit()

    clear_inventory_cache()
    return {
        "message": f"Stok berhasil di-adjust ({log_type})",
        "item_id": id,
        "old_stock": old_stock,
        "new_stock": new_stock
    }

@router.get("/{item_id}/logs", response_model=List[schemas.StockLogResponse])
def get_stock_logs(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserDB = Depends(security.get_current_user)
):
    item = db.query(models.InventoryDB).filter(models.InventoryDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    logs = db.query(models.StockLog).filter(models.StockLog.item_id == item_id).order_by(models.StockLog.created_at.desc()).all()
    return logs
