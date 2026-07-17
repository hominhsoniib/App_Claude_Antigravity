import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "quoteflow.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
