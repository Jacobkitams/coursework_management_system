from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db
from schemas import schemas
from models import models
from auth.auth import get_current_active_user, get_password_hash

router = APIRouter()

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    department_id: Optional[int] = None

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to view all users")
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to update users")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.email is not None:
        # Check email uniqueness
        existing = db.query(models.User).filter(models.User.email == update_data.email, models.User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use by another account")
        user.email = update_data.email
    if update_data.password is not None and update_data.password.strip() != "":
        user.password = get_password_hash(update_data.password)
    if update_data.department_id is not None:
        user.department_id = update_data.department_id if update_data.department_id > 0 else None

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to delete users")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return None

class DepartmentCreateBody(BaseModel):
    department_name: str

@router.get("/departments", response_model=List[schemas.DepartmentResponse])
def get_departments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return db.query(models.Department).all()

@router.post("/departments", response_model=schemas.DepartmentResponse)
def create_department(dept: DepartmentCreateBody, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    db_dept = models.Department(department_name=dept.department_name)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(dept)
    db.commit()
    return {"message": "Department deleted successfully"}
