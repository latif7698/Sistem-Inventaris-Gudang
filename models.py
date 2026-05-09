from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean 
from database import Base
from sqlalchemy.orm import relationship # <-- Tambah relationship 
from sqlalchemy.sql import func
import enum

class InventoryDB(Base):
    __tablename__ = "inventory" #pastikan nama tabel konsisten

    id = Column(Integer, primary_key = True, index=True) 
    name = Column(String(100), index = True, nullable= False )
    price = Column(Integer, nullable= False)
    stock = Column(Integer, nullable= False)
    description = Column(String(1000), nullable = True)
    # KOLOM BARU: Siapa Pemiliknya?
    owner_id = Column(Integer, ForeignKey("users.id"))
    image_url = Column(String, nullable = True) # nullable = True karena barang boleh gak punya foto
    is_deleted = Column(Boolean, default=False) # Default False (artinya barang aktif/tidak dihapus)
    # HUBUNGAN KE USER (Satu Barang milik satu Owner)
    owner = relationship("UserDB", back_populates = "items")
    logs = relationship("StockLog", back_populates="item", cascade="all, delete")

# gunakan class ini untuk menyangkal incossistensi input data seperti masuk Enter dsb
class LogType(enum.Enum):
    IN = "IN"
    OUT = "OUT"
    UPDATE = "UPDATE"

class StockLog(Base):
    __tablename__ = "stock_logs"

    id = Column(Integer, primary_key = True, index = True)
    item_id = Column(Integer, ForeignKey("inventory.id", ondelete="CASCADE"))
    change_amount = Column(Integer) # Contoh: +50 (masuk) atau -10 (keluar)
    log_type = Column(Enum(LogType)) # "IN", "OUT", atau "UPDATE"
    user_id = Column(Integer, ForeignKey("users.id",ondelete="SET NULL"),nullable = True) #opsional tapi ini untuk mengubah
    user_actor = relationship("UserDB")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    item = relationship("InventoryDB", back_populates = "logs")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String(50), unique=True, index = True) #unique =True, biar gak kembar
    hashed_password = Column(String(255)) # Kita simpan HASIL ACAKAN, bukan password asli

    # HUBUNGKAN KE INVENTORY (Satu User punya banyak items)
    items = relationship("InventoryDB", back_populates = "owner")