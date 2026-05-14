import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import models
from auth.auth import get_password_hash

def seed_users():
    db = SessionLocal()
    
    # Check student
    student = db.query(models.User).filter(models.User.email == "student@university.edu").first()
    if not student:
        hashed_password = get_password_hash("student123")
        db_student = models.User(
            full_name="John Student",
            email="student@university.edu",
            password=hashed_password,
            role="student"
        )
        db.add(db_student)
        print("Student user created: student@university.edu / student123")
    else:
        print("Student user already exists.")
        
    # Check lecturer
    lecturer = db.query(models.User).filter(models.User.email == "lecturer@university.edu").first()
    if not lecturer:
        hashed_password = get_password_hash("lecturer123")
        db_lecturer = models.User(
            full_name="Dr. Jane Smith",
            email="lecturer@university.edu",
            password=hashed_password,
            role="lecturer"
        )
        db.add(db_lecturer)
        print("Lecturer user created: lecturer@university.edu / lecturer123")
    else:
        print("Lecturer user already exists.")
        
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_users()
