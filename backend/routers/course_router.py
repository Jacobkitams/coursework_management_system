from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db
from schemas import schemas
from models import models
from auth.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role not in ['admin', 'lecturer']:
        raise HTTPException(status_code=403, detail="Not authorized to create courses")
    
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/", response_model=List[schemas.CourseResponse])
def get_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    courses = db.query(models.Course).offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}
