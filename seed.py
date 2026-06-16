import random
from faker import Faker
from database import SessionLocal
from models import InventoryDB

fake = Faker('id_ID')

brands = ["Samsung", "Asus", "Lenovo", "MacBook", "Dell", "HP", "Xiaomi", "Oppo"]
types = ["Pro", "Air", "Ultra", "Lite", "Max", "Gaming Edition", "Enterprise"]

def seed_data(jumlah=200):
    print(f"🌱 Memulai proses seeding {jumlah} data barang...")
    db = SessionLocal()
    
    try:
        for i in range(jumlah):
            brand = random.choice(brands)
            tipe = random.choice(types)
            nama_barang = f"{brand} {fake.word().capitalize()} {tipe}"
            
            harga = random.randint(20, 400) * 100000
            
            stok = random.randint(1, 200)
            
            item_baru = InventoryDB(
                name=nama_barang,
                price=harga,
                stock=stok,
                description=fake.sentence(nb_words=10),
                owner_id=1, 
                is_deleted=False
            )
            
            db.add(item_baru)
            
        db.commit()
        print(" Seeding SELESAI! Database-mu sekarang kaya raya!")
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data(200)