from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean 
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

class InventoryDB(Base):
    __tablename__ = "inventory" 

    id = Column(Integer, primary_key = True, index=True) 
    name = Column(String(100), index = True, nullable= False )
    price = Column(Integer, nullable= False)
    stock = Column(Integer, nullable= False)
    description = Column(String(1000), nullable = True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    image_url = Column(String, nullable = True) 
    is_deleted = Column(Boolean, default=False) 
    owner = relationship("UserDB", back_populates = "items")
    logs = relationship("StockLog", back_populates="item", cascade="all, delete")


class LogType(enum.Enum):
    IN = "IN"
    OUT = "OUT"
    UPDATE = "UPDATE"

class StockLog(Base):
    __tablename__ = "stock_logs"

    id = Column(Integer, primary_key = True, index = True)
    item_id = Column(Integer, ForeignKey("inventory.id", ondelete="CASCADE"))
    change_amount = Column(Integer) 
    log_type = Column(Enum(LogType)) 
    user_id = Column(Integer, ForeignKey("users.id",ondelete="SET NULL"),nullable = True) 
    user_actor = relationship("UserDB")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    item = relationship("InventoryDB", back_populates = "logs")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String(50), unique=True, index = True) 
    hashed_password = Column(String(255)) 

    items = relationship("InventoryDB", back_populates = "owner")

class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_type = Column(String) 
    quantity = Column(Integer)
    notes = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())