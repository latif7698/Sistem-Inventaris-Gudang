from locust import HttpUser, task, between
import random
import string

class InventoryUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.username = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.password = "password123"
        
        reg_res = self.client.post("/register", json={"username": self.username, "password": self.password})
        if reg_res.status_code == 422:
            print(f" ERROR 422 REGISTER: {reg_res.json()}") 
            
            
        log_res = self.client.post("/login", data={"username": self.username, "password": self.password})
        if log_res.status_code == 200:
            token = log_res.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f" ERROR LOGIN {log_res.status_code}: {log_res.text}")
            self.headers = {}

    @task(2)
    def get_all_inventory(self):
        res = self.client.get("/inventory", headers=getattr(self, 'headers', {}))
        if res.status_code in [404, 422]:
            print(f" ERROR GET {res.status_code}: {res.text}")

    @task(1)
    def create_item(self):
        item_id = random.randint(1000, 9999)
        res = self.client.post("/inventory", json={
            "name": f"Barang {item_id}",
            "price": random.randint(1000, 50000),
            "stock": random.randint(1, 100),
            "description": "Barang dari Locust"
        }, headers=getattr(self, 'headers', {}))
        
        if res.status_code == 422:
            print(f" ERROR 422 CREATE: {res.json()}") 