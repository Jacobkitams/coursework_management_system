from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os
import shutil
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db
from schemas import schemas
from models import models
from auth.auth import get_current_active_user

router = APIRouter()

import json

@router.post("/", response_model=schemas.CourseworkResponse)
async def create_coursework(
    data: str = Form(...),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ['lecturer', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Parse JSON data
    try:
        cw_data = json.loads(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")

    # Create Coursework object
    db_coursework = models.Coursework(
        title=cw_data.get('title'),
        description=cw_data.get('description'),
        type=cw_data.get('type', 'file'),
        instructions=cw_data.get('instructions'),
        deadline=datetime.fromisoformat(cw_data.get('deadline').replace("Z", "+00:00")),
        total_marks=cw_data.get('total_marks', 100),
        duration=cw_data.get('duration'),
        status=cw_data.get('status', 'published'),
        semester=cw_data.get('semester'),
        academic_year=cw_data.get('academic_year'),
        course_id=cw_data.get('course_id'),
        lecturer_id=current_user.id
    )
    db.add(db_coursework)
    db.flush() # Get ID without committing

    # Handle MCQ Questions if present
    if cw_data.get('type') in ['mcq', 'mixed'] and 'questions' in cw_data:
        for q_idx, q_data in enumerate(cw_data['questions']):
            db_question = models.MCQQuestion(
                coursework_id=db_coursework.id,
                question_text=q_data['question_text'],
                marks=q_data.get('marks', 1),
                order=q_idx
            )
            db.add(db_question)
            db.flush()
            
            for c_data in q_data.get('choices', []):
                db_choice = models.MCQChoice(
                    question_id=db_question.id,
                    choice_text=c_data['choice_text'],
                    is_correct=int(c_data['is_correct'])
                )
                db.add(db_choice)

    # Handle File Attachments
    for file in files:
        file_path = f"uploads/courseworks/{db_coursework.id}/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        db_file = models.CourseworkFile(
            coursework_id=db_coursework.id,
            file_name=file.filename,
            file_path=file_path
        )
        db.add(db_file)

    db.commit()
    db.refresh(db_coursework)
    return db_coursework

@router.get("/course/{course_id}", response_model=List[schemas.CourseworkResponse])
def get_courseworks_by_course(course_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return db.query(models.Coursework).filter(models.Coursework.course_id == course_id).all()

@router.get("/{coursework_id}", response_model=schemas.CourseworkResponse)
def get_coursework(coursework_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    coursework = db.query(models.Coursework).filter(models.Coursework.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=404, detail="Coursework not found")
    return coursework

@router.delete("/{coursework_id}")
def delete_coursework(coursework_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    coursework = db.query(models.Coursework).filter(models.Coursework.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=404, detail="Coursework not found")
    
    if current_user.role != 'admin' and coursework.lecturer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(coursework)
    db.commit()
    return {"message": "Coursework deleted"}
