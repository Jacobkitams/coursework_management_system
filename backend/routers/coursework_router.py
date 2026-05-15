from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os
import shutil
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db
from schemas import schemas
from models import models
from auth.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[schemas.CourseworkResponse])
def get_my_courseworks(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role == 'admin':
        return db.query(models.Coursework).all()
    return db.query(models.Coursework).filter(models.Coursework.lecturer_id == current_user.id).all()

@router.post("/")
async def create_coursework(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ['lecturer', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    form_data = await request.form()
    
    title = form_data.get('title')
    description = form_data.get('description', "")
    cw_type = form_data.get('type', 'file')
    deadline_str = form_data.get('deadline')
    total_marks = int(form_data.get('total_marks') or 100)
    status = form_data.get('status', 'published')
    course_id = int(form_data.get('course_id') or 0)
    instructions = form_data.get('instructions')
    questions_json = form_data.get('questions_json')
    
    if not title or not course_id:
        raise HTTPException(status_code=422, detail="Title and Course are required")

    # Parse deadline
    deadline_val = None
    if deadline_str:
        try:
            deadline_val = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
        except ValueError:
            deadline_val = datetime.utcnow()

    # Create Coursework object
    db_coursework = models.Coursework(
        title=title,
        description=description,
        type=cw_type,
        instructions=instructions,
        deadline=deadline_val,
        total_marks=total_marks,
        status=status,
        course_id=course_id,
        lecturer_id=current_user.id
    )
    db.add(db_coursework)
    db.flush() 

    # Handle MCQ Questions if present
    if questions_json and cw_type in ['mcq', 'mixed']:
        try:
            questions_data = json.loads(questions_json)
            for q_idx, q_data in enumerate(questions_data):
                db_question = models.MCQQuestion(
                    coursework_id=db_coursework.id,
                    question_text=q_data['question_text'],
                    marks=int(q_data.get('marks') or 1),
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
        except Exception as e:
            print(f"Error parsing questions: {e}")

    # Handle File Attachments
    # Use request.form() to get all files
    files = form_data.getlist('files')
    for file in files:
        if isinstance(file, UploadFile) and file.filename:
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
    query = db.query(models.Coursework).filter(models.Coursework.course_id == course_id)
    if current_user.role == 'student':
        query = query.filter(models.Coursework.status == 'published')
    return query.all()

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

@router.put("/{coursework_id}")
async def update_coursework(
    coursework_id: int,
    data: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ['lecturer', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    coursework = db.query(models.Coursework).filter(models.Coursework.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=404, detail="Coursework not found")
        
    if current_user.role != 'admin' and coursework.lecturer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        cw_data = json.loads(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")

    coursework.title = cw_data.get('title', coursework.title)
    coursework.description = cw_data.get('description', coursework.description)
    coursework.instructions = cw_data.get('instructions', coursework.instructions)
    if cw_data.get('deadline'):
        coursework.deadline = datetime.fromisoformat(cw_data.get('deadline').replace("Z", "+00:00"))
    coursework.total_marks = cw_data.get('total_marks', coursework.total_marks)
    coursework.duration = cw_data.get('duration', coursework.duration)
    coursework.status = cw_data.get('status', coursework.status)
    
    db.commit()
    db.refresh(coursework)
    return coursework
