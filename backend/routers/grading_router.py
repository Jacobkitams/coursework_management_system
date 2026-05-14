from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..auth.auth import get_current_active_user

router = APIRouter(prefix="/grading", tags=["Grading"])

def calculate_grade_letter(percentage: float):
    if percentage >= 90: return "A"
    if percentage >= 80: return "B+"
    if percentage >= 70: return "B"
    if percentage >= 60: return "C"
    if percentage >= 50: return "D"
    return "F"

@router.get("/submissions", response_model=List[schemas.SubmissionResponse])
async def get_lecturer_submissions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all coursework created by this lecturer
    courseworks = db.query(models.Coursework).filter(models.Coursework.lecturer_id == current_user.id).all()
    coursework_ids = [cw.id for cw in courseworks]
    
    submissions = db.query(models.Submission).filter(models.Submission.coursework_id.in_(coursework_ids)).all()
    return submissions

@router.post("/", response_model=schemas.GradeResponse)
async def grade_submission(
    grade_data: schemas.GradeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    submission = db.query(models.Submission).filter(models.Submission.id == grade_data.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    coursework = db.query(models.Coursework).filter(models.Coursework.id == submission.coursework_id).first()
    
    # Calculate percentage and grade letter
    percentage = (grade_data.marks_obtained / coursework.total_marks) * 100
    grade_letter = calculate_grade_letter(percentage)
    
    # Check if grade already exists
    existing_grade = db.query(models.Grade).filter(models.Grade.submission_id == grade_data.submission_id).first()
    
    if existing_grade:
        existing_grade.marks_obtained = grade_data.marks_obtained
        existing_grade.percentage = percentage
        existing_grade.grade_letter = grade_letter
        existing_grade.feedback = grade_data.feedback
        existing_grade.remarks = grade_data.remarks
        existing_grade.status = grade_data.status
        db.commit()
        db.refresh(existing_grade)
        return existing_grade
    
    new_grade = models.Grade(
        submission_id=grade_data.submission_id,
        lecturer_id=current_user.id,
        marks_obtained=grade_data.marks_obtained,
        percentage=percentage,
        grade_letter=grade_letter,
        feedback=grade_data.feedback,
        remarks=grade_data.remarks,
        status=grade_data.status
    )
    
    db.add(new_grade)
    
    # Update submission status
    submission.status = "graded" if grade_data.status == "published" else "grading"
    
    db.commit()
    db.refresh(new_grade)
    return new_grade

@router.get("/stats")
async def get_grading_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["lecturer", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    courseworks = db.query(models.Coursework).filter(models.Coursework.lecturer_id == current_user.id).all()
    cw_ids = [cw.id for cw in courseworks]
    
    total_submissions = db.query(models.Submission).filter(models.Submission.coursework_id.in_(cw_ids)).count()
    graded_submissions = db.query(models.Grade).filter(models.Grade.lecturer_id == current_user.id, models.Grade.status == "published").count()
    pending_grading = total_submissions - graded_submissions
    
    avg_score = db.query(func.avg(models.Grade.percentage)).filter(models.Grade.lecturer_id == current_user.id, models.Grade.status == "published").scalar() or 0
    max_score = db.query(func.max(models.Grade.percentage)).filter(models.Grade.lecturer_id == current_user.id, models.Grade.status == "published").scalar() or 0
    min_score = db.query(func.min(models.Grade.percentage)).filter(models.Grade.lecturer_id == current_user.id, models.Grade.status == "published").scalar() or 0
    
    return {
        "total_submissions": total_submissions,
        "graded_submissions": graded_submissions,
        "pending_grading": pending_grading,
        "average_score": round(avg_score, 2),
        "highest_score": round(max_score, 2),
        "lowest_score": round(min_score, 2)
    }
