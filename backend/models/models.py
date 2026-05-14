from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, JSON, func
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(50)) # 'student', 'lecturer', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    courses = relationship("Course", back_populates="lecturer")
    submissions = relationship("Submission", back_populates="student")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), index=True)

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String(150), index=True)
    course_code = Column(String(20), unique=True, index=True)
    lecturer_id = Column(Integer, ForeignKey("users.id"))

    lecturer = relationship("User", back_populates="courses")
    courseworks = relationship("Coursework", back_populates="course")

class Coursework(Base):
    __tablename__ = "courseworks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), index=True)
    description = Column(Text)
    type = Column(String(50), default="file") # mcq, written, file, mixed
    instructions = Column(Text, nullable=True)
    deadline = Column(DateTime)
    total_marks = Column(Integer, default=100)
    duration = Column(Integer, nullable=True) # in minutes
    status = Column(String(50), default="published") # draft, published, scheduled
    semester = Column(String(20), nullable=True)
    academic_year = Column(String(20), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lecturer_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="courseworks")
    submissions = relationship("Submission", back_populates="coursework")
    questions = relationship("MCQQuestion", back_populates="coursework", cascade="all, delete-orphan")
    attachments = relationship("CourseworkFile", back_populates="coursework", cascade="all, delete-orphan")

class MCQQuestion(Base):
    __tablename__ = "mcq_questions"

    id = Column(Integer, primary_key=True, index=True)
    coursework_id = Column(Integer, ForeignKey("courseworks.id"))
    question_text = Column(Text)
    image_path = Column(String(255), nullable=True)
    marks = Column(Integer, default=1)
    order = Column(Integer, default=0)

    coursework = relationship("Coursework", back_populates="questions")
    choices = relationship("MCQChoice", back_populates="question", cascade="all, delete-orphan")

class MCQChoice(Base):
    __tablename__ = "mcq_choices"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("mcq_questions.id"))
    choice_text = Column(Text)
    is_correct = Column(Integer, default=0) # 1 for correct, 0 for incorrect

    question = relationship("MCQQuestion", back_populates="choices")

class CourseworkFile(Base):
    __tablename__ = "coursework_files"

    id = Column(Integer, primary_key=True, index=True)
    coursework_id = Column(Integer, ForeignKey("courseworks.id", ondelete="CASCADE"))
    file_name = Column(String(150))
    file_path = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    coursework = relationship("Coursework", back_populates="attachments")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), unique=True)
    lecturer_id = Column(Integer, ForeignKey("users.id"))
    marks_obtained = Column(Float)
    percentage = Column(Float)
    grade_letter = Column(String(5))
    feedback = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(String(20), default="draft") # draft, published
    graded_at = Column(DateTime, default=func.now())

    submission = relationship("Submission", back_populates="grade")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    coursework_id = Column(Integer, ForeignKey("courseworks.id"))
    submission_file = Column(String(255), nullable=True)
    written_answer = Column(Text, nullable=True)
    mcq_answers = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    
    grade = relationship("Grade", back_populates="submission", uselist=False)
    feedback = Column(Text, nullable=True)

    student = relationship("User", back_populates="submissions")
    coursework = relationship("Coursework", back_populates="submissions")
