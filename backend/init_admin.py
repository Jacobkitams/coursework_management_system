import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import models
from auth.auth import get_password_hash

def init_admin():
    db = SessionLocal()
    admin = db.query(models.User).filter(models.User.email == "admin@university.edu").first()
    if not admin:
        hashed_password = get_password_hash("admin123")
        db_admin = models.User(
            full_name="System Admin",
            email="admin@university.edu",
            password=hashed_password,
            role="admin"
        )
        db.add(db_admin)
        db.commit()
        print("Admin user created: admin@university.edu / admin123")
    else:
        print("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    init_admin()
