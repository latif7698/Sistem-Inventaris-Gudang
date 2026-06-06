# 📦 Enterprise Warehouse Inventory API

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/celery-%2337814A.svg?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

A high-performance, production-ready RESTful API built for scalable warehouse inventory and supply chain management. Engineered with a robust modern backend stack to handle high-concurrency requests, automated background tasks, and strict data security.

---

## 🌟 Architecture & Core Features

This project demonstrates a complete Software Development Life Cycle (SDLC) and modern backend infrastructure — far beyond standard CRUD operations.

| Feature | Description |
|---|---|
| 🔒 **Security (OAuth2 & JWT)** | Strict endpoint protection with hashed JWT tokens and role-based ownership validation |
| ⚡ **Caching & Rate Limiting** | Redis integration to cache hot endpoints and mitigate traffic spikes, reducing PostgreSQL load |
| ⚙️ **Async Processing (Celery)** | Heavy tasks (email notifications, data exports) offloaded to Celery Workers; scheduled via Celery Beat |
| 🛡️ **Resilient Infrastructure** | Deployed on GCP (e2-micro) with Nginx as a Reverse Proxy/API Gateway |
| 🐳 **Containerization** | Fully Dockerized via `docker-compose.yml` for consistent local and production environments |
| 🚥 **CI/CD Pipeline** | GitHub Actions workflow auto-runs tests and deploys to GCP via SSH on every push |
| 🧪 **Comprehensive Testing** | Unit/Integration tests with `pytest`; Load & stress testing with `Locust` (DDoS simulation) |
| 🗄️ **Database Management** | PostgreSQL (Neon DB) + SQLAlchemy ORM, Alembic migrations, and automated data seeding |

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| **Backend Framework** | FastAPI (Python) |
| **Database & ORM** | PostgreSQL, SQLAlchemy, Alembic |
| **Caching & Queue** | Redis, Celery (Worker & Beat) |
| **Security** | Passlib, Bcrypt, Python-Jose (JWT) |
| **DevOps & Infra** | Docker, Docker Compose, Nginx, GCP, GitHub Actions |
| **Testing** | Pytest, Locust, HTTPX |

---

## 🚀 Quick Start (Local Development)

Thanks to Docker Compose, spinning up the full enterprise stack locally takes less than a minute.

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/Sistem-Inventaris-Gudang.git
cd Sistem-Inventaris-Gudang
```

**2. Setup environment variables**

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@db:5432/inventory_db
SECRET_KEY=your_secure_jwt_secret_key
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
```

**3. Build and run with Docker Compose**

```bash
docker-compose up -d --build
```

**4. Run database migrations and seed data**

```bash
docker-compose exec web alembic upgrade head
docker-compose exec web python seed.py
```

The API will be live at **`http://localhost:8000`**.
Interactive Swagger UI docs available at **`http://localhost:8000/docs`**.

---

## 📈 Load Testing (Locust)

To simulate high traffic and validate server resilience:

```bash
locust -f load_test.py
```

Then open `http://localhost:8089` in your browser, set the number of concurrent users and spawn rate, and start the stress test.

---

## 📡 Production Deployment

This API is actively deployed on Google Cloud Platform.

| Component | Detail |
|---|---|
| **Host** | Google Cloud VM (e2-micro, Ubuntu Linux) |
| **Reverse Proxy** | Nginx — routes domain traffic to Dockerized FastAPI |
| **Domain Routing** | DuckDNS |
| **CI/CD** | GitHub Actions (auto-deploy via SSH on push to `main`) |

---

## 📁 Project Structure

```
Sistem-Inventaris-Gudang/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API route handlers
│   ├── schemas/             # Pydantic schemas
│   ├── core/                # Config, security, dependencies
│   └── tasks/               # Celery async tasks
├── tests/
│   ├── test_auth.py         # Auth unit/integration tests
│   ├── test_crud.py         # CRUD unit/integration tests
│   └── load_test.py         # Locust load testing script
├── alembic/                 # Database migration files
├── seed.py                  # Mock data seeding script
├── docker-compose.yml       # Multi-container orchestration
├── nginx.conf               # Nginx reverse proxy config
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD pipeline
└── .env                     # Environment variables (not committed)
```

---

## 👤 Author

**Asep Abdul Latip (Latif)**
Computer Science Student · Backend Engineering Enthusiast

Passionate about Cloud Infrastructure, DevSecOps, and High-Performance Systems.

- 🔗 LinkedIn: [Your LinkedIn URL]
- 📧 Email: [Your Professional Email]

---

> Developed as a capstone project representing an enterprise-grade backend architecture.