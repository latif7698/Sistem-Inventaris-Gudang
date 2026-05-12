import random
from faker import Faker
from database import SessionLocal
from models import InventoryDB

# Inisialisasi Faker dengan lokalisasi Indonesia
fake = Faker('id_ID')

# Daftar kata kunci agar namanya terdengar seperti barang gudang elektronik
brands = ["Samsung", "Asus", "Lenovo", "MacBook", "Dell", "HP", "Xiaomi", "Oppo"]
types = ["Pro", "Air", "Ultra", "Lite", "Max", "Gaming Edition", "Enterprise"]

def seed_data(jumlah=50):
    print(f"🌱 Memulai proses seeding {jumlah} data barang...")
    db = SessionLocal()
    
    try:
        for i in range(jumlah):
            # Membuat nama barang acak namun masuk akal
            brand = random.choice(brands)
            tipe = random.choice(types)
            nama_barang = f"{brand} {fake.word().capitalize()} {tipe}"
            
            # Harga acak antara 2 juta - 40 juta (kelipatan 100.000)
            harga = random.randint(20, 400) * 100000
            
            # Stok acak antara 1 - 200
            stok = random.randint(1, 200)
            
            # Buat objek database
            item_baru = InventoryDB(
                name=nama_barang,
                price=harga,
                stock=stok,
                description=fake.sentence(nb_words=10),
                owner_id=1, # Asumsikan ID kamu adalah 1
                is_deleted=False
            )
            
            db.add(item_baru)
            
        # Simpan semua ke PostgreSQL sekaligus
        db.commit()
        print("✅ Seeding SELESAI! Database-mu sekarang kaya raya!")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Jalankan fungsi seeding dengan 50 data (bisa kamu ubah angkanya)
    seed_data(50)