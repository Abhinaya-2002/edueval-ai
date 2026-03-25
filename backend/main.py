# main.py - Complete Backend for Render Deployment
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, date, timedelta
import uuid
import json
import os
import shutil
import time
import random
import string
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI
from difflib import SequenceMatcher
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
import numpy as np

# Load environment variables
load_dotenv()

# ==================================
# DATABASE SETUP
# ==================================

# Get database URL from environment (for Render PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./edueval.db")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with proper settings
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Initialize OpenAI (optional, will work without API key)
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except:
    client = None

# ==================================
# DATABASE MODELS
# ==================================

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    subject = Column(String, nullable=True)
    qualification = Column(String, nullable=True)
    experience = Column(Integer, default=0)
    institution_type = Column(String, default="school")
    status = Column(String, default="PENDING")
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, nullable=True)
    password = Column(String)
    language = Column(String, default="english")
    institution_type = Column(String, default="school")
    class_level = Column(String, nullable=True)
    section = Column(String, nullable=True)
    program = Column(String, nullable=True)
    parent_phone = Column(String, nullable=True)
    total_points = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.utcnow)
    badges = Column(JSON, default=[])
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(String, unique=True, index=True)
    subject = Column(String)
    chapter = Column(String)
    institution_type = Column(String, default="school")
    class_level = Column(String)
    section = Column(String, nullable=True)
    program = Column(String, nullable=True)
    duration = Column(String)
    total_marks = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("teachers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    exam_date = Column(Date, nullable=True)
    status = Column(String, default="DRAFT")
    exam_data = Column(Text)
    bloom_levels = Column(JSON, default={})
    teacher = relationship("Teacher")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    question_number = Column(Integer)
    question_type = Column(String)
    question_text = Column(Text)
    max_marks = Column(Integer)
    correct_option = Column(String, nullable=True)
    teacher_final_answer = Column(Text, nullable=True)
    bloom_level = Column(String)
    exam = relationship("Exam")

class Option(Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    option_text = Column(String)
    is_correct = Column(Boolean, default=False)
    question = relationship("Question")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    uploaded_pdf_path = Column(String)
    extracted_text = Column(Text, nullable=True)
    ai_total_marks = Column(Integer, default=0)
    final_total_marks = Column(Integer, default=0)
    ai_feedback_summary = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)
    weak_topics = Column(JSON, default=[])
    risk_level = Column(String, default="LOW")
    risk_factors = Column(JSON, default=[])
    status = Column(String, default="UPLOADED")
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")
    exam = relationship("Exam")

class StudentResponse(Base):
    __tablename__ = "student_responses"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_text = Column(Text, nullable=True)
    ai_is_correct = Column(Boolean, nullable=True)
    ai_marks_awarded = Column(Integer, default=0)
    ai_feedback = Column(Text, nullable=True)
    teacher_marks_awarded = Column(Integer, default=0)
    teacher_feedback = Column(Text, nullable=True)
    teacher_override = Column(Boolean, default=False)
    final_marks = Column(Integer, default=0)
    evaluated_status = Column(String, default="PENDING")
    submission = relationship("Submission")
    student = relationship("Student")
    question = relationship("Question")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    title = Column(String)
    message = Column(Text)
    type = Column(String)
    related_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")
    teacher = relationship("Teacher")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    user_type = Column(String)
    message = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class CareerGuidance(Base):
    __tablename__ = "career_guidance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    resume_text = Column(Text, nullable=True)
    career_interests = Column(Text, nullable=True)
    skills_assessment = Column(JSON, default={})
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")

class Leaderboard(Base):
    __tablename__ = "leaderboard"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    total_score = Column(Integer, default=0)
    exams_taken = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    rank = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")

class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    icon = Column(String)
    criteria = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

# ==================================
# DEPENDENCIES
# ==================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================================
# PYDANTIC MODELS
# ==================================

class AdminLogin(BaseModel):
    username: str
    password: str

class TeacherRegister(BaseModel):
    teacher_id: str
    name: str
    email: EmailStr
    password: str
    subject: str
    qualification: Optional[str] = None
    experience: Optional[int] = 0
    institution_type: str = "school"

class TeacherLogin(BaseModel):
    email: str
    password: str

class TeacherApprove(BaseModel):
    teacher_id: int
    status: str

class StudentRegister(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    password: str
    language: str = "english"
    institution_type: str = "school"
    class_level: str
    section: Optional[str] = None
    program: Optional[str] = None
    parent_phone: Optional[str] = None

class StudentLogin(BaseModel):
    student_id: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str
    user_type: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    user_type: str

class ChatRequest(BaseModel):
    user_id: int
    user_type: str
    message: str

class ExamRequest(BaseModel):
    subject: str
    chapter: str
    institution_type: str
    class_level: str
    section: Optional[str] = None
    program: Optional[str] = None
    duration: str
    exam_date: Optional[str] = None
    partA_bloom: str
    partB_bloom: str
    partC_bloom: str

class TeacherReviewItem(BaseModel):
    response_id: int
    teacher_marks: int
    teacher_feedback: Optional[str] = None
    teacher_override: bool = True

# ==================================
# APPLICATION SETTINGS
# ==================================

APP_SETTINGS = {
    "AUTO_GRADING_AFTER_SUBMISSION": True,
    "AUTO_PUBLISH_EXAMS": False,
    "MIN_ASSIGNMENT_MARKS": 5,
    "MAX_RETAKE_ATTEMPTS": 3
}

# Create folders
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_ADMIN = {
    "admin_id": "ADMIN001",
    "username": "admin",
    "password": "admin123",
    "email": "admin@edueval.com"
}

DEFAULT_BADGES = [
    {"name": "First Exam", "description": "Completed your first exam", "icon": "🎓", "criteria": "first_exam"},
    {"name": "Perfect Score", "description": "Scored 100%", "icon": "⭐", "criteria": "perfect_score"},
    {"name": "Consistent Learner", "description": "7-day streak", "icon": "🔥", "criteria": "streak_7"},
    {"name": "Assignment Master", "description": "5 assignments", "icon": "📝", "criteria": "assignments_5"},
]

# ==================================
# HELPER FUNCTIONS
# ==================================

def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def get_ai_evaluation(student_answer, correct_answer, max_marks):
    """Simple evaluation using similarity matching"""
    similarity = calculate_similarity(student_answer, correct_answer)
    marks = int(similarity * max_marks)
    
    if marks >= max_marks * 0.8:
        feedback = "Excellent! Great understanding."
    elif marks >= max_marks * 0.6:
        feedback = "Good answer! Some minor improvements needed."
    elif marks >= max_marks * 0.4:
        feedback = "Fair answer. Review the key concepts."
    else:
        feedback = "Needs improvement. Please review the topic thoroughly."
    
    return {"marks": marks, "feedback": feedback}

def get_ai_chat_response(message, user_context=""):
    """Simple chat response"""
    message_lower = message.lower()
    
    if "exam" in message_lower:
        return "I can help you prepare for exams! Focus on understanding concepts, practice regularly, and review weak topics. Would you like specific study tips?"
    elif "study" in message_lower:
        return "Effective study tips: 1) Set a schedule, 2) Take breaks, 3) Practice actively, 4) Review regularly. What subject are you studying?"
    elif "career" in message_lower:
        return "Career guidance: Identify your interests, develop relevant skills, gain experience through internships, and network with professionals. What field interests you?"
    else:
        return "I'm your AI Learning Assistant! I can help with exam preparation, study tips, concept explanations, and career guidance. What would you like to know?"

def generate_exam_ai(subject, chapter, class_level, duration, partA_bloom, partB_bloom, partC_bloom):
    """Generate sample exam"""
    return json.dumps({
        "subject": subject,
        "chapter": chapter,
        "class_level": class_level,
        "duration": duration,
        "total_marks": 49,
        "parts": {
            "Part A - MCQ": {
                "type": "MCQ",
                "marks_per_question": 1,
                "bloom_level": partA_bloom,
                "questions": [
                    {"question": f"What is the main concept of {chapter}?", "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"], "correct": "A", "answer": f"The correct answer is A."}
                ]
            },
            "Part B - Short Answer": {
                "type": "Short Answer",
                "marks_per_question": 2,
                "bloom_level": partB_bloom,
                "questions": [
                    {"question": f"Explain the concept of {chapter}.", "answer": f"This is a model answer explaining the key concepts."}
                ]
            },
            "Part C - Long Answer": {
                "type": "Long Answer",
                "marks_per_question": 5,
                "bloom_level": partC_bloom,
                "questions": [
                    {"question": f"Describe in detail about {chapter}.", "answer": f"This is a detailed model answer."}
                ]
            }
        }
    })

def save_exam_to_db(db, metadata, exam_data, teacher_id):
    total_marks = exam_data.get("total_marks", 49)
    
    exam = Exam(
        exam_id=metadata["exam_id"],
        subject=exam_data.get("subject"),
        chapter=exam_data.get("chapter"),
        class_level=exam_data.get("class_level"),
        duration=exam_data.get("duration"),
        total_marks=total_marks,
        created_by=teacher_id,
        created_at=datetime.fromisoformat(metadata["created_at"]),
        status=metadata["status"],
        exam_data=json.dumps(exam_data)
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    
    parts = exam_data.get("parts", {})
    q_number = 1
    
    for part_name, part_data in parts.items():
        marks_per_q = part_data.get("marks_per_question", 1)
        for q in part_data["questions"]:
            question = Question(
                exam_id=exam.id,
                question_number=q_number,
                question_type=part_data["type"],
                question_text=q["question"],
                max_marks=marks_per_q,
                correct_option=q.get("correct"),
                teacher_final_answer=q.get("answer"),
                bloom_level=part_data.get("bloom_level", "Remember")
            )
            db.add(question)
            db.flush()
            
            if part_data["type"] == "MCQ" and "options" in q:
                for opt in q["options"]:
                    option = Option(
                        question_id=question.id,
                        option_text=opt,
                        is_correct=opt.startswith(q.get("correct", ""))
                    )
                    db.add(option)
            
            q_number += 1
    
    db.commit()
    return exam

def create_notification(db, student_id=None, teacher_id=None, title="", message="", type="", related_id=None):
    if student_id:
        notification = Notification(student_id=student_id, title=title, message=message, type=type, related_id=related_id)
        db.add(notification)
    if teacher_id:
        notification = Notification(teacher_id=teacher_id, title=title, message=message, type=type, related_id=related_id)
        db.add(notification)
    db.commit()

def update_leaderboard(student_id, db):
    submissions = db.query(Submission).filter(Submission.student_id == student_id).all()
    total_score = sum(s.final_total_marks for s in submissions)
    exams_taken = len(submissions)
    avg_score = total_score / exams_taken if exams_taken > 0 else 0
    
    entry = db.query(Leaderboard).filter(Leaderboard.student_id == student_id).first()
    if entry:
        entry.total_score = total_score
        entry.exams_taken = exams_taken
        entry.average_score = avg_score
        entry.updated_at = datetime.utcnow()
    else:
        entry = Leaderboard(student_id=student_id, total_score=total_score, exams_taken=exams_taken, average_score=avg_score)
        db.add(entry)
    db.commit()

def get_leaderboard(db, limit=10):
    entries = db.query(Leaderboard).order_by(Leaderboard.average_score.desc()).limit(limit).all()
    result = []
    for e in entries:
        student = db.query(Student).filter(Student.id == e.student_id).first()
        if student:
            result.append({
                "rank": e.rank,
                "name": student.name,
                "average_score": round(e.average_score, 2),
                "exams_taken": e.exams_taken
            })
    return result

def award_badges(student_id, db):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return
    
    submissions = db.query(Submission).filter(Submission.student_id == student_id).all()
    current_badges = student.badges or []
    current_names = [b.get("name") for b in current_badges]
    
    if len(submissions) >= 1 and "First Exam" not in current_names:
        current_badges.append({"name": "First Exam", "description": "Completed first exam", "icon": "🎓", "earned_at": datetime.utcnow().isoformat()})
    
    student.badges = current_badges
    db.commit()

# ==================================
# FASTAPI APP
# ==================================

app = FastAPI(title="EduEval AI", version="6.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================
# INITIALIZATION
# ==================================

@app.on_event("startup")
def startup_event():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == DEFAULT_ADMIN["username"]).first()
        if not admin:
            print("Creating default admin...")
            admin = Admin(**DEFAULT_ADMIN)
            db.add(admin)
            db.commit()
            print("Admin created successfully!")
        
        for badge in DEFAULT_BADGES:
            existing = db.query(Badge).filter(Badge.name == badge["name"]).first()
            if not existing:
                db.add(Badge(**badge))
        db.commit()
        print("Database initialization complete!")
    except Exception as e:
        print(f"Error during startup: {e}")
    finally:
        db.close()

# ==================================
# HEALTH ENDPOINTS
# ==================================

@app.get("/")
def root():
    return {"message": "EduEval AI API is running", "status": "healthy", "version": "6.0"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ==================================
# ADMIN ENDPOINTS
# ==================================

@app.post("/admin/login")
def admin_login(request: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == request.username, Admin.password == request.password).first()
    return {"success": bool(admin)}

@app.get("/admin/pending-teachers")
def get_pending_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).filter(Teacher.status == "PENDING").all()
    return [{"id": t.id, "name": t.name, "email": t.email, "subject": t.subject} for t in teachers]

@app.get("/admin/approved-teachers")
def get_approved_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).filter(Teacher.status == "APPROVED").all()
    return [{"id": t.id, "name": t.name, "email": t.email, "subject": t.subject} for t in teachers]

@app.post("/admin/approve-teacher")
def approve_teacher(request: TeacherApprove, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id).first()
    if teacher:
        teacher.status = request.status
        teacher.approved_at = datetime.utcnow()
        db.commit()
        return {"success": True}
    return {"success": False}

# ==================================
# TEACHER ENDPOINTS
# ==================================

@app.post("/teacher/register")
def teacher_register(request: TeacherRegister, db: Session = Depends(get_db)):
    existing = db.query(Teacher).filter((Teacher.email == request.email) | (Teacher.teacher_id == request.teacher_id)).first()
    if existing:
        return {"success": False, "message": "Email or Teacher ID already exists"}
    
    teacher = Teacher(**request.dict(), status="PENDING")
    db.add(teacher)
    db.commit()
    return {"success": True, "message": "Registration successful! Waiting for admin approval."}

@app.post("/teacher/login")
def teacher_login(request: TeacherLogin, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == request.email, Teacher.password == request.password).first()
    if not teacher:
        return {"success": False, "message": "Invalid credentials"}
    if teacher.status != "APPROVED":
        return {"success": False, "message": f"Account pending approval"}
    return {"success": True, "teacher_id": teacher.id, "name": teacher.name, "subject": teacher.subject}

@app.post("/teacher/forgot-password")
def teacher_forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == request.email).first()
    if not teacher:
        return {"success": False, "message": "Email not found"}
    token = generate_reset_token()
    teacher.reset_token = token
    teacher.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    return {"success": True, "message": "Reset link sent"}

@app.post("/teacher/reset-password")
def teacher_reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.reset_token == request.token, Teacher.reset_token_expiry > datetime.utcnow()).first()
    if not teacher:
        return {"success": False, "message": "Invalid token"}
    teacher.password = request.new_password
    teacher.reset_token = None
    teacher.reset_token_expiry = None
    db.commit()
    return {"success": True, "message": "Password reset"}

# ==================================
# STUDENT ENDPOINTS
# ==================================

@app.post("/student/register")
def student_register(request: StudentRegister, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.student_id == request.student_id).first()
    if existing:
        return {"success": False, "message": "Student ID already exists"}
    
    student = Student(**request.dict())
    db.add(student)
    db.commit()
    return {"success": True, "message": "Student registered successfully"}

@app.post("/student/login")
def student_login(request: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == request.student_id, Student.password == request.password).first()
    if not student:
        return {"success": False, "message": "Invalid credentials"}
    
    # Update streak
    today = datetime.utcnow().date()
    if student.last_active.date() == today - timedelta(days=1):
        student.streak_days += 1
    elif student.last_active.date() < today - timedelta(days=1):
        student.streak_days = 1
    student.last_active = datetime.utcnow()
    db.commit()
    
    return {"success": True, "student_id": student.id, "name": student.name, "class_level": student.class_level, "streak_days": student.streak_days, "badges": student.badges}

@app.post("/student/forgot-password")
def student_forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == request.email).first()
    if not student:
        return {"success": False, "message": "Email not found"}
    token = generate_reset_token()
    student.reset_token = token
    student.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    return {"success": True, "message": "Reset link sent"}

@app.post("/student/reset-password")
def student_reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.reset_token == request.token, Student.reset_token_expiry > datetime.utcnow()).first()
    if not student:
        return {"success": False, "message": "Invalid token"}
    student.password = request.new_password
    student.reset_token = None
    student.reset_token_expiry = None
    db.commit()
    return {"success": True, "message": "Password reset"}

# ==================================
# CHAT ENDPOINT
# ==================================

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_context = ""
    if request.user_type == "student":
        student = db.query(Student).filter(Student.id == request.user_id).first()
        if student:
            user_context = f"Student in {student.class_level}"
    
    response = get_ai_chat_response(request.message, user_context)
    chat = ChatHistory(user_id=request.user_id, user_type=request.user_type, message=request.message, response=response)
    db.add(chat)
    db.commit()
    return {"response": response}

# ==================================
# EXAM ENDPOINTS
# ==================================

@app.post("/generate-exam")
def create_exam(request: ExamRequest, teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=403, detail="Teacher not found")
    
    result = generate_exam_ai(
        request.subject, request.chapter, request.class_level,
        request.duration, request.partA_bloom, request.partB_bloom, request.partC_bloom
    )
    
    clean_result = result.strip()
    if clean_result.startswith("```"):
        clean_result = clean_result.replace("```json", "").replace("```", "").strip()
    
    try:
        exam_data = json.loads(clean_result)
    except:
        exam_data = json.loads(generate_exam_ai(request.subject, request.chapter, request.class_level,
            request.duration, request.partA_bloom, request.partB_bloom, request.partC_bloom))
    
    exam_id = "EXAM_" + uuid.uuid4().hex[:8].upper()
    metadata = {
        "exam_id": exam_id,
        "class_level": request.class_level,
        "created_at": datetime.utcnow().isoformat(),
        "status": "PUBLISHED" if APP_SETTINGS["AUTO_PUBLISH_EXAMS"] else "DRAFT"
    }
    
    exam = save_exam_to_db(db, metadata, exam_data, teacher_id)
    return {"metadata": metadata, "exam": exam_data, "exam_id": exam.id}

@app.post("/publish-exam/{exam_id}")
def publish_exam(exam_id: int, teacher_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam.status = "PUBLISHED"
    db.commit()
    return {"message": f"Exam {exam.exam_id} published successfully"}

@app.get("/exams")
def get_exams(db: Session = Depends(get_db)):
    exams = db.query(Exam).all()
    return [{"id": e.id, "exam_id": e.exam_id, "subject": e.subject, "chapter": e.chapter, 
             "class_level": e.class_level, "duration": e.duration, "total_marks": e.total_marks, 
             "status": e.status} for e in exams]

# ==================================
# EXAM SUBMISSION ENDPOINTS
# ==================================

@app.post("/submit-exam/{student_id}/{exam_id}")
def submit_exam(student_id: int, exam_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not student or not exam:
        raise HTTPException(status_code=404, detail="Student or Exam not found")
    
    file_path = os.path.join(UPLOAD_FOLDER, f"{student_id}_{exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract text from file (mock for now)
    extracted_text = "Sample answer text"
    
    submission = Submission(
        student_id=student_id,
        exam_id=exam_id,
        uploaded_pdf_path=file_path,
        extracted_text=extracted_text,
        status="UPLOADED"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    total_marks = 0
    
    for q in questions:
        evaluation = get_ai_evaluation(extracted_text, q.teacher_final_answer or "", q.max_marks)
        ai_marks = evaluation.get("marks", 0)
        
        response = StudentResponse(
            submission_id=submission.id,
            student_id=student_id,
            question_id=q.id,
            answer_text=extracted_text,
            ai_is_correct=ai_marks >= q.max_marks * 0.6,
            ai_marks_awarded=ai_marks,
            ai_feedback=evaluation.get("feedback", ""),
            teacher_marks_awarded=ai_marks,
            final_marks=ai_marks,
            evaluated_status="AI_EVALUATED"
        )
        db.add(response)
        total_marks += ai_marks
    
    submission.status = "AI_EVALUATED"
    submission.ai_total_marks = total_marks
    submission.final_total_marks = total_marks
    db.commit()
    
    return {"message": "Exam evaluated", "submission_id": submission.id, "score": total_marks}

@app.get("/student-dashboard/{student_id}")
def student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return {"error": "Student not found"}
    
    submissions = {s.exam_id: s for s in db.query(Submission).filter(Submission.student_id == student_id).all()}
    exams = db.query(Exam).filter(Exam.status == "PUBLISHED", Exam.class_level == student.class_level).all()
    
    result = []
    for e in exams:
        submission = submissions.get(e.id)
        result.append({
            "exam_id": e.id,
            "exam_name": e.exam_id,
            "subject": e.subject,
            "chapter": e.chapter,
            "duration": e.duration,
            "total_marks": e.total_marks,
            "status": submission.status if submission else "NOT_ATTEMPTED",
            "submission_id": submission.id if submission else None,
            "score": submission.final_total_marks if submission else None
        })
    
    completed = [s for s in submissions.values() if s.status in ["AI_EVALUATED", "RESULT_PUBLISHED"]]
    avg_score = sum(s.final_total_marks for s in completed) / len(completed) if completed else 0
    
    return {
        "student": {"id": student.id, "name": student.name, "streak_days": student.streak_days, "badges": student.badges},
        "exams": result,
        "statistics": {"total_exams_taken": len(completed), "average_score": round(avg_score, 2), "total_published_exams": len(exams)}
    }

@app.get("/submission-result/{submission_id}")
def get_submission_result(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    responses = db.query(StudentResponse).filter(StudentResponse.submission_id == submission_id).all()
    
    questions = []
    for r in responses:
        q = db.query(Question).filter(Question.id == r.question_id).first()
        if q:
            questions.append({
                "question_number": q.question_number,
                "question_text": q.question_text,
                "marks_awarded": r.final_marks,
                "max_marks": q.max_marks,
                "ai_feedback": r.ai_feedback
            })
    
    percentage = (submission.final_total_marks / exam.total_marks) * 100 if exam.total_marks else 0
    
    return {
        "exam_name": exam.exam_id,
        "total_marks": submission.final_total_marks,
        "max_marks": exam.total_marks,
        "percentage": round(percentage, 2),
        "questions": questions,
        "risk_level": submission.risk_level
    }

@app.get("/submissions-for-review")
def get_submissions_for_review(db: Session = Depends(get_db)):
    submissions = db.query(Submission).filter(Submission.status.in_(["UPLOADED", "AI_EVALUATED"])).all()
    result = []
    for s in submissions:
        student = db.query(Student).filter(Student.id == s.student_id).first()
        exam = db.query(Exam).filter(Exam.id == s.exam_id).first()
        result.append({
            "id": s.id,
            "student_name": student.name if student else "Unknown",
            "exam_name": exam.exam_id if exam else "Unknown",
            "subject": exam.subject if exam else "Unknown",
            "risk_level": s.risk_level,
            "status": s.status
        })
    return result

@app.get("/submission-review/{submission_id}")
def get_submission_review(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    student = db.query(Student).filter(Student.id == submission.student_id).first()
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    responses = db.query(StudentResponse).filter(StudentResponse.submission_id == submission_id).all()
    
    questions = []
    for r in responses:
        q = db.query(Question).filter(Question.id == r.question_id).first()
        if q:
            questions.append({
                "response_id": r.id,
                "question_number": q.question_number,
                "question_text": q.question_text,
                "student_answer": r.answer_text or "[No answer]",
                "max_marks": q.max_marks,
                "ai_marks": r.ai_marks_awarded,
                "ai_feedback": r.ai_feedback or "No feedback",
                "teacher_marks": r.teacher_marks_awarded,
                "final_marks": r.final_marks
            })
    
    return {
        "submission_id": submission.id,
        "student_name": student.name if student else "Unknown",
        "exam_name": exam.exam_id if exam else "Unknown",
        "subject": exam.subject if exam else "Unknown",
        "status": submission.status,
        "ai_total_marks": submission.ai_total_marks,
        "final_total_marks": submission.final_total_marks,
        "questions": questions
    }

@app.post("/teacher-review/{submission_id}")
def teacher_review(submission_id: int, updates: List[TeacherReviewItem], db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    total_marks = 0
    for item in updates:
        response = db.query(StudentResponse).filter(
            StudentResponse.id == item.response_id,
            StudentResponse.submission_id == submission_id
        ).first()
        if response:
            response.teacher_marks_awarded = item.teacher_marks
            response.teacher_feedback = item.teacher_feedback
            response.teacher_override = item.teacher_override
            response.final_marks = item.teacher_marks
            total_marks += item.teacher_marks
    
    submission.final_total_marks = total_marks
    submission.status = "TEACHER_REVIEWED"
    db.commit()
    
    return {"message": "Review saved", "total_marks": total_marks}

@app.post("/publish-result/{submission_id}")
def publish_result(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.status = "RESULT_PUBLISHED"
    db.commit()
    award_badges(submission.student_id, db)
    update_leaderboard(submission.student_id, db)
    
    return {"message": "Result published"}

@app.get("/leaderboard")
def get_leaderboard_api(db: Session = Depends(get_db)):
    return get_leaderboard(db)

@app.get("/notifications/{user_id}/{user_type}")
def get_notifications(user_id: int, user_type: str, db: Session = Depends(get_db)):
    if user_type == "student":
        notifications = db.query(Notification).filter(Notification.student_id == user_id).order_by(Notification.created_at.desc()).all()
    else:
        notifications = db.query(Notification).filter(Notification.teacher_id == user_id).order_by(Notification.created_at.desc()).all()
    return [{"id": n.id, "title": n.title, "message": n.message, "type": n.type, "is_read": n.is_read, "created_at": n.created_at} for n in notifications]

@app.post("/mark-notification-read/{notification_id}")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.is_read = True
        db.commit()
    return {"success": True}

@app.get("/exam-analytics/{exam_id}")
def exam_analytics(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    submissions = db.query(Submission).filter(Submission.exam_id == exam_id).all()
    scores = [s.final_total_marks for s in submissions if s.final_total_marks]
    
    return {
        "exam_name": exam.exam_id,
        "total_students": len(submissions),
        "average_score": sum(scores) / len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0
    }

@app.post("/career-guidance/{student_id}")
def save_career_guidance(student_id: int, career_interests: str = Form(None), db: Session = Depends(get_db)):
    existing = db.query(CareerGuidance).filter(CareerGuidance.student_id == student_id).first()
    if existing:
        existing.career_interests = career_interests
    else:
        guidance = CareerGuidance(student_id=student_id, career_interests=career_interests)
        db.add(guidance)
    db.commit()
    return {"success": True}

@app.get("/career-guidance/{student_id}")
def get_career_guidance(student_id: int, db: Session = Depends(get_db)):
    guidance = db.query(CareerGuidance).filter(CareerGuidance.student_id == student_id).first()
    if not guidance:
        return {"has_data": False}
    return {"has_data": True, "career_interests": guidance.career_interests, "recommendations": "Explore careers based on your interests!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
