# 📌 Temuan Isu & Rekomendasi Perbaikan Codebase

> Dokumen ini merangkum daftar sisa isu/temuan pada codebase serta rekomendasi prioritas perbaikannya.

---

## 1. Isu yang Masih Ada

### 🔴 Kritis

#### `main.py` di disk — Tidak sinkron dengan yang sudah diperbaiki
File `main.py` yang aktif di disk masih versi lama: masih memiliki `asyncio.sleep(0.5)`, duplikasi import, dan mendaftarkan `reports_router` yang filenya tidak ada. Perbaikan sudah ada di script tetapi `main.py` di disk perlu diperbarui ulang.

```python
# Di main.py disk saat ini (BERMASALAH):
from routers import inventory, auth          # baris 1
from routers import inventory, transactions  # baris 2 — duplikasi inventory & auth hilang
# ...
from routers import inventory, auth, reports_router, transactions, media_router, stock_router
# reports_router.py TIDAK ADA di direktori routers/
```

#### `reports_router.py` — File tidak ada
`routers/reports_router.py` tidak ada di direktori tetapi pernah diimport di versi lama `main.py`. Perlu dibuat atau referensi import perlu dihapus.

#### `media_router.py` dan `stock_router.py` — Tidak didaftarkan ke app
Kedua file router sudah ada di direktori `routers/` tetapi versi `main.py` aktif tidak mendaftarkannya, sehingga endpoint `/inventory/{id}/image`, `/inventory/{item_id}/stock`, `/inventory/{id}/stock`, dan `/inventory/{item_id}/logs` tidak aktif.

### 🟠 Sedang

#### `security.py` — Fallback `SECRET_KEY` berisiko
```python
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_rahasia_lokal")
```
Jika environment variable `SECRET_KEY` tidak di-set, aplikasi berjalan dengan kunci JWT yang lemah dan diketahui publik. Idealnya aplikasi **gagal startup** (`raise ValueError`) bila `SECRET_KEY` tidak ada di production.

#### `cache.py` — Nama env var tidak konsisten
```python
REDIS_URL = os.getenv("REDIS", "redis://localhost:6379")  # key: "REDIS"
```
Sedangkan `worker.py` menggunakan:
```python
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")  # key: "REDIS_URL"
```
Dua nama env var berbeda untuk hal yang sama — salah satu akan selalu gagal membaca nilai dari `.env`.

#### `database.py` — Dua mekanisme konfigurasi DATABASE_URL
Konfigurasi database membaca `DATABASE_URL` terlebih dahulu, lalu fallback ke variabel individual (`DB_HOST`, `DB_PORT`, dll.). Namun `docker-compose.yml` hanya menyetel variabel individual, bukan `DATABASE_URL`. Ini tidak langsung bermasalah tapi membingungkan.

### 🟡 Minor / Saran

#### `requirements.txt` — Banyak dependensi tidak relevan
Library berikut ada di `requirements.txt` tapi tidak digunakan aplikasi:
- `Flask`, `flask-cors`, `Flask-Login`, `Werkzeug`, `Jinja2`, `itsdangerous` — seluruh stack Flask
- `python-socketio`, `python-engineio`, `websockets`, `bidict`, `simple-websocket` — WebSocket/Socket.IO stack
- `q`, `psutil`, `gevent`, `greenlet`, `blinker`, dll.

> **Saran**: Audit dan bersihkan `requirements.txt` — ini akan mempercepat build Docker image secara signifikan.

#### `fix_db.py` — Duplikasi tanggung jawab dengan Alembic
File `fix_db.py` memanggil `Base.metadata.create_all(bind=engine)` langsung ke database. Dalam proyek yang menggunakan Alembic, operasi schema harus selalu lewat migrasi Alembic untuk menghindari inkonsistensi.

#### `.github/workflows/ci.yml` — Tidak ada step automated testing
Pipeline CI/CD hanya melakukan build & push Docker image — tidak ada langkah `pytest` sebelum push. Kode yang gagal test bisa lolos ke production.

#### `docker-compose.yml` — Image tag `latest` di-hardcode
Semua service menggunakan tag `latest`, menyulitkan traceability antara kode di git dan image yang berjalan.

#### `nginx/default.conf` — Domain di-hardcode
Domain `portofolio-inventaris-latif.duckdns.org` di-hardcode, menyulitkan deployment ke domain lain tanpa modifikasi file konfigurasi.

---

## 2. Rekomendasi Prioritas Tindak Lanjut

| # | Prioritas | Aksi |
|---|---|---|
| 1 | 🔴 | Perbarui `main.py` — konsolidasikan import, daftarkan `media_router` & `stock_router`, hapus `asyncio.sleep(0.5)` |
| 2 | 🔴 | Buat `routers/reports_router.py` atau hapus referensinya secara permanen |
| 3 | 🔴 | Tambahkan step `pytest` di `.github/workflows/ci.yml` sebelum Docker build |
| 4 | 🟠 | Standarisasi nama env var Redis: gunakan `REDIS_URL` secara konsisten |
| 5 | 🟠 | Hapus fallback `SECRET_KEY` — buat aplikasi gagal startup jika tidak di-set |
| 6 | 🟡 | Bersihkan `requirements.txt` — hapus Flask stack dan library tidak terpakai |
| 7 | 🟡 | Tambahkan test negatif: akses tanpa token, update barang milik user lain, stok negatif |
| 8 | 🟡 | Gunakan image tag spesifik (`${{ github.sha }}`) di CI/CD dan `docker-compose.yml` |
