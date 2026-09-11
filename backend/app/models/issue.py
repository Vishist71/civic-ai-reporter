from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    annotated_image_path = Column(String, nullable=True)
    resolved_image_path = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    category = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    priority = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="Reported")
    upvotes = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)