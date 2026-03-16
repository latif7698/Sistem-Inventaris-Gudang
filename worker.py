import os
import time
from celery import Celery
from celery.schedules import crontab

# 1. Panggil papan pesanan (Redis)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# 2. Bangun Dapur Celery (Nama Dapur, Papan Pesanan, dan Tempat Simpan Hasil)
celery_app = Celery(
    "inventory_worker",
    broker = REDIS_URL,
    backend = REDIS_URL
)

#===========================================
#JADWAL RUTINITAS SANG MANAJER (CELERY BEAT)
#===========================================
celery_app.conf.beat_schedule = {
    'laporan-stok-tiap-10-detik': {
        'task': 'worker.check_stock_routine', # Nama fungsi yang akan dipanggil
        'schedule':10.0, # Dijalankan setiap 10 detik (Khusus untuk testing malam ini)

        # CATATAN INDUSTRI:
        # Kalau di dunia nyata, kita pakai crontab untuk jadwal spesifik.
        # Contoh jalan tiap jam 08:00 pagi: 'schedule': crontab(hour=8, minute=0)
    },
}

# ==========================================
# TUGAS RUTIN YANG AKAN DIKERJAKAN
# ==========================================
@celery_app.task
def check_stock_routine():
    """Tugas yang berjalan otomatis tanpa perlu API / User yang memicu"""
    print("🤖 [CRON JOB] Manajer berteriak: Cek barang yang stoknya menipis sekarang!")
    # Nanti di dunia nyata, logika query ke database untuk ngecek stok ditaruh di sini
    return "Pengecekan rutin selesai."

# 3. Buat tugas Berat (Contoh: Kirim email palsu)
@celery_app.task
def send_notification_email(item_name: str):
    """Simulasi Pekerjaan berat yang membutuhkan waktu lama"""
    print(f"[CELERY] Memulai pengiriman email untuk barang: {item_name}...")
    # Kita suruh program tidur 5s untuk mensimulasikan koneksi internet lambat
    time.sleep(5)

    print(f"[CELERY] Email sukses terkirim ke 50 cabang untuk {item_name}!")
    return f"Email Sent for {item_name}"