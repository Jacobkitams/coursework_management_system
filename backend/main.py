from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import engine, Base
from routers import auth_router, coursework_router, course_router, user_router, submission_router, grading_router, admin_router

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coursework Management System API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(user_router.router, prefix="/api/users", tags=["users"])
app.include_router(course_router.router, prefix="/api/courses", tags=["courses"])
app.include_router(coursework_router.router, prefix="/api/courseworks", tags=["courseworks"])
app.include_router(submission_router.router, prefix="/api/submissions", tags=["submissions"])
app.include_router(grading_router.router, prefix="/api/grading", tags=["grading"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Coursework Management System API"}
