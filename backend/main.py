from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import sys
import os
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import engine, Base
from routers import auth_router, coursework_router, course_router, user_router, submission_router, grading_router

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coursework Management System API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware: redirect /pages/something → /pages/something.html
@app.middleware("http")
async def redirect_html_extension(request: Request, call_next):
    path = request.url.path
    # If it's a page path without a file extension, redirect to .html
    if path.startswith("/pages/") and "." not in path.split("/")[-1]:
        return RedirectResponse(url=path + ".html", status_code=301)
    return await call_next(request)

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

# Serve Frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
