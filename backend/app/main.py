from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import engine, Base
from app.api.endpoints import router as api_router

# Database tables create karein
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Civic AI Reporter API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root aur Folder paths definition
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend folder
ROOT_DIR = os.path.dirname(BASE_DIR)                                    # civic-ai-reporter folder
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# Uploads folder setup
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Frontend static files mount (agar CSS/JS files frontend folder me hain)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Include API endpoints
app.include_router(api_router, prefix="/api")

# Serve Frontend directly
@app.get("/")
def serve_home():
    frontend_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Civic AI Reporter Backend is live!"}