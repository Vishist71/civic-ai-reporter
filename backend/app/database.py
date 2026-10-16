from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🚀 PostgreSQL Enterprise Connection String
# Format: postgresql://username:password@localhost:5432/civiceye_db
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Vishist7700%40.@localhost:5432/civiceye_db"

# Create PostgreSQL Engine with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()