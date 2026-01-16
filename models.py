from sqlalchemy import Column, Integer, String, Float
from database import Base

class InventoryBD(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key = True, index=True)
    name = Column(String(100), nullable= False )
    price = Column(Integer,nullable= False)
    stock = Column(Integer,nullable= False)
    description = Column(String(1000))