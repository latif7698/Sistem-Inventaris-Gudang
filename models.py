from sqlalchemy import Column, Integer, String, Float
from database import Base

class InventoryBD(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key = True, index=True)
    name = Column(String(100), nullable= False )
    price = Column(Integer,nullable= False)
    stock = Column(Integer,nullable= False)
    description = Column(String(1000))

# ---- Tambahan baru tabel user ----
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, unique=True, index = True) #unique =True, boar gak kembar
    hashed_password = Column(String) # Kita simpan HASIL ACAKAN, bukan password asli