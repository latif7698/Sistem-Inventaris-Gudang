import os
import time
import logging
from datetime import timedelta
import models
from celery import Celery
from database import SessionLocal

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "inventory_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.beat_schedule = {
    "laporan-stok-tiap-10-detik": {
        "task": "worker.check_stock_routine",
        "schedule": timedelta(seconds=10),
    },
}

@celery_app.task
def check_stock_routine():
    """Tugas yang berjalan otomatis tanpa perlu API / User yang memicu"""
    logger.info("[CRON JOB] Pengecekan stok rutin...")
    return "Pengecekan rutin selesai."

@celery_app.task
def send_notification_email(item_name: str):
    """Simulasi Pekerjaan berat yang membutuhkan waktu lama"""
    logger.info(f"[CELERY] Memulai pengiriman email untuk barang: {item_name}...")
    time.sleep(5)
    logger.info(f"[CELERY] Email sukses terkirim ke 50 cabang untuk {item_name}!")
    return f"Email Sent for {item_name}"

@celery_app.task(name="log_stock_change_task")
def record_stock_log(item_id: int, change_amount: int, log_type: str, user_id: int = None):
    """Tugas latar belakang untuk mencatat riwayat pergerakan barang"""
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
        return f"Sukses mencatat log: Item {item_id} | {log_type} {change_amount}"
    except Exception as e:
        db.rollback()
        logger.error(f"Gagal mencatat stock log: {str(e)}", exc_info=True)
        return f"Gagal mencatat log: {str(e)}"
    finally:
        db.close()
