from locust import HttpUser, task, between

class SeranganInventaris(HttpUser):
    # Simulasi user yang mikir 1-2 detik sebelum ngeklik lagi
    wait_time = between(1, 2)

    @task
    def serang_endpoint_item(self):
        # Nembak endpoint API lu terus-menerus
        self.client.get("/api/items")

    @task(3) # Angka 3 berarti task ini 3x lebih sering dieksekusi
    def simulasi_brute_force(self):
        # Simulasi nembak halaman login dengan payload JSON
        self.client.post("/login", json={"username": "admin", "password": "password_ngasal"})
