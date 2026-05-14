from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..auth.auth import get_current_active_user

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    total_students = db.query(models.User).filter(models.User.role == 'student').count()
    total_lecturers = db.query(models.User).filter(models.User.role == 'lecturer').count()
    total_courses = db.query(models.Course).count()
    total_submissions = db.query(models.Submission).count()
    
    # Recent activity logs (mocked for now based on recent submissions/users)
    recent_submissions = db.query(models.Submission).order_by(models.Submission.submitted_at.desc()).limit(5).all()
    logs = []
    for sub in recent_submissions:
        logs.append({
            "icon": "fa-file-upload",
            "color": "#8b5cf6",
            "text": f"New submission for coursework #{sub.coursework_id}",
            "time": "Just now"
        })
        
    return {
        "total_students": total_students,
        "total_lecturers": total_lecturers,
        "total_courses": total_courses,
        "total_submissions": total_submissions,
        "logs": logs
    }

@router.post("/users", response_model=schemas.UserResponse)
def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        password=user_data.password, # In production, hash this!
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
