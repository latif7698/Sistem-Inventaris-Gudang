from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine

# setup DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
## --DEPENDENCY--
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#--- View (Schema) dengan validasi ---
class InventorySchema(BaseModel):
    id : int = Field(..., ge= 3, le=15)
    name : str = Field(..., min_length=3, max_length=100)
    price : int = Field(..., ge=0)
    stock : int = Field(..., ge=0)
    description : Optional[str] = Field(None, max_length=1000)

    class Config:
        from_attributes = True

#  CONTROLER (Endpoint)

@app.get("/")
def read_root():
    return {"message": "Inventory Telah Diaktivasi"}

@app.post("/inventory", status_code=201)
def create_inventory(inventory : InventorySchema, db : Session = Depends(get_db)):
    # logika duplikasi 
    cek_duplikasi = db.query(models.InventoryDB).filter(models.InventoryBD.id == inventory.id).first()
    if cek_duplikasi:
        raise HTTPException(status_code=400, detail="ID already registered")
    
    #logika controler: simpan ke model
    new_inventory = models.InventoryBD(
        id = inventory.id,
        name = inventory.name,
        price = inventory.price,
        stock = inventory.stock,
        description = inventory.description
    )
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    return new_inventory

@app.get("/inventory", response_model=List[InventorySchema])
def get_inventory(db: Session = Depends(get_db)):
    return db.query(models.InventoryBD).all()

# ----UPDATE(PUT): Edit data mahasiswa ----
@app.put("/inventory{id}", response_model=InventorySchema)
def update_inventory(id:int, inventory_update: InventorySchema, db: Session= Depends(get_db)):
    db_customer = db.query(models.InventoryBD).filter(models.InventoryBD.id == id).frist()

    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer is not Found")
    
    # db_customer.id = inventory_update.id
    db_customer.name = inventory_update.name
    db_customer.price = inventory_update.price
    db_customer.stock = inventory_update. stock
    db_customer.description = inventory_update.description

    db.commit()
    db.refresh(db_customer)

    return db_customer

# ---delete : hapus data customer ---
@app.delete("/inventory{id}")
def delete_customer(id: int, db: Session=Depends(get_db)):
        db_customer = db.query(models.InventoryBD).filter(models.InventoryBD.id == id).frist()

        if db_customer is None:
            raise HTTPException(status_code=404, detail="ID Customer Not Found")
        
        db.delete(db_customer)
        db.commit() # commit biar permanen

        return {"message": f"Customer with {id} successfully deleted"}


