from sqlalchemy import Column, Integer, String, Float, ForeignKey # <-- Tambahkan ForeignKey
from database import Base
from sqlalchemy.orm import relationship # <-- Tambah relationship 

class InventoryDB(Base):
    __tablename__ = "inventory" #pastikan nama tabel konsisten

    id = Column(Integer, primary_key = True, index=True) # ID Barang (Auto Increment lebih baik, tapi pakai manual dulu sesuai kodemu)
    name = Column(String(100), nullable= False )
    price = Column(Integer,nullable= False)
    stock = Column(Integer,nullable= False)
    description = Column(String(1000), nullable = True)

    # KOLOM BARU: Siapa Pemiliknya?
    owner_id = Column(Integer, ForeignKey("users.id"))

    # HUBUNGAN KE USER (Satu Barang milik satu Owner)
    owner = relationship("UserDB", back_populates = "items")

# ---- Tambahan baru tabel user ----
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, unique=True, index = True) #unique =True, biar gak kembar
    hashed_password = Column(String) # Kita simpan HASIL ACAKAN, bukan password asli

    # HUBUNGKAN KE INVENTORY (Satu User punya banyak items)
    items = relationship("InventoryDB", back_populates = "owner")