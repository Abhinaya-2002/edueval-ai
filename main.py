# main.py - Complete Backend with All Features
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON, Date, func
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
import re
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
from difflib import SequenceMatcher
import zipfile
from collections import Counter
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO

# Configure pytesseract
try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except:
    pass

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==================================
# DATABASE SETUP
# ==================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./edueval.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    subject = Column(String)
    institution_type = Column(String, default="school")
    class_level = Column(String)
    section = Column(String, nullable=True)
    program = Column(String, nullable=True)
    total_marks = Column(Integer, default=0)
    deadline = Column(DateTime)
    reference_materials = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("teachers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE")
    teacher = relationship("Teacher")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    file_path = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    marks_awarded = Column(Integer, default=0)
    ai_feedback = Column(Text, nullable=True)
    teacher_feedback = Column(Text, nullable=True)
    instant_feedback = Column(Text, nullable=True)
    plagiarism_score = Column(Float, default=0.0)
    status = Column(String, default="SUBMITTED")
    assignment = relationship("Assignment")
    student = relationship("Student")

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
    subject_wise_insights = Column(JSON, default={})
    mistake_analysis = Column(JSON, default={})
    weak_topics = Column(JSON, default=[])
    learning_path = Column(JSON, default={})
    grading_mode = Column(String, default="STRICT")
    risk_level = Column(String, default="LOW")
    risk_factors = Column(JSON, default=[])
    status = Column(String, default="UPLOADED")
    retake_count = Column(Integer, default=0)
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
    mistake_type = Column(String, nullable=True)
    teacher_marks_awarded = Column(Integer, default=0)
    teacher_feedback = Column(Text, nullable=True)
    teacher_override = Column(Boolean, default=False)
    final_marks = Column(Integer, default=0)
    evaluated_status = Column(String, default="PENDING")
    submission = relationship("Submission")
    student = relationship("Student")
    question = relationship("Question")

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic = Column(String)
    video_url = Column(String)
    video_title = Column(String)
    difficulty_level = Column(String, default="Beginner")
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")

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

class PracticeTest(Base):
    __tablename__ = "practice_tests"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic = Column(String)
    questions = Column(JSON, default=[])
    score = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")

class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    icon = Column(String)
    criteria = Column(String)

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

class AssignmentRequest(BaseModel):
    title: str
    description: str
    subject: str
    institution_type: str
    class_level: str
    section: Optional[str] = None
    program: Optional[str] = None
    total_marks: int
    deadline: str
    reference_materials: Optional[str] = None

class TeacherReviewItem(BaseModel):
    response_id: int
    teacher_marks: int
    teacher_feedback: Optional[str] = None
    teacher_override: bool = True

class RetakeExamRequest(BaseModel):
    submission_id: int

# ==================================
# APPLICATION SETTINGS
# ==================================

APP_SETTINGS = {
    "AUTO_GRADING_AFTER_SUBMISSION": True,
    "AUTO_PUBLISH_EXAMS": False,
    "MIN_ASSIGNMENT_MARKS": 5,
    "MAX_RETAKE_ATTEMPTS": 3
}

UPLOAD_FOLDER = "uploads"
ASSIGNMENT_FOLDER = "assignments"
BULK_UPLOAD_FOLDER = "bulk_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ASSIGNMENT_FOLDER, exist_ok=True)
os.makedirs(BULK_UPLOAD_FOLDER, exist_ok=True)

DEFAULT_ADMIN = {
    "admin_id": "ADMIN001",
    "username": "admin",
    "password": "admin123",
    "email": "admin@edueval.com"
}

DEFAULT_BADGES = [
    {"name": "First Exam", "description": "Completed your first exam", "icon": "🎓", "criteria": "first_exam"},
    {"name": "Perfect Score", "description": "Scored 100% in an exam", "icon": "⭐", "criteria": "perfect_score"},
    {"name": "Consistent Learner", "description": "7-day learning streak", "icon": "🔥", "criteria": "streak_7"},
    {"name": "Quick Learner", "description": "Improved score by 20%", "icon": "📈", "criteria": "improvement_20"},
    {"name": "Assignment Master", "description": "Submitted 5 assignments", "icon": "📝", "criteria": "assignments_5"},
    {"name": "Top Performer", "description": "Ranked in top 3 on leaderboard", "icon": "🏆", "criteria": "top_3"},
]

# ==================================
# HELPER FUNCTIONS
# ==================================

def preprocess_image_for_ocr(image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised = cv2.medianBlur(thresh, 3)
        _, buffer = cv2.imencode('.png', denoised)
        return buffer.tobytes()
    except:
        return image_bytes

def extract_text_from_image(file_path):
    try:
        if file_path.lower().endswith('.pdf'):
            images = convert_from_path(file_path, first_page=1, last_page=1)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)
            return text
        else:
            img = cv2.imread(file_path)
            text = pytesseract.image_to_string(img)
            return text
    except:
        return ""

def extract_text_from_file(file_path):
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_path)
    elif file_path.lower().endswith('.pdf'):
        try:
            images = convert_from_path(file_path)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)
            return text
        except:
            return ""
    return ""

def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def send_reset_email(email, token, user_type):
    print(f"Reset link for {email}: http://localhost:8000/reset-password?token={token}&type={user_type}")
    return True

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def check_plagiarism(answer_text, db, exam_id, student_id):
    other_submissions = db.query(Submission).filter(
        Submission.exam_id == exam_id,
        Submission.student_id != student_id
    ).all()
    max_similarity = 0
    for sub in other_submissions:
        responses = db.query(StudentResponse).filter(StudentResponse.submission_id == sub.id).all()
        for resp in responses:
            if resp.answer_text:
                similarity = calculate_similarity(answer_text, resp.answer_text)
                max_similarity = max(max_similarity, similarity)
    return max_similarity

def analyze_mistakes(student_answer, correct_answer):
    mistakes = []
    if not student_answer or student_answer.strip() == "":
        mistakes.append("No answer provided")
        return mistakes
    
    student_lower = student_answer.lower()
    correct_lower = correct_answer.lower()
    
    key_concepts = extract_key_concepts(correct_answer)
    missing_concepts = [c for c in key_concepts if c not in student_lower]
    if missing_concepts:
        mistakes.append(f"Missing key concepts: {', '.join(missing_concepts[:3])}")
    
    formulas = extract_formulas(correct_answer)
    missing_formulas = [f for f in formulas if f not in student_lower]
    if missing_formulas:
        mistakes.append(f"Missing formulas: {', '.join(missing_formulas[:2])}")
    
    if len(student_answer) < len(correct_answer) * 0.5:
        mistakes.append("Answer is incomplete")
    
    return mistakes if mistakes else ["Minor improvements needed"]

def extract_key_concepts(text):
    common_concepts = ['definition', 'principle', 'theory', 'concept', 'law', 'formula', 'explain', 'describe']
    return [c for c in common_concepts if c in text.lower()]

def extract_formulas(text):
    import re
    formula_pattern = r'[A-Za-z]\s*=\s*[A-Za-z0-9\+\-\*\/\(\)\s]+'
    return re.findall(formula_pattern, text)

def generate_learning_path(weak_topics, student_score):
    learning_path = {
        "daily_plan": [], "resources": [], "estimated_days": 0,
        "intensity": "Medium", "recommended_hours": 2
    }
    if not weak_topics:
        return learning_path
    
    days = []
    for i, topic in enumerate(weak_topics[:5]):
        days.append({
            "day": i + 1, "topic": topic,
            "activities": [
                f"📖 Read about {topic}",
                f"🎥 Watch video tutorial on {topic}",
                f"✍️ Practice 5 questions on {topic}",
                f"📝 Take a mini-test on {topic}"
            ]
        })
        learning_path["resources"].append({
            "topic": topic,
            "video": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial",
            "practice": f"Practice questions on {topic}"
        })
    
    learning_path["daily_plan"] = days
    learning_path["estimated_days"] = len(weak_topics[:5])
    
    if student_score < 40:
        learning_path["intensity"] = "High"
        learning_path["recommended_hours"] = 3
    elif student_score < 60:
        learning_path["intensity"] = "Medium"
        learning_path["recommended_hours"] = 2
    else:
        learning_path["intensity"] = "Low"
        learning_path["recommended_hours"] = 1
    
    return learning_path

def generate_practice_test(topic, num_questions=5):
    try:
        prompt = f"""
        Generate {num_questions} practice questions on the topic: {topic}
        Return in JSON format: {{"topic": "{topic}", "questions": [{{"question": "text", "options": ["A) Opt1", "B) Opt2", "C) Opt3", "D) Opt4"], "correct": "A", "explanation": "why"}}]}}
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
        return {"topic": topic, "questions": [{"question": f"Sample question on {topic}", "options": ["A) Option1", "B) Option2", "C) Option3", "D) Option4"], "correct": "A", "explanation": "Explanation"}]}

def generate_smart_report_card(submission_id, db):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        return None
    
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    student = db.query(Student).filter(Student.id == submission.student_id).first()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, alignment=1, spaceAfter=20)
    elements.append(Paragraph("Smart Report Card", title_style))
    elements.append(Spacer(1, 10))
    
    percentage = (submission.final_total_marks / exam.total_marks * 100) if exam and exam.total_marks else 0
    info_data = [
        ["Student Name", student.name if student else "N/A"],
        ["Student ID", student.student_id if student else "N/A"],
        ["Exam", exam.exam_id if exam else "N/A"],
        ["Subject", exam.subject if exam else "N/A"],
        ["Total Marks", f"{submission.final_total_marks}/{exam.total_marks if exam else 100}"],
        ["Percentage", f"{percentage:.1f}%"],
        ["Risk Level", submission.risk_level],
    ]
    table = Table(info_data, colWidths=[150, 300])
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)]))
    elements.append(table)
    elements.append(Spacer(1, 15))
    
    if submission.ai_feedback_summary:
        elements.append(Paragraph("AI Feedback", styles["Heading2"]))
        elements.append(Paragraph(submission.ai_feedback_summary, styles["Normal"]))
        elements.append(Spacer(1, 10))
    
    if submission.weak_topics:
        elements.append(Paragraph("Weak Topics", styles["Heading2"]))
        for topic in submission.weak_topics[:5]:
            elements.append(Paragraph(f"• {topic}", styles["Normal"]))
        elements.append(Spacer(1, 10))
    
    if submission.learning_path:
        lp = submission.learning_path
        elements.append(Paragraph("Improvement Plan", styles["Heading2"]))
        elements.append(Paragraph(f"Intensity: {lp.get('intensity', 'Medium')} | Hours: {lp.get('recommended_hours', 2)}/day", styles["Normal"]))
        for day in lp.get('daily_plan', [])[:3]:
            elements.append(Paragraph(f"Day {day['day']}: {day['topic']}", styles["Heading3"]))
            for activity in day['activities'][:2]:
                elements.append(Paragraph(f"  • {activity}", styles["Normal"]))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def award_badges(student_id, db):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return
    
    submissions = db.query(Submission).filter(Submission.student_id == student_id).all()
    assignments = db.query(AssignmentSubmission).filter(AssignmentSubmission.student_id == student_id).all()
    current_badges = student.badges or []
    current_names = [b.get("name") for b in current_badges]
    
    if len(submissions) >= 1 and "First Exam" not in current_names:
        current_badges.append({"name": "First Exam", "description": "Completed your first exam", "icon": "🎓", "earned_at": datetime.utcnow().isoformat()})
    
    for s in submissions:
        exam = db.query(Exam).filter(Exam.id == s.exam_id).first()
        if exam and s.final_total_marks == exam.total_marks and "Perfect Score" not in current_names:
            current_badges.append({"name": "Perfect Score", "description": "Scored 100% in an exam", "icon": "⭐", "earned_at": datetime.utcnow().isoformat()})
            break
    
    if student.streak_days >= 7 and "Consistent Learner" not in current_names:
        current_badges.append({"name": "Consistent Learner", "description": "7-day learning streak", "icon": "🔥", "earned_at": datetime.utcnow().isoformat()})
    
    if len(assignments) >= 5 and "Assignment Master" not in current_names:
        current_badges.append({"name": "Assignment Master", "description": "Submitted 5 assignments", "icon": "📝", "earned_at": datetime.utcnow().isoformat()})
    
    student.badges = current_badges
    db.commit()
    update_leaderboard(student_id, db)

def update_leaderboard(student_id, db):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return
    
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
    
    all_entries = db.query(Leaderboard).order_by(Leaderboard.average_score.desc()).all()
    for idx, e in enumerate(all_entries):
        e.rank = idx + 1
    db.commit()
    
    if entry.rank <= 3:
        badges = student.badges or []
        if "Top Performer" not in [b.get("name") for b in badges]:
            badges.append({"name": "Top Performer", "description": "Ranked in top 3 on leaderboard", "icon": "🏆", "earned_at": datetime.utcnow().isoformat()})
            student.badges = badges
            db.commit()

def get_leaderboard(db, limit=10):
    entries = db.query(Leaderboard).order_by(Leaderboard.average_score.desc()).limit(limit).all()
    result = []
    for entry in entries:
        student = db.query(Student).filter(Student.id == entry.student_id).first()
        if student:
            result.append({
                "rank": entry.rank, "student_id": student.student_id, "name": student.name,
                "total_score": entry.total_score, "exams_taken": entry.exams_taken,
                "average_score": round(entry.average_score, 2), "badges": student.badges or []
            })
    return result

def get_ai_chat_response_with_context(message, student_id, db):
    student = db.query(Student).filter(Student.id == student_id).first()
    context = ""
    weak_topics = []
    if student:
        submissions = db.query(Submission).filter(Submission.student_id == student_id).order_by(Submission.created_at.desc()).limit(3).all()
        for s in submissions:
            if s.weak_topics:
                weak_topics.extend(s.weak_topics[:3])
        weak_topics = list(set(weak_topics))
        if weak_topics:
            context = f"Student's weak topics: {', '.join(weak_topics[:3])}. "
        context += f"Student is in {student.class_level} class."
    
    system_prompt = f"""You are EduEval AI Assistant. Context: {context}. Provide personalized help based on weak areas."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
            temperature=0.7, max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return f"I'm here to help! Focus on practicing {', '.join(weak_topics[:2]) if weak_topics else 'key concepts'}."

def get_ai_evaluation(student_answer, correct_answer, max_marks):
    try:
        prompt = f"""
        Evaluate student answer vs correct answer.
        Correct: {correct_answer}
        Student: {student_answer}
        Max Marks: {max_marks}
        Return JSON: {{"marks": number, "feedback": "text", "mistakes": ["list"], "correctness": "percentage"}}
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5, max_tokens=400
        )
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
        similarity = calculate_similarity(student_answer, correct_answer)
        marks = int(similarity * max_marks)
        return {"marks": marks, "feedback": f"Matches {similarity*100:.0f}%", "mistakes": ["Review key points"], "correctness": f"{similarity*100:.0f}"}

def generate_exam_ai(subject, chapter, class_level, duration, partA_bloom, partB_bloom, partC_bloom):
    try:
        prompt = f"""
        Generate exam for {subject} - {chapter} for {class_level}. Duration: {duration}
        Part A: 10 MCQ at {partA_bloom} (1 mark)
        Part B: 7 Short Answer at {partB_bloom} (2 marks)
        Part C: 5 Long Answer at {partC_bloom} (5 marks)
        Return JSON: {{"subject":"{subject}","chapter":"{chapter}","class_level":"{class_level}","duration":"{duration}","total_marks":49,"parts":{{"Part A - MCQ":{{"type":"MCQ","marks_per_question":1,"bloom_level":"{partA_bloom}","questions":[{{"question":"text","options":["A)","B)","C)","D)"],"correct":"A","answer":"explanation"}}]}},"Part B - Short Answer":{{"type":"Short Answer","marks_per_question":2,"bloom_level":"{partB_bloom}","questions":[{{"question":"text","answer":"model"}}]}},"Part C - Long Answer":{{"type":"Long Answer","marks_per_question":5,"bloom_level":"{partC_bloom}","questions":[{{"question":"text","answer":"detailed"}}]}}}}}}
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=2000
        )
        return response.choices[0].message.content
    except:
        return json.dumps({
            "subject": subject, "chapter": chapter, "class_level": class_level, "duration": duration, "total_marks": 49,
            "parts": {
                "Part A - MCQ": {"type": "MCQ", "marks_per_question": 1, "bloom_level": partA_bloom,
                    "questions": [{"question": f"Sample MCQ", "options": ["A) Opt1", "B) Opt2", "C) Opt3", "D) Opt4"], "correct": "A", "answer": "Explanation"}]},
                "Part B - Short Answer": {"type": "Short Answer", "marks_per_question": 2, "bloom_level": partB_bloom,
                    "questions": [{"question": f"Explain {chapter}.", "answer": "Model answer"}]},
                "Part C - Long Answer": {"type": "Long Answer", "marks_per_question": 5, "bloom_level": partC_bloom,
                    "questions": [{"question": f"Describe {chapter}.", "answer": "Detailed answer"}]}
            }
        })

def save_exam_to_db(db, metadata, exam_data, teacher_id):
    total_marks = exam_data.get("total_marks", 49)
    exam = Exam(
        exam_id=metadata["exam_id"], subject=exam_data.get("subject"), chapter=exam_data.get("chapter"),
        institution_type=metadata.get("institution_type", "school"), class_level=exam_data.get("class_level"),
        section=metadata.get("section"), program=metadata.get("program"), duration=exam_data.get("duration"),
        total_marks=total_marks, created_by=teacher_id, created_at=datetime.fromisoformat(metadata["created_at"]),
        exam_date=datetime.strptime(metadata["exam_date"], "%Y-%m-%d").date() if metadata.get("exam_date") else None,
        status=metadata["status"], exam_data=json.dumps(exam_data),
        bloom_levels={"partA": exam_data.get("parts", {}).get("Part A - MCQ", {}).get("bloom_level", ""),
                      "partB": exam_data.get("parts", {}).get("Part B - Short Answer", {}).get("bloom_level", ""),
                      "partC": exam_data.get("parts", {}).get("Part C - Long Answer", {}).get("bloom_level", "")}
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
                exam_id=exam.id, question_number=q_number, question_type=part_data["type"],
                question_text=q["question"], max_marks=marks_per_q, correct_option=q.get("correct"),
                teacher_final_answer=q.get("answer"), bloom_level=part_data.get("bloom_level", "Remember")
            )
            db.add(question)
            db.flush()
            if part_data["type"] == "MCQ" and "options" in q:
                for opt in q["options"]:
                    option = Option(question_id=question.id, option_text=opt, is_correct=opt.startswith(q.get("correct", "")))
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

def generate_youtube_recommendations(topic, max_results=2):
    search_query = topic.replace(" ", "+")
    return [
        {"title": f"Learn {topic} - Tutorial", "url": f"https://www.youtube.com/results?search_query={search_query}+tutorial", "duration": "10-15 mins", "difficulty": "Beginner"},
        {"title": f"{topic} - Advanced", "url": f"https://www.youtube.com/results?search_query={search_query}+advanced", "duration": "15-20 mins", "difficulty": "Intermediate"}
    ][:max_results]

# ==================================
# FASTAPI APP
# ==================================

app = FastAPI(title="EduEval AI", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    admin = db.query(Admin).filter(Admin.username == DEFAULT_ADMIN["username"]).first()
    if not admin:
        admin = Admin(**DEFAULT_ADMIN)
        db.add(admin)
        db.commit()
    for badge in DEFAULT_BADGES:
        if not db.query(Badge).filter(Badge.name == badge["name"]).first():
            db.add(Badge(**badge))
    db.commit()
    db.close()

# ==================================
# ADMIN ENDPOINTS
# ==================================

@app.post("/admin/login")
def admin_login(request: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == request.username, Admin.password == request.password).first()
    return {"success": bool(admin), "message": "Login successful" if admin else "Invalid credentials"}

@app.get("/admin/pending-teachers")
def get_pending_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).filter(Teacher.status == "PENDING").all()
    return [{"id": t.id, "teacher_id": t.teacher_id, "name": t.name, "email": t.email, "subject": t.subject, "qualification": t.qualification, "experience": t.experience} for t in teachers]

@app.get("/admin/approved-teachers")
def get_approved_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).filter(Teacher.status == "APPROVED").all()
    return [{"id": t.id, "name": t.name, "email": t.email, "subject": t.subject} for t in teachers]

@app.post("/admin/approve-teacher")
def approve_teacher(request: TeacherApprove, admin_id: int = 1, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id).first()
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    teacher.status = request.status
    teacher.approved_by = admin_id
    teacher.approved_at = datetime.utcnow()
    db.commit()
    create_notification(db, teacher_id=teacher.id, title="Application Status", message=f"Your application has been {request.status}!", type="TEACHER_STATUS")
    return {"success": True, "message": f"Teacher {request.status}"}

# ==================================
# TEACHER ENDPOINTS
# ==================================

@app.post("/teacher/register")
def teacher_register(request: TeacherRegister, db: Session = Depends(get_db)):
    if db.query(Teacher).filter((Teacher.email == request.email) | (Teacher.teacher_id == request.teacher_id)).first():
        return {"success": False, "message": "Email or Teacher ID exists"}
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
        return {"success": False, "message": f"Account status: {teacher.status}"}
    return {"success": True, "teacher_id": teacher.id, "name": teacher.name, "email": teacher.email, "subject": teacher.subject}

@app.post("/teacher/forgot-password")
def teacher_forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == request.email).first()
    if not teacher:
        return {"success": False, "message": "Email not found"}
    token = generate_reset_token()
    teacher.reset_token = token
    teacher.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    send_reset_email(request.email, token, "teacher")
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
    if db.query(Student).filter(Student.student_id == request.student_id).first():
        return {"success": False, "message": "Student ID exists"}
    student = Student(**request.dict())
    db.add(student)
    db.commit()
    return {"success": True, "message": "Registration successful"}

@app.post("/student/login")
def student_login(request: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == request.student_id, Student.password == request.password).first()
    if not student:
        return {"success": False, "message": "Invalid credentials"}
    today = datetime.utcnow().date()
    if student.last_active.date() == today - timedelta(days=1):
        student.streak_days += 1
    elif student.last_active.date() < today - timedelta(days=1):
        student.streak_days = 1
    student.last_active = datetime.utcnow()
    db.commit()
    award_badges(student.id, db)
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
    send_reset_email(request.email, token, "student")
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

@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    return [{"id": s.id, "student_id": s.student_id, "name": s.name, "class_level": s.class_level} for s in db.query(Student).all()]

@app.get("/leaderboard")
def get_leaderboard_api(limit: int = 10, db: Session = Depends(get_db)):
    return get_leaderboard(db, limit)

@app.get("/student-badges/{student_id}")
def get_student_badges(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    return {"badges": student.badges or []} if student else {"badges": []}

# ==================================
# CHATBOT ENDPOINT
# ==================================

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if request.user_type == "student":
        response_text = get_ai_chat_response_with_context(request.message, request.user_id, db)
    else:
        response_text = get_ai_chat_response_with_context(request.message, 0, db)
    chat = ChatHistory(user_id=request.user_id, user_type=request.user_type, message=request.message, response=response_text)
    db.add(chat)
    db.commit()
    return {"response": response_text}

@app.get("/chat-history/{user_id}/{user_type}")
def get_chat_history(user_id: int, user_type: str, db: Session = Depends(get_db)):
    history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id, ChatHistory.user_type == user_type).order_by(ChatHistory.created_at.desc()).limit(50).all()
    return [{"message": h.message, "response": h.response, "created_at": h.created_at} for h in reversed(history)]

# ==================================
# EXAM ENDPOINTS
# ==================================

@app.post("/generate-exam")
def create_exam(request: ExamRequest, teacher_id: int, db: Session = Depends(get_db)):
    result = generate_exam_ai(request.subject, request.chapter, request.class_level, request.duration, request.partA_bloom, request.partB_bloom, request.partC_bloom)
    clean = result.strip()
    if clean.startswith("```"):
        clean = clean.replace("```json", "").replace("```", "").strip()
    exam_data = json.loads(clean)
    exam_id = "EXAM_" + uuid.uuid4().hex[:8].upper()
    metadata = {
        "exam_id": exam_id, "institution_type": request.institution_type, "class_level": request.class_level,
        "section": request.section, "program": request.program, "exam_date": request.exam_date,
        "created_at": datetime.utcnow().isoformat(), "status": "PUBLISHED" if APP_SETTINGS["AUTO_PUBLISH_EXAMS"] else "DRAFT"
    }
    exam = save_exam_to_db(db, metadata, exam_data, teacher_id)
    return {"metadata": metadata, "exam": exam_data, "exam_id": exam.id}

@app.post("/publish-exam/{exam_id}")
def publish_exam(exam_id: int, teacher_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(404, "Exam not found")
    exam.status = "PUBLISHED"
    db.commit()
    students = db.query(Student).filter(Student.class_level == exam.class_level)
    if exam.section:
        students = students.filter(Student.section == exam.section)
    for s in students.all():
        create_notification(db, student_id=s.id, title=f"New Exam: {exam.exam_id}", message=f"Exam on {exam.subject} - {exam.chapter} published", type="EXAM", related_id=exam.id)
    return {"message": f"Exam {exam.exam_id} published"}

@app.get("/exams")
def get_exams(db: Session = Depends(get_db)):
    return [{"id": e.id, "exam_id": e.exam_id, "subject": e.subject, "chapter": e.chapter, "class_level": e.class_level, "duration": e.duration, "total_marks": e.total_marks, "status": e.status} for e in db.query(Exam).all()]

@app.get("/published-exams")
def get_published_exams(db: Session = Depends(get_db)):
    return [{"id": e.id, "exam_id": e.exam_id, "subject": e.subject, "chapter": e.chapter, "class_level": e.class_level, "duration": e.duration, "total_marks": e.total_marks} for e in db.query(Exam).filter(Exam.status == "PUBLISHED").all()]

# ==================================
# ASSIGNMENT ENDPOINTS
# ==================================

@app.post("/create-assignment")
def create_assignment(request: AssignmentRequest, teacher_id: int, db: Session = Depends(get_db)):
    if request.total_marks < 5:
        raise HTTPException(400, "Assignment total marks must be at least 5")
    assignment_id = "ASSIGN_" + uuid.uuid4().hex[:8].upper()
    deadline_dt = datetime.fromisoformat(request.deadline)
    assignment = Assignment(
        assignment_id=assignment_id, title=request.title, description=request.description, subject=request.subject,
        institution_type=request.institution_type, class_level=request.class_level, section=request.section,
        program=request.program, total_marks=request.total_marks, deadline=deadline_dt,
        reference_materials=request.reference_materials, created_by=teacher_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    students = db.query(Student).filter(Student.class_level == request.class_level)
    if request.section:
        students = students.filter(Student.section == request.section)
    for s in students.all():
        create_notification(db, student_id=s.id, title=f"New Assignment: {request.title}", message=f"Assignment on {request.subject} due {deadline_dt.strftime('%Y-%m-%d %H:%M')}", type="ASSIGNMENT", related_id=assignment.id)
    return {"success": True, "assignment_id": assignment.id}

@app.get("/assignments")
def get_assignments(db: Session = Depends(get_db)):
    return [{"id": a.id, "title": a.title, "subject": a.subject, "class_level": a.class_level, "total_marks": a.total_marks, "deadline": a.deadline, "status": a.status} for a in db.query(Assignment).all()]

@app.get("/student-assignments/{student_id}")
def get_student_assignments(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, "Student not found")
    assignments = db.query(Assignment).filter(Assignment.class_level == student.class_level, Assignment.status == "ACTIVE")
    if student.section:
        assignments = assignments.filter(Assignment.section == student.section)
    submissions = {s.assignment_id: s for s in db.query(AssignmentSubmission).filter(AssignmentSubmission.student_id == student_id).all()}
    return [{
        "id": a.id, "title": a.title, "subject": a.subject, "total_marks": a.total_marks,
        "deadline": a.deadline, "reference_materials": a.reference_materials,
        "status": "SUBMITTED" if a.id in submissions else "PENDING",
        "submission_id": submissions[a.id].id if a.id in submissions else None,
        "marks_awarded": submissions[a.id].marks_awarded if a.id in submissions else None
    } for a in assignments.all()]

@app.post("/submit-assignment/{student_id}/{assignment_id}")
def submit_assignment(student_id: int, assignment_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not student or not assignment:
        raise HTTPException(404, "Not found")
    file_path = os.path.join(ASSIGNMENT_FOLDER, f"{student_id}_{assignment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    extracted = extract_text_from_file(file_path)
    instant_feedback = get_ai_evaluation(extracted, assignment.description or "", assignment.total_marks)
    submission = AssignmentSubmission(assignment_id=assignment_id, student_id=student_id, file_path=file_path, instant_feedback=instant_feedback.get("feedback", "Good attempt!"), status="SUBMITTED")
    db.add(submission)
    db.commit()
    award_badges(student_id, db)
    return {"message": "Assignment submitted", "submission_id": submission.id, "instant_feedback": instant_feedback.get("feedback", "Good attempt!")}

@app.post("/evaluate-assignment/{submission_id}")
def evaluate_assignment(submission_id: int, marks: int, feedback: str = None, db: Session = Depends(get_db)):
    submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    submission.marks_awarded = marks
    submission.teacher_feedback = feedback
    submission.status = "EVALUATED"
    db.commit()
    create_notification(db, student_id=submission.student_id, title="Assignment Evaluated", message=f"Score: {marks}", type="RESULT", related_id=submission_id)
    award_badges(submission.student_id, db)
    return {"message": "Assignment evaluated"}

# ==================================
# EXAM SUBMISSION ENDPOINTS
# ==================================

@app.post("/submit-exam/{student_id}/{exam_id}")
def submit_exam(student_id: int, exam_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not student or not exam:
        raise HTTPException(404, "Not found")
    existing = db.query(Submission).filter(Submission.student_id == student_id, Submission.exam_id == exam_id).count()
    if existing >= APP_SETTINGS["MAX_RETAKE_ATTEMPTS"]:
        raise HTTPException(400, f"Max retake attempts ({APP_SETTINGS['MAX_RETAKE_ATTEMPTS']}) reached")
    
    file_path = os.path.join(UPLOAD_FOLDER, f"{student_id}_{exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    extracted = extract_text_from_file(file_path)
    submission = Submission(student_id=student_id, exam_id=exam_id, uploaded_pdf_path=file_path, extracted_text=extracted, status="UPLOADED", retake_count=existing)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    total_marks = 0
    weak_topics = []
    all_mistakes = []
    
    for q in questions:
        eval_result = get_ai_evaluation(extracted or "", q.teacher_final_answer or "", q.max_marks)
        ai_marks = eval_result.get("marks", 0)
        mistakes = analyze_mistakes(extracted or "", q.teacher_final_answer or "")
        response = StudentResponse(
            submission_id=submission.id, student_id=student_id, question_id=q.id, answer_text=extracted,
            ai_is_correct=ai_marks >= q.max_marks * 0.6, ai_marks_awarded=ai_marks, ai_feedback=eval_result.get("feedback", ""),
            mistake_type=", ".join(mistakes), teacher_marks_awarded=ai_marks, final_marks=ai_marks, evaluated_status="AI_EVALUATED"
        )
        db.add(response)
        total_marks += ai_marks
        all_mistakes.extend(mistakes)
        if ai_marks < q.max_marks * 0.5:
            weak_topics.append(q.question_text[:50])
    
    percentage = (total_marks / exam.total_marks) * 100 if exam.total_marks else 0
    submission.status = "AI_EVALUATED"
    submission.ai_total_marks = total_marks
    submission.final_total_marks = total_marks
    submission.weak_topics = list(set(weak_topics[:5]))
    submission.mistake_analysis = {"mistakes": list(set(all_mistakes[:5]))}
    submission.ai_feedback_summary = "Excellent!" if percentage >= 80 else "Good!" if percentage >= 60 else "Satisfactory" if percentage >= 40 else "Needs improvement"
    submission.learning_path = generate_learning_path(submission.weak_topics, percentage)
    
    risk_factors = []
    risk_score = 0
    if percentage < 35:
        risk_factors.append("Critical: Score below 35%")
        risk_score += 40
    elif percentage < 50:
        risk_factors.append("High Risk: Score below 50%")
        risk_score += 30
    elif percentage < 60:
        risk_factors.append("Moderate Risk: Score below 60%")
        risk_score += 20
    submission.risk_level = "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 25 else "LOW"
    submission.risk_factors = risk_factors
    
    db.commit()
    award_badges(student_id, db)
    update_leaderboard(student_id, db)
    create_notification(db, student_id=student_id, title="Exam Evaluated", message=f"Score: {total_marks}/{exam.total_marks}", type="EXAM_RESULT", related_id=submission.id)
    
    return {"message": "Exam evaluated", "submission_id": submission.id, "score": total_marks, "percentage": percentage}

@app.get("/student-dashboard/{student_id}")
def student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return {"error": "Student not found"}
    submissions = {s.exam_id: s for s in db.query(Submission).filter(Submission.student_id == student_id).all()}
    exams = db.query(Exam).filter(Exam.status == "PUBLISHED", Exam.class_level == student.class_level).all()
    if student.section:
        exams = [e for e in exams if e.section is None or e.section == student.section]
    
    result = []
    for e in exams:
        s = submissions.get(e.id)
        result.append({
            "exam_id": e.id, "exam_name": e.exam_id, "subject": e.subject, "chapter": e.chapter,
            "duration": e.duration, "total_marks": e.total_marks,
            "status": s.status if s else "NOT_ATTEMPTED",
            "submission_id": s.id if s else None, "score": s.final_total_marks if s else None,
            "percentage": round((s.final_total_marks / e.total_marks) * 100, 1) if s and e.total_marks else None
        })
    
    completed = [s for s in db.query(Submission).filter(Submission.student_id == student_id, Submission.status.in_(["AI_EVALUATED", "RESULT_PUBLISHED"])).all()]
    avg_score = sum(s.final_total_marks for s in completed) / len(completed) if completed else 0
    
    return {
        "student": {"id": student.id, "name": student.name, "student_id": student.student_id, "class_level": student.class_level, "streak_days": student.streak_days, "badges": student.badges},
        "exams": result,
        "statistics": {"total_exams_taken": len(completed), "average_score": round(avg_score, 2), "total_published_exams": len(exams)}
    }

@app.get("/submission-result/{submission_id}")
def get_submission_result(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    responses = db.query(StudentResponse).filter(StudentResponse.submission_id == submission_id).all()
    
    questions_data = []
    weak_topics = []
    for r in responses:
        q = db.query(Question).filter(Question.id == r.question_id).first()
        if q:
            percentage = (r.final_marks / q.max_marks) * 100 if q.max_marks else 0
            if percentage < 50:
                weak_topics.append(q.question_text[:80])
            questions_data.append({
                "question_number": q.question_number, "question_text": q.question_text,
                "student_answer": r.answer_text, "correct_answer": q.teacher_final_answer,
                "marks_awarded": r.final_marks, "max_marks": q.max_marks, "percentage": round(percentage, 1),
                "ai_feedback": r.ai_feedback, "teacher_feedback": r.teacher_feedback
            })
    
    percentage = (submission.final_total_marks / exam.total_marks) * 100 if exam.total_marks else 0
    youtube_recs = []
    for topic in weak_topics[:3]:
        youtube_recs.extend(generate_youtube_recommendations(topic, 1))
    
    return {
        "exam_name": exam.exam_id, "subject": exam.subject, "chapter": exam.chapter,
        "total_marks": submission.final_total_marks, "max_marks": exam.total_marks,
        "percentage": round(percentage, 2), "questions": questions_data,
        "weak_topics": list(set(weak_topics)), "risk_level": submission.risk_level,
        "risk_factors": submission.risk_factors, "ai_feedback_summary": submission.ai_feedback_summary,
        "improvement_suggestions": submission.improvement_suggestions,
        "learning_path": submission.learning_path, "youtube_recommendations": youtube_recs
    }

@app.get("/submissions-for-review")
def get_submissions_for_review(db: Session = Depends(get_db)):
    submissions = db.query(Submission).filter(Submission.status.in_(["UPLOADED", "AI_EVALUATED"])).all()
    result = []
    for s in submissions:
        student = db.query(Student).filter(Student.id == s.student_id).first()
        exam = db.query(Exam).filter(Exam.id == s.exam_id).first()
        result.append({
            "id": s.id, "student_name": student.name if student else "Unknown",
            "exam_name": exam.exam_id if exam else "Unknown", "subject": exam.subject if exam else "Unknown",
            "risk_level": s.risk_level, "status": s.status, "ai_total_marks": s.ai_total_marks,
            "final_total_marks": s.final_total_marks
        })
    return result

@app.get("/submission-review/{submission_id}")
def get_submission_review(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    student = db.query(Student).filter(Student.id == submission.student_id).first()
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    responses = db.query(StudentResponse).filter(StudentResponse.submission_id == submission_id).all()
    
    questions_data = []
    for r in responses:
        q = db.query(Question).filter(Question.id == r.question_id).first()
        if q:
            questions_data.append({
                "response_id": r.id, "question_number": q.question_number, "question_text": q.question_text,
                "student_answer": r.answer_text or "[No answer]", "max_marks": q.max_marks,
                "ai_marks": r.ai_marks_awarded, "ai_feedback": r.ai_feedback or "No feedback",
                "teacher_marks": r.teacher_marks_awarded, "teacher_feedback": r.teacher_feedback or "",
                "final_marks": r.final_marks
            })
    
    return {
        "submission_id": submission.id, "student_name": student.name if student else "Unknown",
        "exam_name": exam.exam_id if exam else "Unknown", "subject": exam.subject if exam else "Unknown",
        "status": submission.status, "ai_total_marks": submission.ai_total_marks,
        "final_total_marks": submission.final_total_marks, "risk_level": submission.risk_level,
        "risk_factors": submission.risk_factors or [], "ai_feedback_summary": submission.ai_feedback_summary,
        "improvement_suggestions": submission.improvement_suggestions, "learning_path": submission.learning_path,
        "questions": questions_data
    }

@app.post("/teacher-review/{submission_id}")
def teacher_review(submission_id: int, updates: List[TeacherReviewItem], db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    total_marks = 0
    for item in updates:
        response = db.query(StudentResponse).filter(StudentResponse.id == item.response_id, StudentResponse.submission_id == submission_id).first()
        if response:
            response.teacher_marks_awarded = item.teacher_marks
            response.teacher_feedback = item.teacher_feedback
            response.teacher_override = item.teacher_override
            response.final_marks = item.teacher_marks
            total_marks += item.teacher_marks
    submission.final_total_marks = total_marks
    submission.status = "TEACHER_REVIEWED"
    db.commit()
    award_badges(submission.student_id, db)
    update_leaderboard(submission.student_id, db)
    create_notification(db, student_id=submission.student_id, title="Exam Reviewed", message=f"Final score: {total_marks}", type="RESULT", related_id=submission_id)
    return {"message": "Review saved", "total_marks": total_marks}

@app.post("/publish-result/{submission_id}")
def publish_result(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    submission.status = "RESULT_PUBLISHED"
    if submission.weak_topics:
        for topic in submission.weak_topics[:3]:
            recs = generate_youtube_recommendations(topic, 1)
            for r in recs:
                db.add(Recommendation(student_id=submission.student_id, topic=topic, video_url=r["url"], video_title=r["title"]))
    db.commit()
    create_notification(db, student_id=submission.student_id, title="Result Published", message=f"Final score: {submission.final_total_marks}", type="RESULT", related_id=submission_id)
    return {"message": "Result published"}

@app.get("/notifications/{user_id}/{user_type}")
def get_notifications(user_id: int, user_type: str, db: Session = Depends(get_db)):
    if user_type == "student":
        notifs = db.query(Notification).filter(Notification.student_id == user_id).order_by(Notification.created_at.desc()).all()
    else:
        notifs = db.query(Notification).filter(Notification.teacher_id == user_id).order_by(Notification.created_at.desc()).all()
    return [{"id": n.id, "title": n.title, "message": n.message, "type": n.type, "is_read": n.is_read, "created_at": n.created_at} for n in notifs]

@app.post("/mark-notification-read/{notification_id}")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"success": True}

@app.get("/student-recommendations/{student_id}")
def get_student_recommendations(student_id: int, db: Session = Depends(get_db)):
    recs = db.query(Recommendation).filter(Recommendation.student_id == student_id).all()
    return [{"topic": r.topic, "video_title": r.video_title, "video_url": r.video_url} for r in recs]

@app.get("/generate-practice-test/{student_id}/{topic}")
def generate_practice_test_api(student_id: int, topic: str, db: Session = Depends(get_db)):
    return generate_practice_test(topic, 5)

@app.get("/exam-analytics/{exam_id}")
def exam_analytics(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(404, "Exam not found")
    submissions = db.query(Submission).filter(Submission.exam_id == exam_id).all()
    
    scores = [s.final_total_marks for s in submissions if s.final_total_marks]
    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for s in submissions:
        risk_dist[s.risk_level] = risk_dist.get(s.risk_level, 0) + 1
    
    return {
        "exam_name": exam.exam_id, "subject": exam.subject, "class_level": exam.class_level,
        "total_students": len(submissions), "average_score": sum(scores)/len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0, "lowest_score": min(scores) if scores else 0,
        "risk_distribution": risk_dist
    }

@app.get("/generate-report-card/{submission_id}")
def generate_report_card(submission_id: int, db: Session = Depends(get_db)):
    pdf = generate_smart_report_card(submission_id, db)
    if not pdf:
        raise HTTPException(404, "Report not found")
    return FileResponse(pdf, media_type="application/pdf", filename=f"report_card_{submission_id}.pdf")

@app.post("/bulk-upload")
async def bulk_upload(exam_id: int, zip_file: UploadFile = File(...), db: Session = Depends(get_db)):
    zip_path = os.path.join(BULK_UPLOAD_FOLDER, f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)
    extract_path = os.path.join(BULK_UPLOAD_FOLDER, f"extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_path)
    
    results = []
    for student_folder in os.listdir(extract_path):
        student_path = os.path.join(extract_path, student_folder)
        if os.path.isdir(student_path):
            student = db.query(Student).filter(Student.student_id == student_folder).first()
            if student:
                for file in os.listdir(student_path):
                    if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(student_path, file)
                        with open(file_path, 'rb') as f:
                            files = {"file": f}
                            import requests
                            r = requests.post(f"http://localhost:8000/submit-exam/{student.id}/{exam_id}", files=files)
                            results.append({"student_id": student_folder, "filename": file, "status": "Success" if r.status_code == 200 else "Failed"})
    return {"message": f"Processed {len(results)} files", "results": results}

@app.post("/career-guidance/{student_id}")
def save_career_guidance(student_id: int, resume_text: str = Form(None), career_interests: str = Form(None), db: Session = Depends(get_db)):
    existing = db.query(CareerGuidance).filter(CareerGuidance.student_id == student_id).first()
    skills = []
    if resume_text:
        skill_keywords = {"python": "Python", "java": "Java", "javascript": "JavaScript", "sql": "SQL", "react": "React", "machine learning": "ML"}
        for kw, skill in skill_keywords.items():
            if kw in resume_text.lower():
                skills.append(skill)
    rec = f"Based on your profile, consider careers in {', '.join(skills[:3]) if skills else 'technology, business, or education'}."
    if existing:
        existing.resume_text = resume_text
        existing.career_interests = career_interests
        existing.skills_assessment = {"skills": skills}
        existing.recommendations = rec
    else:
        db.add(CareerGuidance(student_id=student_id, resume_text=resume_text, career_interests=career_interests, skills_assessment={"skills": skills}, recommendations=rec))
    db.commit()
    return {"success": True, "recommendations": rec, "skills": skills}

@app.get("/career-guidance/{student_id}")
def get_career_guidance(student_id: int, db: Session = Depends(get_db)):
    guidance = db.query(CareerGuidance).filter(CareerGuidance.student_id == student_id).first()
    if not guidance:
        return {"has_data": False}
    return {"has_data": True, "resume_text": guidance.resume_text, "career_interests": guidance.career_interests, "skills": guidance.skills_assessment.get("skills", []), "recommendations": guidance.recommendations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)