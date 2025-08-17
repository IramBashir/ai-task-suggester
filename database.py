# database.py
from sqlmodel import create_engine, SQLModel, Session
import os

DB_FILE = os.getenv("DEV_DB_FILE", "dev.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

# echo=True prints SQL to console (helpful during dev)
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

# helper factory for sessions (you'll use this in routes later)
def get_session():
    with Session(engine) as session:
        yield session
