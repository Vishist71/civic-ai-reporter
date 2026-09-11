import os
import math
import shutil
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, engine
from app.models.issue import Issue
from app.services.detector import analyze_civic_issue, get_address_from_coords, verify_issue_resolution
from app.services.alert_service import send_priority_alert
from pydantic import BaseModel

router = APIRouter()

# Auto-migrate SQLite schema
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE issues ADD COLUMN resolved_image_path VARCHAR"))
        conn.commit()
except Exception:
    pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE issues ADD COLUMN upvotes INTEGER DEFAULT 1"))
        conn.commit()
except Exception:
    pass


class StatusUpdateRequest(BaseModel):
    status: str

class LoginRequest(BaseModel):
    username: str
    password: str

MUNICIPAL_USERS = {
    "admin": {"password": "admin123", "role": "SUPER_ADMIN", "dept": "Municipal Commissioner / All Departments", "allowed": "ALL"},
    "pwd_officer": {"password": "pwd123", "role": "PWD_ROADS", "dept": "PWD - Roads & Infrastructure", "allowed": "Pothole"},
    "sanitation_officer": {"password": "clean123", "role": "SANITATION", "dept": "Sanitation & Solid Waste Management", "allowed": "Garbage"},
    "emergency_officer": {"password": "alert123", "role": "EMERGENCY_SERVICES", "dept": "Disaster, Water & Sewerage Board", "allowed": "Emergency"}
}

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_sla_hours(priority: str) -> int:
    return 24 if (priority or "").lower() == "high" else 48

@router.post("/auth/login")
def municipal_login(req: LoginRequest):
    user = MUNICIPAL_USERS.get(req.username.strip())
    if not user or user["password"] != req.password.strip():
        raise HTTPException(status_code=401, detail="Invalid Municipal Officer credentials.")
    return {
        "status": "success",
        "username": req.username,
        "role": user["role"],
        "department": user["dept"],
        "allowed_scope": user["allowed"],
        "token": f"mock_token_{uuid.uuid4()}"
    }

@router.post("/report")
async def report_issue(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = os.path.splitext(image.filename)[1] or ".jpg"
        unique_name = f"{uuid.uuid4()}{file_ext}"
        original_file_path = os.path.join(upload_dir, unique_name)

        with open(original_file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        category, confidence, priority, annotated_path = analyze_civic_issue(original_file_path, description)

        active_issues = db.query(Issue).filter(Issue.status != "Resolved").all()
        for existing in active_issues:
            if existing.category == category:
                dist = calculate_haversine_distance(latitude, longitude, existing.latitude, existing.longitude)
                if dist <= 50.0:
                    current_upvotes = existing.upvotes if existing.upvotes is not None else 1
                    existing.upvotes = current_upvotes + 1
                    
                    if existing.upvotes >= 3 and existing.priority != "High":
                        existing.priority = "High"
                        background_tasks.add_task(send_priority_alert, existing)
                    
                    db.commit()
                    db.refresh(existing)

                    return {
                        "status": "duplicate_merged",
                        "is_duplicate": True,
                        "issue_id": existing.id,
                        "category": existing.category,
                        "confidence": existing.confidence,
                        "priority": existing.priority,
                        "address": existing.address,
                        "upvotes": existing.upvotes,
                        "created_at_iso": existing.created_at.isoformat() if existing.created_at else datetime.utcnow().isoformat(),
                        "sla_hours": get_sla_hours(existing.priority),
                        "annotated_image_path": existing.annotated_image_path or existing.image_path,
                        "message": f"Similar active hazard found within {int(dist)}m. Merged (+1 Confirmation) to Ticket #CIVIC-{existing.id}."
                    }

        address = get_address_from_coords(latitude, longitude)
        new_issue = Issue(
            image_path=f"uploads/{unique_name}",
            annotated_image_path=annotated_path,
            latitude=latitude,
            longitude=longitude,
            address=address,
            category=category,
            confidence=confidence,
            priority=priority,
            description=description,
            status="Reported",
            upvotes=1,
            created_at=datetime.utcnow()
        )
        db.add(new_issue)
        db.commit()
        db.refresh(new_issue)

        if priority == "High":
            background_tasks.add_task(send_priority_alert, new_issue)

        return {
            "status": "success",
            "is_duplicate": False,
            "issue_id": new_issue.id,
            "category": category,
            "confidence": confidence,
            "priority": priority,
            "address": address,
            "upvotes": 1,
            "created_at_iso": new_issue.created_at.isoformat(),
            "sla_hours": get_sla_hours(new_issue.priority),
            "annotated_image_path": annotated_path,
            "created_at": new_issue.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"Error in /report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issues")
def get_all_issues(db: Session = Depends(get_db)):
    issues = db.query(Issue).order_by(Issue.created_at.desc()).all()
    results = []
    for i in issues:
        results.append({
            "id": i.id,
            "category": i.category,
            "priority": i.priority,
            "status": i.status,
            "upvotes": i.upvotes or 1,
            "confidence": i.confidence,
            "address": i.address,
            "latitude": i.latitude,
            "longitude": i.longitude,
            "description": i.description,
            "image_path": i.image_path,
            "annotated_image_path": i.annotated_image_path,
            "resolved_image_path": i.resolved_image_path,
            "created_at_iso": i.created_at.isoformat() if i.created_at else datetime.utcnow().isoformat(),
            "sla_hours": get_sla_hours(i.priority),
            "created_at": i.created_at.strftime("%b %d, %Y - %I:%M %p") if i.created_at else "Recently"
        })
    return results

@router.get("/issues/{issue_id}")
def get_single_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Ticket not found with this ID")
    return {
        "id": issue.id,
        "category": issue.category,
        "priority": issue.priority,
        "status": issue.status,
        "upvotes": issue.upvotes or 1,
        "confidence": issue.confidence,
        "address": issue.address,
        "latitude": issue.latitude,
        "longitude": issue.longitude,
        "description": issue.description,
        "image_path": issue.image_path,
        "annotated_image_path": issue.annotated_image_path,
        "resolved_image_path": issue.resolved_image_path,
        "created_at_iso": issue.created_at.isoformat() if issue.created_at else datetime.utcnow().isoformat(),
        "sla_hours": get_sla_hours(issue.priority),
        "created_at": issue.created_at.strftime("%b %d, %Y - %I:%M %p") if issue.created_at else "Recently"
    }

@router.put("/issues/{issue_id}/status")
def update_issue_status(issue_id: int, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.status = req.status
    db.commit()
    db.refresh(issue)
    return {"status": "success", "issue_id": issue.id, "new_status": issue.status}

@router.post("/issues/{issue_id}/resolve")
async def resolve_issue_with_verification(
    issue_id: int,
    resolution_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(resolution_image.filename)[1] or ".jpg"
    unique_name = f"resolved_{uuid.uuid4()}{file_ext}"
    saved_path = os.path.join(upload_dir, unique_name)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(resolution_image.file, buffer)

    is_verified, ver_conf, label = verify_issue_resolution(saved_path, issue.category)

    issue.status = "Resolved"
    issue.resolved_image_path = f"uploads/{unique_name}"
    db.commit()
    db.refresh(issue)

    return {
        "status": "success",
        "issue_id": issue.id,
        "is_ai_verified": is_verified,
        "verification_confidence": ver_conf,
        "verification_label": label,
        "resolved_image_path": issue.resolved_image_path
    }