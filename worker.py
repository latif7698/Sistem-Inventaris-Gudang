import os
import time
import models
from celery import Celery
from celery.schedules import crontab
from database import SessionLocal

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "inventory_worker",
    broker = REDIS_URL,
    backend = REDIS_URL
)

celery_app.conf.beat_schedule = {
    'laporan-stok-tiap-10-detik': {
        'task': 'worker.check_stock_routine', 
        'schedule':10.0, 
    },
}

@celery_app.task
def check_stock_routine():
    """Tugas yang berjalan otomatis tanpa perlu API / User yang memicu"""
    print("[CRON JOB] Manajer berteriak: Cek barang yang stoknya menipis sekarang!")
    return "Pengecekan rutin selesai."

@celery_app.task
def send_notification_email(item_name: str):
    """Simulasi Pekerjaan berat yang membutuhkan waktu lama"""
    print(f"[CELERY] Memulai pengiriman email untuk barang: {item_name}...")
    time.sleep(5)

    print(f"[CELERY] Email sukses terkirim ke 50 cabang untuk {item_name}!")
    return f"Email Sent for {item_name}"


@celery_app.task(name="log_stock_change_task")
def record_stock_log(item_id: int, change_amount: int, log_type: str, user_id: int = None):
    """
    Tugas latar belakang untuk mencatat riwayat pergerakan barang
    """
    db = SessionLocal()
    try:
        new_log = models.StockLog(
            item_id=item_id,
            change_amount=change_amount,
            log_type=log_type,
            user_id=user_id
        )

        db.add(new_log)
        db.commit()
        return f"Sukses mencatat log: Item{item_id} | {log_type} {change_amount}"
    except Exception as e:
        db.rollback()
        return f"Gagal mencatat log: {str(e)}"
    finally:
        db.close()