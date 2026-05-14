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

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to view all users")
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users
