from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import json
import os
import shutil
from datetime import datetime
from database import get_db
from models import models
from schemas import schemas
from auth.auth import get_current_active_user

router = APIRouter(tags=["Submissions"])

def calculate_grade_letter(percentage: float):
    if percentage >= 90: return "A"
    if percentage >= 80: return "B+"
    if percentage >= 70: return "B"
    if percentage >= 60: return "C"
    if percentage >= 50: return "D"
    return "F"

@router.post("/", response_model=schemas.SubmissionResponse)
async def submit_coursework(
    coursework_id: int = Form(...),
    file: Optional[UploadFile] = File(None),
    written_answer: Optional[str] = Form(None),
    mcq_answers: Optional[str] = Form(None), # Expecting JSON string
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != 'student':
        raise HTTPException(status_code=403, detail="Only students can submit coursework")
        
    coursework = db.query(models.Coursework).filter(models.Coursework.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=404, detail="Coursework not found")

    # Check if student already submitted
    existing_sub = db.query(models.Submission).filter(
        models.Submission.student_id == current_user.id,
        models.Submission.coursework_id == coursework_id
    ).first()
    if existing_sub:
        raise HTTPException(status_code=400, detail="Assignment already submitted")

    # Check deadline
    if coursework.deadline and datetime.utcnow() > coursework.deadline:
        raise HTTPException(status_code=403, detail="Submission deadline has passed. This assignment is now closed.")

    file_path = None
    if file:
        file_path = f"uploads/submissions/{current_user.id}_{coursework_id}_{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    mcq_data = None
    if mcq_answers:
        mcq_data = json.loads(mcq_answers)

    submission = models.Submission(
        student_id=current_user.id,
        coursework_id=coursework_id,
        submission_file=file_path,
        written_answer=written_answer,
        mcq_answers=mcq_data,
        status="pending"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # --- AUTO GRADING LOGIC FOR MCQ ---
    if coursework.type == "mcq" and mcq_data:
        correct_count = 0
        questions = db.query(models.MCQQuestion).filter(models.MCQQuestion.coursework_id == coursework_id).all()
        total_questions = len(questions)
        
        if total_questions > 0:
            for question in questions:
                # Find the correct choice for this question
                correct_choice = db.query(models.MCQChoice).filter(
                    models.MCQChoice.question_id == question.id,
                    models.MCQChoice.is_correct == 1
                ).first()
                
                # Check if student's answer matches
                student_choice_id = mcq_data.get(str(question.id))
                if student_choice_id and int(student_choice_id) == correct_choice.id:
                    correct_count += 1
            
            # Calculate score
            percentage = (correct_count / total_questions) * 100
            marks_obtained = (percentage / 100) * coursework.total_marks
            grade_letter = calculate_grade_letter(percentage)
            
            # Save automatic grade
            auto_grade = models.Grade(
                submission_id=submission.id,
                lecturer_id=coursework.lecturer_id,
                marks_obtained=marks_obtained,
                percentage=percentage,
                grade_letter=grade_letter,
                feedback="Automatically graded by System.",
                remarks="MCQ Auto-Grade",
                status="published" # Auto-grades are published immediately
            )
            db.add(auto_grade)
            submission.status = "graded"
            db.commit()

    return submission

@router.get("/my", response_model=List[schemas.SubmissionResponse])
async def get_my_submissions(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    return db.query(models.Submission).filter(models.Submission.student_id == current_user.id).all()
