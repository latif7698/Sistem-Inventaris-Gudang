from database import SessionLocal
from sqlalchemy import text

def fix_sequence():
    print("🔧 Memperbaiki mesin penghitung ID (Sequence) PostgreSQL...")
    db = SessionLocal()
    try:
        # Perintah SQL asli untuk menyinkronkan ulang ID
        query = text("SELECT setval('inventory_id_seq', (SELECT MAX(id) FROM inventory));")
        db.execute(query)
        db.commit()
        print("✅ PENYEMBUHAN SUKSES! Mesin penghitung sudah normal kembali!")
    except Exception as e:
        print(f"❌ Gagal: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_sequence()