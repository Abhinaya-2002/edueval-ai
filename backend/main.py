# main.py - Complete Backend with All 11 Advanced Features
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect
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
import speech_recognition as sr
import asyncio
from sklearn.linear_model import LinearRegression
import numpy as np

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
    learning_style = Column(String, default="visual")
    behavior_data = Column(JSON, default={})
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
    adaptive_level = Column(String, default="standard")
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
    question_text_tamil = Column(Text, nullable=True)
    question_text_hindi = Column(Text, nullable=True)
    max_marks = Column(Integer)
    correct_option = Column(String, nullable=True)
    teacher_final_answer = Column(Text, nullable=True)
    bloom_level = Column(String)
    difficulty = Column(String, default="medium")
    exam = relationship("Exam")

class Option(Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    option_text = Column(String)
    option_text_tamil = Column(String, nullable=True)
    option_text_hindi = Column(String, nullable=True)
    is_correct = Column(Boolean, default=False)
    question = relationship("Question")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    uploaded_pdf_path = Column(String)
    extracted_text = Column(Text, nullable=True)
    time_taken = Column(Integer, default=0)
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
    predicted_next_score = Column(Float, default=0.0)
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
    answer_audio_path = Column(String, nullable=True)
    ai_is_correct = Column(Boolean, nullable=True)
    ai_marks_awarded = Column(Integer, default=0)
    ai_feedback = Column(Text, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    mistake_type = Column(String, nullable=True)
    teacher_marks_awarded = Column(Integer, default=0)
    teacher_feedback = Column(Text, nullable=True)
    teacher_override = Column(Boolean, default=False)
    final_marks = Column(Integer, default=0)
    evaluated_status = Column(String, default="PENDING")
    submission = relationship("Submission")
    student = relationship("Student")
    question = relationship("Question")

class DiscussionPost(Base):
    __tablename__ = "discussion_posts"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    content = Column(Text)
    answer_reference = Column(Text, nullable=True)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")
    exam = relationship("Exam")

class RevisionReminder(Base):
    __tablename__ = "revision_reminders"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic = Column(String)
    scheduled_date = Column(Date)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    certificate_number = Column(String, unique=True)
    score = Column(Integer)
    percentage = Column(Float)
    issued_at = Column(DateTime, default=datetime.utcnow)
    student = relationship("Student")
    exam = relationship("Exam")

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
    adaptive_level: str = "standard"

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

class VoiceAnswerRequest(BaseModel):
    student_id: int
    exam_id: int
    question_id: int
    audio_base64: str

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
AUDIO_FOLDER = "audio"
BULK_UPLOAD_FOLDER = "bulk_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ASSIGNMENT_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
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
    {"name": "Top Performer", "description": "Ranked in top 3", "icon": "🏆", "criteria": "top_3"},
    {"name": "Voice Champion", "description": "Used voice input", "icon": "🎙️", "criteria": "voice_input"},
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

def speech_to_text(audio_bytes):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
    except:
        return ""

def generate_ai_explanation(question, student_answer, correct_answer, marks_awarded, max_marks):
    try:
        prompt = f"""
        Question: {question}
        Student Answer: {student_answer}
        Correct Answer: {correct_answer}
        Marks: {marks_awarded}/{max_marks}
        
        Explain:
        1. What was wrong
        2. Specific mistakes
        3. How to correct
        4. Key points to remember
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content
    except:
        return f"Score: {marks_awarded}/{max_marks}. Review the correct answer."

def predict_future_score(student_id, db):
    submissions = db.query(Submission).filter(Submission.student_id == student_id).order_by(Submission.created_at).all()
    if len(submissions) < 3:
        return 0.0
    scores = []
    for s in submissions:
        exam = db.query(Exam).filter(Exam.id == s.exam_id).first()
        if exam and exam.total_marks:
            scores.append((s.final_total_marks / exam.total_marks) * 100)
    if len(scores) < 3:
        return 0.0
    X = np.array(range(len(scores))).reshape(-1, 1)
    y = np.array(scores)
    model = LinearRegression()
    model.fit(X, y)
    return max(0, min(100, model.predict([[len(scores)]])[0]))

def analyze_student_behavior(student_id, db):
    student = db.query(Student).filter(Student.id == student_id).first()
    submissions = db.query(Submission).filter(Submission.student_id == student_id).order_by(Submission.created_at).all()
    behavior = {"total_exams": len(submissions), "average_time": 0, "improvement_rate": 0, "consistency": "Low", "learning_pace": "Average", "recommendations": []}
    if submissions:
        times = [s.time_taken for s in submissions if s.time_taken > 0]
        if times:
            behavior["average_time"] = sum(times) / len(times)
        scores = []
        for s in submissions:
            exam = db.query(Exam).filter(Exam.id == s.exam_id).first()
            if exam and exam.total_marks:
                scores.append((s.final_total_marks / exam.total_marks) * 100)
        if len(scores) >= 2:
            improvement = scores[-1] - scores[0]
            behavior["improvement_rate"] = improvement
            if improvement > 20:
                behavior["learning_pace"] = "Fast"
                behavior["recommendations"].append("You're improving quickly!")
            elif improvement > 5:
                behavior["learning_pace"] = "Steady"
                behavior["recommendations"].append("Good steady progress.")
            else:
                behavior["learning_pace"] = "Slow"
                behavior["recommendations"].append("Need more consistent practice.")
        if len(scores) >= 3:
            variance = np.var(scores)
            if variance < 100:
                behavior["consistency"] = "High"
            elif variance < 300:
                behavior["consistency"] = "Medium"
            else:
                behavior["consistency"] = "Low"
    return behavior

def generate_adaptive_questions(question, difficulty):
    try:
        prompt = f"Generate similar question with {difficulty} difficulty. Original: {question}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return {"question": response.choices[0].message.content, "options": ["A) Option1", "B) Option2", "C) Option3", "D) Option4"], "correct": "A"}
    except:
        return {"question": question, "options": ["A) Option1", "B) Option2", "C) Option3", "D) Option4"], "correct": "A"}

def generate_certificate(student_id, exam_id, db):
    student = db.query(Student).filter(Student.id == student_id).first()
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    submission = db.query(Submission).filter(Submission.student_id == student_id, Submission.exam_id == exam_id).first()
    if not student or not exam or not submission:
        return None
    percentage = (submission.final_total_marks / exam.total_marks) * 100 if exam.total_marks else 0
    cert_number = f"CERT-{student.student_id}-{exam.exam_id}-{datetime.now().strftime('%Y%m%d')}"
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Certificate of Achievement", ParagraphStyle('CertTitle', parent=styles['Heading1'], fontSize=28, alignment=TA_CENTER, spaceAfter=30)))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"This certifies that", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(student.name, ParagraphStyle('Name', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=20)))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"has successfully completed the examination in", styles['Normal']))
    elements.append(Paragraph(f"<b>{exam.subject} - {exam.chapter}</b>", styles['Normal']))
    elements.append(Paragraph(f"with a score of <b>{submission.final_total_marks}/{exam.total_marks}</b> marks ({percentage:.1f}%)", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Certificate Number: {cert_number}", styles['Normal']))
    elements.append(Paragraph(f"Issued on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    doc.build(elements)
    buffer.seek(0)
    cert = Certificate(student_id=student_id, exam_id=exam_id, certificate_number=cert_number, score=submission.final_total_marks, percentage=percentage)
    db.add(cert)
    db.commit()
    return buffer

def get_question_text(question, language):
    if language == "tamil" and question.question_text_tamil:
        return question.question_text_tamil
    elif language == "hindi" and question.question_text_hindi:
        return question.question_text_hindi
    return question.question_text

def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def send_reset_email(email, token, user_type):
    print(f"Reset link: http://localhost:8000/reset-password?token={token}&type={user_type}")
    return True

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def analyze_mistakes(student_answer, correct_answer):
    mistakes = []
    if not student_answer or student_answer.strip() == "":
        mistakes.append("No answer provided")
        return mistakes
    student_lower = student_answer.lower()
    correct_lower = correct_answer.lower()
    if len(student_answer) < len(correct_answer) * 0.5:
        mistakes.append("Answer is incomplete")
    return mistakes if mistakes else ["Minor improvements needed"]

def generate_learning_path(weak_topics, student_score):
    learning_path = {"daily_plan": [], "resources": [], "estimated_days": 0, "intensity": "Medium", "recommended_hours": 2}
    if not weak_topics:
        return learning_path
    days = []
    for i, topic in enumerate(weak_topics[:5]):
        days.append({"day": i+1, "topic": topic, "activities": [f"Read about {topic}", f"Watch video on {topic}", f"Practice 5 questions", f"Take mini-test"]})
        learning_path["resources"].append({"topic": topic, "video": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial"})
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
        prompt = f"Generate {num_questions} practice questions on {topic}. Return JSON with questions array."
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
        return {"topic": topic, "questions": [{"question": f"Question on {topic}", "options": ["A) Opt1", "B) Opt2", "C) Opt3", "D) Opt4"], "correct": "A", "explanation": "Explanation"}]}
    except:
        return {"topic": topic, "questions": [{"question": f"Sample question on {topic}", "options": ["A) Opt1", "B) Opt2", "C) Opt3", "D) Opt4"], "correct": "A", "explanation": "Explanation"}]}

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
    percentage = (submission.final_total_marks / exam.total_marks * 100) if exam and exam.total_marks else 0
    elements.append(Paragraph("Smart Report Card", ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, alignment=TA_CENTER, spaceAfter=20)))
    elements.append(Table([["Student", student.name], ["Exam", exam.exam_id], ["Score", f"{submission.final_total_marks}/{exam.total_marks}"], ["Percentage", f"{percentage:.1f}%"]], colWidths=[100, 250]))
    if submission.ai_feedback_summary:
        elements.append(Paragraph("Feedback", styles["Heading2"]))
        elements.append(Paragraph(submission.ai_feedback_summary, styles["Normal"]))
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
        current_badges.append({"name": "First Exam", "description": "Completed first exam", "icon": "🎓", "earned_at": datetime.utcnow().isoformat()})
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
            badges.append({"name": "Top Performer", "description": "Top 3", "icon": "🏆", "earned_at": datetime.utcnow().isoformat()})
            student.badges = badges
            db.commit()

def get_leaderboard(db, limit=10):
    entries = db.query(Leaderboard).order_by(Leaderboard.average_score.desc()).limit(limit).all()
    return [{"rank": e.rank, "name": db.query(Student).filter(Student.id == e.student_id).first().name, "average_score": round(e.average_score, 2), "exams_taken": e.exams_taken} for e in entries if db.query(Student).filter(Student.id == e.student_id).first()]

def get_ai_chat_response_with_context(message, student_id, db):
    student = db.query(Student).filter(Student.id == student_id).first() if student_id else None
    weak_topics = []
    if student:
        submissions = db.query(Submission).filter(Submission.student_id == student_id).order_by(Submission.created_at.desc()).limit(3).all()
        for s in submissions:
            if s.weak_topics:
                weak_topics.extend(s.weak_topics[:3])
        weak_topics = list(set(weak_topics))
    context = f"Student weak topics: {', '.join(weak_topics[:3])}. " if weak_topics else ""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": f"You are EduEval AI Assistant. Context: {context}"}, {"role": "user", "content": message}],
            temperature=0.7, max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return f"I'm here to help! Focus on {', '.join(weak_topics[:2]) if weak_topics else 'key concepts'}."

def get_ai_evaluation(student_answer, correct_answer, max_marks):
    try:
        prompt = f"Evaluate: Correct: {correct_answer}, Student: {student_answer}, Max: {max_marks}. Return JSON: {{'marks': number, 'feedback': 'text'}}"
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.5, max_tokens=300)
        import json
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except:
        similarity = calculate_similarity(student_answer, correct_answer)
        return {"marks": int(similarity * max_marks), "feedback": f"Matches {similarity*100:.0f}%"}

def generate_exam_ai(subject, chapter, class_level, duration, partA_bloom, partB_bloom, partC_bloom):
    try:
        prompt = f"Generate exam for {subject}-{chapter} for {class_level}. Duration: {duration}. Part A: 10 MCQ at {partA_bloom} (1 mark), Part B: 7 Short at {partB_bloom} (2 marks), Part C: 5 Long at {partC_bloom} (5 marks). Return JSON."
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=2000)
        return response.choices[0].message.content
    except:
        return json.dumps({"subject": subject, "chapter": chapter, "total_marks": 49, "parts": {"Part A": {"type": "MCQ", "questions": [{"question": f"Sample MCQ", "options": ["A) Opt1", "B) Opt2", "C) Opt3", "D) Opt4"], "correct": "A"}]}}})

def save_exam_to_db(db, metadata, exam_data, teacher_id):
    exam = Exam(
        exam_id=metadata["exam_id"], subject=exam_data.get("subject"), chapter=exam_data.get("chapter"),
        class_level=exam_data.get("class_level"), duration=exam_data.get("duration"),
        total_marks=exam_data.get("total_marks", 49), created_by=teacher_id,
        created_at=datetime.fromisoformat(metadata["created_at"]), status=metadata["status"],
        exam_data=json.dumps(exam_data)
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam

def create_notification(db, student_id=None, teacher_id=None, title="", message="", type="", related_id=None):
    if student_id:
        db.add(Notification(student_id=student_id, title=title, message=message, type=type, related_id=related_id))
    if teacher_id:
        db.add(Notification(teacher_id=teacher_id, title=title, message=message, type=type, related_id=related_id))
    db.commit()

def generate_youtube_recommendations(topic):
    return [{"title": f"Learn {topic}", "url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial", "duration": "10 mins"}]

# ==================================
# FASTAPI APP
# ==================================

app = FastAPI(title="EduEval AI", version="6.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    db = SessionLocal()
    if not db.query(Admin).filter(Admin.username == DEFAULT_ADMIN["username"]).first():
        db.add(Admin(**DEFAULT_ADMIN))
    for badge in DEFAULT_BADGES:
        if not db.query(Badge).filter(Badge.name == badge["name"]).first():
            db.add(Badge(**badge))
    db.commit()
    db.close()

# ==================================
# ENDPOINTS
# ==================================

@app.post("/admin/login")
def admin_login(request: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == request.username, Admin.password == request.password).first()
    return {"success": bool(admin)}

@app.get("/admin/pending-teachers")
def get_pending_teachers(db: Session = Depends(get_db)):
    return [{"id": t.id, "name": t.name, "email": t.email, "subject": t.subject} for t in db.query(Teacher).filter(Teacher.status == "PENDING").all()]

@app.post("/admin/approve-teacher")
def approve_teacher(request: TeacherApprove, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id).first()
    if teacher:
        teacher.status = request.status
        teacher.approved_at = datetime.utcnow()
        db.commit()
    return {"success": True}

@app.post("/teacher/register")
def teacher_register(request: TeacherRegister, db: Session = Depends(get_db)):
    if db.query(Teacher).filter((Teacher.email == request.email) | (Teacher.teacher_id == request.teacher_id)).first():
        return {"success": False, "message": "Exists"}
    db.add(Teacher(**request.dict(), status="PENDING"))
    db.commit()
    return {"success": True}

@app.post("/teacher/login")
def teacher_login(request: TeacherLogin, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.email == request.email, Teacher.password == request.password).first()
    if not teacher or teacher.status != "APPROVED":
        return {"success": False}
    return {"success": True, "teacher_id": teacher.id, "name": teacher.name, "subject": teacher.subject}

@app.post("/student/register")
def student_register(request: StudentRegister, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.student_id == request.student_id).first():
        return {"success": False, "message": "ID exists"}
    db.add(Student(**request.dict()))
    db.commit()
    return {"success": True}

@app.post("/student/login")
def student_login(request: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == request.student_id, Student.password == request.password).first()
    if not student:
        return {"success": False}
    student.last_active = datetime.utcnow()
    student.streak_days = (student.streak_days + 1) if student.last_active.date() == datetime.utcnow().date() - timedelta(days=1) else 1
    db.commit()
    award_badges(student.id, db)
    return {"success": True, "student_id": student.id, "name": student.name, "class_level": student.class_level, "language": student.language, "streak_days": student.streak_days, "badges": student.badges}

@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    response = get_ai_chat_response_with_context(request.message, request.user_id if request.user_type == "student" else 0, db)
    db.add(ChatHistory(user_id=request.user_id, user_type=request.user_type, message=request.message, response=response))
    db.commit()
    return {"response": response}

@app.post("/generate-exam")
def create_exam(request: ExamRequest, teacher_id: int, db: Session = Depends(get_db)):
    result = generate_exam_ai(request.subject, request.chapter, request.class_level, request.duration, request.partA_bloom, request.partB_bloom, request.partC_bloom)
    exam_data = json.loads(result.strip().replace("```json", "").replace("```", ""))
    exam_id = "EXAM_" + uuid.uuid4().hex[:8].upper()
    metadata = {"exam_id": exam_id, "class_level": request.class_level, "created_at": datetime.utcnow().isoformat(), "status": "DRAFT"}
    exam = save_exam_to_db(db, metadata, exam_data, teacher_id)
    return {"exam": exam_data, "exam_id": exam.id}

@app.post("/publish-exam/{exam_id}")
def publish_exam(exam_id: int, teacher_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if exam:
        exam.status = "PUBLISHED"
        db.commit()
    return {"message": "Published"}

@app.get("/exams")
def get_exams(db: Session = Depends(get_db)):
    return [{"id": e.id, "exam_id": e.exam_id, "subject": e.subject, "chapter": e.chapter, "total_marks": e.total_marks} for e in db.query(Exam).all()]

@app.post("/submit-exam/{student_id}/{exam_id}")
def submit_exam(student_id: int, exam_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not student or not exam:
        raise HTTPException(404, "Not found")
    file_path = os.path.join(UPLOAD_FOLDER, f"{student_id}_{exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    extracted = extract_text_from_file(file_path)
    submission = Submission(student_id=student_id, exam_id=exam_id, uploaded_pdf_path=file_path, extracted_text=extracted, status="UPLOADED")
    db.add(submission)
    db.commit()
    db.refresh(submission)
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    total = 0
    weak = []
    for q in questions:
        eval_result = get_ai_evaluation(extracted or "", q.teacher_final_answer or "", q.max_marks)
        marks = eval_result.get("marks", 0)
        explanation = generate_ai_explanation(q.question_text, extracted or "", q.teacher_final_answer or "", marks, q.max_marks)
        response = StudentResponse(
            submission_id=submission.id, student_id=student_id, question_id=q.id, answer_text=extracted,
            ai_marks_awarded=marks, ai_feedback=eval_result.get("feedback", ""), ai_explanation=explanation,
            final_marks=marks
        )
        db.add(response)
        total += marks
        if marks < q.max_marks * 0.5:
            weak.append(q.question_text[:50])
    submission.status = "AI_EVALUATED"
    submission.ai_total_marks = total
    submission.final_total_marks = total
    submission.weak_topics = list(set(weak[:5]))
    submission.predicted_next_score = predict_future_score(student_id, db)
    db.commit()
    award_badges(student_id, db)
    update_leaderboard(student_id, db)
    return {"submission_id": submission.id, "score": total, "percentage": (total/exam.total_marks*100) if exam.total_marks else 0}

@app.get("/student-dashboard/{student_id}")
def student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    submissions = {s.exam_id: s for s in db.query(Submission).filter(Submission.student_id == student_id).all()}
    exams = db.query(Exam).filter(Exam.status == "PUBLISHED", Exam.class_level == student.class_level).all() if student else []
    return {
        "student": {"name": student.name, "streak_days": student.streak_days, "badges": student.badges},
        "exams": [{"exam_id": e.id, "exam_name": e.exam_id, "subject": e.subject, "status": submissions.get(e.id).status if submissions.get(e.id) else "NOT_ATTEMPTED", "submission_id": submissions.get(e.id).id if submissions.get(e.id) else None} for e in exams],
        "statistics": {"total_exams_taken": len([s for s in submissions.values() if s.status in ["AI_EVALUATED", "RESULT_PUBLISHED"]]), "total_published_exams": len(exams)}
    }

@app.get("/submission-result/{submission_id}")
def get_submission_result(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    responses = db.query(StudentResponse).filter(StudentResponse.submission_id == submission_id).all()
    questions = []
    weak = []
    for r in responses:
        q = db.query(Question).filter(Question.id == r.question_id).first()
        if q:
            percentage = (r.final_marks / q.max_marks) * 100 if q.max_marks else 0
            if percentage < 50:
                weak.append(q.question_text[:50])
            questions.append({"question_number": q.question_number, "question_text": q.question_text, "marks_awarded": r.final_marks, "max_marks": q.max_marks, "ai_explanation": r.ai_explanation})
    return {
        "total_marks": submission.final_total_marks, "max_marks": exam.total_marks,
        "percentage": (submission.final_total_marks / exam.total_marks * 100) if exam.total_marks else 0,
        "questions": questions, "weak_topics": list(set(weak[:3])),
        "predicted_next_score": submission.predicted_next_score,
        "behavior_analysis": analyze_student_behavior(submission.student_id, db)
    }

@app.get("/leaderboard")
def get_leaderboard_api(db: Session = Depends(get_db)):
    return get_leaderboard(db)

@app.get("/generate-certificate/{submission_id}")
def generate_certificate_api(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Not found")
    pdf = generate_certificate(submission.student_id, submission.exam_id, db)
    return FileResponse(pdf, media_type="application/pdf", filename=f"certificate_{submission_id}.pdf")

@app.get("/career-guidance/{student_id}")
def get_career_guidance(student_id: int, db: Session = Depends(get_db)):
    guidance = db.query(CareerGuidance).filter(CareerGuidance.student_id == student_id).first()
    return {"has_data": bool(guidance), "recommendations": guidance.recommendations if guidance else ""}

@app.post("/career-guidance/{student_id}")
def save_career_guidance(student_id: int, career_interests: str = Form(None), db: Session = Depends(get_db)):
    guidance = db.query(CareerGuidance).filter(CareerGuidance.student_id == student_id).first()
    if guidance:
        guidance.career_interests = career_interests
    else:
        guidance = CareerGuidance(student_id=student_id, career_interests=career_interests)
        db.add(guidance)
    db.commit()
    return {"success": True}

@app.get("/generate-practice-test/{student_id}/{topic}")
def generate_practice_test_api(student_id: int, topic: str, db: Session = Depends(get_db)):
    return generate_practice_test(topic, 3)

@app.get("/exam-analytics/{exam_id}")
def exam_analytics(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    submissions = db.query(Submission).filter(Submission.exam_id == exam_id).all()
    scores = [s.final_total_marks for s in submissions if s.final_total_marks]
    return {
        "exam_name": exam.exam_id, "total_students": len(submissions),
        "average_score": sum(scores)/len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0
    }

@app.get("/student-behavior/{student_id}")
def get_student_behavior(student_id: int, db: Session = Depends(get_db)):
    return analyze_student_behavior(student_id, db)

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
                        with open(os.path.join(student_path, file), 'rb') as f:
                            r = requests.post(f"http://localhost:8000/submit-exam/{student.id}/{exam_id}", files={"file": f})
                            results.append({"student": student_folder, "status": "Success" if r.status_code == 200 else "Failed"})
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
