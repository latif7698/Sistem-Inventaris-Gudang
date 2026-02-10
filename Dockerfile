# 1. Ambil Base Image (OS Linux + Python 3.12 sudah terinstall)
FROM python:3.12-slim

# 2. Set folder kerja di dalam container (Ibarat 'cd /app')
WORKDIR /app

# 3. Copy file requirements dulu (Supaya installasi di-cache dan cepat)
COPY requirements.txt .

# 4. Install library yang dibutuhkan
# --no-cache-dir biar ukuran file tidak bengkak
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy seluruh kodingan project kamu ke dalam container
COPY . .

# 6. Perintah wajib saat container dinyalakan: "Jalankan Server!"
# --host 0.0.0.0 artinya "Terima tamu dari luar container"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]