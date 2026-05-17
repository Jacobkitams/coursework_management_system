from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Department Schemas ---
class DepartmentBase(BaseModel):
    department_name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int

    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str
    department_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    department: Optional[DepartmentResponse] = None

    class Config:
        from_attributes = True

# --- Course Schemas ---
class CourseBase(BaseModel):
    course_name: str
    course_code: str
    lecturer_id: Optional[int] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    lecturer: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# --- MCQ Schemas ---
class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: int

class ChoiceCreate(ChoiceBase):
    pass

class ChoiceResponse(ChoiceBase):
    id: int
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    question_text: str
    marks: int = 1
    order: int = 0

class QuestionCreate(QuestionBase):
    choices: List[ChoiceCreate]

class QuestionResponse(QuestionBase):
    id: int
    image_path: Optional[str] = None
    choices: List[ChoiceResponse]
    class Config:
        from_attributes = True

class CourseworkFileResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    uploaded_at: datetime
    class Config:
        from_attributes = True

# --- Coursework Schemas ---
class CourseworkBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = ""
    type: str = "file" # mcq, written, file, mixed
    instructions: Optional[str] = None
    deadline: Optional[datetime] = None
    total_marks: int = 100
    duration: Optional[int] = None
    status: str = "published"
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    course_id: Optional[int] = None

class CourseworkCreate(CourseworkBase):
    questions: Optional[List[QuestionCreate]] = []

class CourseworkResponse(CourseworkBase):
    id: int
    lecturer_id: int
    created_at: datetime
    questions: List[QuestionResponse] = []
    attachments: List[CourseworkFileResponse] = []
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True

# --- Submission Schemas ---
class SubmissionBase(BaseModel):
    student_id: int
    coursework_id: int

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionResponse(SubmissionBase):
    id: int
    submission_file: Optional[str] = None
    written_answer: Optional[str] = None
    mcq_answers: Optional[dict] = None
    submitted_at: datetime
    status: str
    student: Optional[UserResponse] = None
    grade: Optional["GradeResponse"] = None

    class Config:
        from_attributes = True

# --- Grade Schemas ---
class GradeBase(BaseModel):
    marks_obtained: float
    feedback: Optional[str] = None
    remarks: Optional[str] = None
    status: str = "draft"

class GradeCreate(GradeBase):
    submission_id: int

class GradeResponse(GradeBase):
    id: int
    percentage: float
    grade_letter: str
    graded_at: datetime

    class Config:
        from_attributes = True

SubmissionResponse.update_forward_refs()
