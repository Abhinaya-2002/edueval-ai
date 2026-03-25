from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./aazhi.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


# ==================================
# 1️⃣ EXAM TABLE
# ==================================
class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(String, unique=True, index=True)

    subject = Column(String)
    chapter = Column(String)
    duration = Column(String)

    created_by = Column(String, index=True)
    status = Column(String, default="CREATED")

    exam_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="exam", cascade="all, delete")
    submissions = relationship("Submission", back_populates="exam", cascade="all, delete")


# ==================================
# 2️⃣ QUESTION TABLE
# ==================================
class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    question_number = Column(Integer)  # 🔥 Needed for OCR mapping

    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)

    part = Column(String)  # A / B / C
    question_type = Column(String)  # MCQ / SHORT / LONG

    question_text = Column(Text)

    max_marks = Column(Integer)

    # Correct answer storage
    correct_option = Column(String, nullable=True)  # For MCQ
    correct_answer_text = Column(Text, nullable=True)

    llm_generated_answer = Column(Text, nullable=True)
    teacher_final_answer = Column(Text, nullable=True)
    is_answer_edited = Column(Boolean, default=False)

    exam = relationship("Exam", back_populates="questions")
    options = relationship("Option", back_populates="question", cascade="all, delete")
    responses = relationship("StudentResponse", back_populates="question", cascade="all, delete")


# ==================================
# 3️⃣ OPTION TABLE (MCQ)
# ==================================
class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)

    question_id = Column(Integer, ForeignKey("questions.id"))

    option_text = Column(Text)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="options")


# ==================================
# 4️⃣ STUDENT TABLE
# ==================================
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String)  # Later: hash this

    submissions = relationship("Submission", back_populates="student", cascade="all, delete")


# ==================================
# 5️⃣ SUBMISSION TABLE
# ==================================
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)

    grading_mode = Column(String, default="STRICT")

    uploaded_pdf_path = Column(String)
    extracted_text = Column(Text)

    ai_total_marks = Column(Integer, default=0)
    final_total_marks = Column(Integer, default=0)

    status = Column(String, default="UPLOADED")
    # UPLOADED → OCR_DONE → AI_EVALUATED → TEACHER_REVIEWED

    submitted_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="submissions")
    exam = relationship("Exam", back_populates="submissions")


# ==================================
# 6️⃣ STUDENT RESPONSE TABLE (ONE ROW PER QUESTION)
# ==================================
class StudentResponse(Base):
    __tablename__ = "student_responses"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 NEW: Link response to a specific submission attempt
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Keep student_id (useful for analytics & filtering)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Link to question
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # -------------------------
    # MCQ
    # -------------------------
    selected_option_id = Column(
        Integer,
        ForeignKey("options.id"),
        nullable=True
    )

    # -------------------------
    # Descriptive Answer
    # -------------------------
    answer_text = Column(Text, nullable=True)

    # -------------------------
    # AI Evaluation
    # -------------------------
    ai_is_correct = Column(Boolean, nullable=True)
    ai_marks_awarded = Column(Integer, default=0)
    ai_feedback = Column(Text, nullable=True)

    # -------------------------
    # Teacher Override
    # -------------------------
    teacher_marks_awarded = Column(Integer, nullable=True)
    teacher_feedback = Column(Text, nullable=True)

    # -------------------------
    # Final Result
    # -------------------------
    final_marks = Column(Integer, default=0)

    evaluated_status = Column(
        String,
        default="PENDING"
    )
    # PENDING → AI_EVALUATED → TEACHER_REVIEWED

    # -------------------------
    # Relationships
    # -------------------------
    question = relationship("Question", back_populates="responses")
    submission = relationship("Submission", backref="responses")


# ==================================
# CREATE TABLES
# ==================================
Base.metadata.create_all(bind=engine)


# ==================================
# DB SESSION DEPENDENCY
# ==================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


import json

def save_exam_to_db(db, metadata, exam_data):

    # 1️⃣ Create Exam row
    db_exam = Exam(
        exam_id=metadata["exam_id"],
        subject=exam_data.get("subject"),
        chapter=exam_data.get("chapter"),
        duration=exam_data.get("duration"),
        created_by=metadata["created_by"],
        status=metadata["status"],
        exam_json=json.dumps(exam_data)
    )

    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)

    # 2️⃣ Insert Questions with proper numbering
    parts = exam_data.get("parts", {})

    question_counter = 1  # 🔥 Global numbering across all parts

    for part_name, part_data in parts.items():

        for q in part_data.get("questions", []):

            # Detect question type
            if "options" in q:
                question_type = "MCQ"
                max_marks = 1
            elif part_name == "Part B":
                question_type = "SHORT"
                max_marks = 2
            else:
                question_type = "LONG"
                max_marks = 5

            db_question = Question(
                question_number=question_counter,  # 🔥 IMPORTANT
                exam_id=db_exam.id,
                part=part_name,
                question_type=question_type,
                question_text=q.get("question"),
                max_marks=max_marks,
                correct_option=q.get("correct_option"),
                correct_answer_text=q.get("model_answer"),
                llm_generated_answer=q.get("model_answer"),
                teacher_final_answer=q.get("model_answer"),
                is_answer_edited=False
            )

            db.add(db_question)
            db.commit()
            db.refresh(db_question)

            # 3️⃣ Insert Options (Only for MCQ)
            if question_type == "MCQ":
                for opt in q.get("options", []):
                    option_letter = opt.split(")")[0].strip()

                    db_option = Option(
                        question_id=db_question.id,
                        option_text=opt,
                        is_correct=(option_letter == q.get("correct_option"))
                    )

                    db.add(db_option)

                db.commit()

            question_counter += 1  # 🔥 Increment after each question


class EvaluationHistory(Base):
    __tablename__ = "evaluation_history"

    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    grading_mode = Column(String)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    ai_total_marks = Column(Integer)


    