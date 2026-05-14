from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db
from schemas import schemas
from models import models
from auth.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.SubmissionResponse)
def submit_coursework(
    coursework_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != 'student':
        raise HTTPException(status_code=403, detail="Only students can submit coursework")
        
    coursework = db.query(models.Coursework).filter(models.Coursework.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=404, detail="Coursework not found")
        
    file_path = f"uploads/submissions/{current_user.id}_{coursework_id}_{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    submission = models.Submission(
        student_id=current_user.id,
        coursework_id=coursework_id,
        submission_file=file_path
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

@router.get("/my-submissions", response_model=List[schemas.SubmissionResponse])
def get_my_submissions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return db.query(models.Submission).filter(models.Submission.student_id == current_user.id).all()

@router.get("/coursework/{coursework_id}", response_model=List[schemas.SubmissionResponse])
def get_coursework_submissions(coursework_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role not in ['lecturer', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view submissions")
    return db.query(models.Submission).filter(models.Submission.coursework_id == coursework_id).all()

@router.put("/{submission_id}/grade", response_model=schemas.SubmissionResponse)
def grade_submission(
    submission_id: int, 
    grade_data: schemas.GradeUpdate,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != 'lecturer':
        raise HTTPException(status_code=403, detail="Not authorized to grade")
        
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    submission.grade = grade_data.grade
    submission.feedback = grade_data.feedback
    db.commit()
    db.refresh(submission)
    return submission
