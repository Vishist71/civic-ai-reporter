from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=True)
    citizen_name = Column(String(100), nullable=True)
    citizen_phone = Column(String(15), nullable=True)
    category = Column(String(100))
    confidence = Column(Float)
    priority = Column(String(20))
    status = Column(String(20), default="Pending")
    upvotes = Column(Integer, default=1)
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(255))
    description = Column(String(500), nullable=True)
    image_path = Column(String(255))
    annotated_image_path = Column(String(255), nullable=True)
    resolved_image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)