from locust import HttpUser, task, between

class SeranganInventaris(HttpUser):
    wait_time = between(1, 2)

    @task
    def serang_endpoint_item(self):
        self.client.get("/api/items")

    @task(3)
    def simulasi_brute_force(self):
        self.client.post("/login", json={"username": "admin", "password": "password_ngasal"})
