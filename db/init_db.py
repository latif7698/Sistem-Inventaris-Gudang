import models
from database import SessionLocal, engine

def init_db():
    models.Base.metadata.create_all(bind=engine)

