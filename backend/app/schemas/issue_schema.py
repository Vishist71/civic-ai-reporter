from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IssueCreate(BaseModel):
    category: Optional[str] = "Unknown"
    latitude: float
    longitude: float
    address: Optional[str] = None
    description: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str

class IssueResponse(BaseModel):
    id: int
    category: str
    confidence: float
    description: Optional[str]
    latitude: float
    longitude: float
    address: Optional[str]
    original_image_path: str
    annotated_image_path: Optional[str]
    status: str
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True