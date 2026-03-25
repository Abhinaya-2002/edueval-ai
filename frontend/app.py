# app.py - Complete Frontend for Render Deployment
import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import time
import plotly.graph_objects as go
import plotly.express as px

# API URL - Change this for production
API_URL = "https://edueval-ai.onrender.com"
# For local testing: API_URL = "http://127.0.0.1:8000"

# ==================================
# CUSTOM CSS
# ==================================

def load_css():
    st.markdown("""
    <style>
    .stApp { background: #FFFFFF; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    .main .block-container { padding: 1rem 2rem !important; max-width: 1200px; margin: 0 auto; }
    .main-header { background: linear-gradient(135deg, #667EEA, #764BA2, #F59E0B); padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem; text-align: center; }
    .main-header h1 { color: white; font-size: 2rem; margin: 0; }
    .main-header p { color: rgba(255,255,255,0.9); margin-top: 0.5rem; }
    .card { background: white; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .card h3 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .card p { margin: 0; color: #6B7280; font-size: 0.9rem; }
    .stats-card { background: #F9FAFB; border-radius: 12px; padding: 1rem; text-align: center; border: 1px solid #E5E7EB; }
    .stats-number { font-size: 2rem; font-weight: bold; color: #8B5CF6; margin: 0.5rem 0; }
    .admin-card, .teacher-card, .student-card { border-radius: 12px; padding: 1rem; margin-bottom: 1rem; border: 2px solid; }
    .admin-card { background: #FEF3C7; border-color: #F59E0B; }
    .teacher-card { background: #EFF6FF; border-color: #8B5CF6; }
    .student-card { background: #F0FDF4; border-color: #10B981; }
    .stButton > button { background: linear-gradient(135deg, #8B5CF6, #7C3AED); color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; width: 100%; font-weight: 600; }
    .footer { text-align: center; padding: 1rem; margin-top: 2rem; color: #9CA3AF; font-size: 0.8rem; border-top: 1px solid #E5E7EB; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background: #F9FAFB; border-radius: 10px; padding: 0.25rem; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 0.5rem 1rem !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #8B5CF6, #7C3AED) !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# ==================================
# GRAPH FUNCTIONS
# ==================================

def performance_trend(scores, labels):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=scores, mode='lines+markers', line=dict(color='#8B5CF6', width=2), marker=dict(size=8), fill='tozeroy', fillcolor='rgba(139,92,246,0.1)'))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20), title="Performance Trend")
    return fig

# ==================================
# HOME PAGE
# ==================================

def home_page():
    st.markdown("""
    <div class="main-header">
        <h1>🎓 EduEval AI</h1>
        <p>AI-Powered Smart Examination & Evaluation Engine</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="card"><h3>✨ Welcome to EduEval AI</h3><p>AI-powered exam generation, evaluation, and personalized learning platform.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stats-card"><div>⚡ AI Evaluation</div><div class="stats-number">500+</div><div>Exams Evaluated</div></div>', unsafe_allow_html=True)
    
    st.markdown("## 👥 Choose Your Role")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👑 Admin Mode", use_container_width=True):
            st.session_state.nav = "Admin"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 Teacher Mode", use_container_width=True):
            st.session_state.nav = "Teacher"
            st.rerun()
    with col3:
        if st.button("👨‍🎓 Student Mode", use_container_width=True):
            st.session_state.nav = "Student"
            st.rerun()

# ==================================
# ADMIN MODE
# ==================================

def admin_mode():
    st.markdown('<div class="admin-card"><h2>👑 Admin Dashboard</h2><p>Manage teacher registrations</p></div>', unsafe_allow_html=True)
    
    if not st.session_state.get("admin_logged", False):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", key="admin_user")
        with col2:
            password = st.text_input("Password", type="password", key="admin_pass")
        
        if st.button("Login", key="admin_login"):
            try:
                resp = requests.post(f"{API_URL}/admin/login", json={"username": username, "password": password})
                if resp.status_code == 200 and resp.json().get("success"):
                    st.session_state.admin_logged = True
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except:
                st.error("Cannot connect to server")
    else:
        st.success("Welcome Admin!")
        if st.button("Logout", key="admin_logout"):
            st.session_state.admin_logged = False
            st.rerun()
        
        tab1, tab2 = st.tabs(["📋 Pending Teachers", "✅ Approved Teachers"])
        
        with tab1:
            try:
                resp = requests.get(f"{API_URL}/admin/pending-teachers")
                if resp.status_code == 200:
                    pending = resp.json()
                    if pending:
                        for t in pending:
                            st.markdown(f'<div class="card"><h3>{t["name"]}</h3><p>Email: {t["email"]}<br>Subject: {t["subject"]}</p></div>', unsafe_allow_html=True)
                            if st.button(f"Approve {t['name']}", key=f"approve_{t['id']}"):
                                requests.post(f"{API_URL}/admin/approve-teacher", json={"teacher_id": t['id'], "status": "APPROVED"})
                                st.success(f"Approved {t['name']}")
                                st.rerun()
                    else:
                        st.info("No pending approvals")
            except:
                st.error("Failed to fetch data")
        
        with tab2:
            try:
                resp = requests.get(f"{API_URL}/admin/approved-teachers")
                if resp.status_code == 200 and resp.json():
                    st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)
            except:
                st.error("Failed to fetch data")

# ==================================
# TEACHER MODE
# ==================================

def teacher_mode():
    if not st.session_state.get("teacher_logged", False):
        st.markdown('<div class="teacher-card"><h2>👨‍🏫 Teacher Access</h2><p>Login to create exams and assignments</p></div>', unsafe_allow_html=True)
        
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", key="teacher_email")
            with col2:
                password = st.text_input("Password", type="password", key="teacher_pass")
            
            if st.button("Login", key="teacher_login"):
                try:
                    resp = requests.post(f"{API_URL}/teacher/login", json={"email": email, "password": password})
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            st.session_state.teacher_logged = True
                            st.session_state.teacher_id = data["teacher_id"]
                            st.session_state.teacher_name = data["name"]
                            st.success(f"Welcome {data['name']}!")
                            st.rerun()
                        else:
                            st.error(data.get("message", "Login failed"))
                except:
                    st.error("Cannot connect to server")
        
        with register_tab:
            col1, col2 = st.columns(2)
            with col1:
                teacher_id = st.text_input("Teacher ID", key="reg_tid")
                name = st.text_input("Full Name", key="reg_name")
                email = st.text_input("Email", key="reg_email")
                subject = st.text_input("Subject", key="reg_subject")
            with col2:
                password = st.text_input("Password", type="password", key="reg_pass")
                confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                qualification = st.text_input("Qualification", key="reg_qual")
                experience = st.number_input("Experience (years)", min_value=0, key="reg_exp")
            
            if st.button("Register", key="teacher_register"):
                if password != confirm:
                    st.error("Passwords do not match")
                else:
                    try:
                        resp = requests.post(f"{API_URL}/teacher/register", json={
                            "teacher_id": teacher_id, "name": name, "email": email,
                            "password": password, "subject": subject,
                            "qualification": qualification, "experience": experience
                        })
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                st.success("Registration successful! Waiting for admin approval.")
                            else:
                                st.error(data.get("message", "Registration failed"))
                    except:
                        st.error("Cannot connect to server")
    else:
        st.markdown(f'<div class="teacher-card"><h3>👋 Welcome, {st.session_state.teacher_name}!</h3></div>', unsafe_allow_html=True)
        
        if st.button("Logout", key="teacher_logout"):
            st.session_state.teacher_logged = False
            st.rerun()
        
        tabs = st.tabs(["📚 Create Exam", "📊 My Exams"])
        
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("Subject", key="exam_subject")
                chapter = st.text_input("Chapter", key="exam_chapter")
                class_level = st.selectbox("Class", [str(i) for i in range(1, 13)], key="exam_class")
            with col2:
                duration = st.selectbox("Duration", ["1 hour", "1.5 hours", "2 hours"], key="exam_duration")
                partA = st.selectbox("Part A Level", ["Remember", "Understand", "Apply"], key="exam_parta")
                partB = st.selectbox("Part B Level", ["Understand", "Apply", "Analyze"], key="exam_partb")
            
            if st.button("Generate Exam", key="gen_exam"):
                with st.spinner("Generating exam..."):
                    try:
                        payload = {
                            "subject": subject, "chapter": chapter, "class_level": class_level,
                            "duration": duration, "partA_bloom": partA, "partB_bloom": partB, "partC_bloom": partB
                        }
                        resp = requests.post(f"{API_URL}/generate-exam", json=payload, params={"teacher_id": st.session_state.teacher_id})
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.generated = data
                            st.success("Exam generated!")
                        else:
                            st.error("Failed to generate")
                    except:
                        st.error("Cannot connect to server")
            
            if st.session_state.get("generated"):
                exam = st.session_state.generated["exam"]
                st.json(exam)
                if st.button("Publish Exam", key="publish"):
                    try:
                        resp = requests.post(f"{API_URL}/publish-exam/{st.session_state.generated['exam_id']}", params={"teacher_id": st.session_state.teacher_id})
                        if resp.status_code == 200:
                            st.success("Exam published!")
                    except:
                        st.error("Failed to publish")
        
        with tabs[1]:
            try:
                resp = requests.get(f"{API_URL}/exams")
                if resp.status_code == 200:
                    exams = resp.json()
                    if exams:
                        st.dataframe(pd.DataFrame(exams), use_container_width=True)
                    else:
                        st.info("No exams created yet")
            except:
                st.error("Failed to fetch exams")

# ==================================
# STUDENT MODE
# ==================================

def student_mode():
    if not st.session_state.get("student_logged", False):
        st.markdown('<div class="student-card"><h2>👨‍🎓 Student Access</h2><p>Login to take exams and track progress</p></div>', unsafe_allow_html=True)
        
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            col1, col2 = st.columns(2)
            with col1:
                student_id = st.text_input("Student ID", key="student_id")
            with col2:
                password = st.text_input("Password", type="password", key="student_pass")
            
            if st.button("Login", key="student_login"):
                try:
                    resp = requests.post(f"{API_URL}/student/login", json={"student_id": student_id, "password": password})
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("success"):
                            st.session_state.student_logged = True
                            st.session_state.student_id = data["student_id"]
                            st.session_state.student_name = data["name"]
                            st.success(f"Welcome {data['name']}!")
                            st.rerun()
                        else:
                            st.error(data.get("message", "Login failed"))
                except:
                    st.error("Cannot connect to server")
        
        with register_tab:
            col1, col2 = st.columns(2)
            with col1:
                sid = st.text_input("Student ID", key="reg_sid")
                name = st.text_input("Full Name", key="reg_sname")
                class_level = st.selectbox("Class", [str(i) for i in range(1, 13)], key="reg_class")
            with col2:
                password = st.text_input("Password", type="password", key="reg_spass")
                confirm = st.text_input("Confirm Password", type="password", key="reg_sconfirm")
                email = st.text_input("Email (optional)", key="reg_semail")
            
            if st.button("Register", key="student_register"):
                if password != confirm:
                    st.error("Passwords do not match")
                else:
                    try:
                        resp = requests.post(f"{API_URL}/student/register", json={
                            "student_id": sid, "name": name, "email": email,
                            "password": password, "class_level": class_level, "section": "A"
                        })
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                st.success("Registration successful! Please login.")
                            else:
                                st.error(data.get("message", "Registration failed"))
                    except:
                        st.error("Cannot connect to server")
    else:
        st.markdown(f'<div class="student-card"><h3>👋 Welcome, {st.session_state.student_name}!</h3></div>', unsafe_allow_html=True)
        
        if st.button("Logout", key="student_logout"):
            st.session_state.student_logged = False
            st.rerun()
        
        try:
            dashboard = requests.get(f"{API_URL}/student-dashboard/{st.session_state.student_id}").json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Exams Taken", dashboard['statistics']['total_exams_taken'])
            with col2:
                st.metric("Average Score", f"{dashboard['statistics']['average_score']}%")
            with col3:
                st.metric("Streak Days", dashboard['student'].get('streak_days', 0))
            
            st.markdown("### 📚 Available Exams")
            
            for exam in dashboard["exams"]:
                with st.expander(f"{exam['exam_name']} - {exam['subject']}"):
                    st.write(f"Duration: {exam['duration']} | Marks: {exam['total_marks']}")
                    
                    if exam["status"] == "NOT_ATTEMPTED":
                        uploaded = st.file_uploader("Upload Answer Sheet", type=["pdf", "jpg", "png"], key=f"upload_{exam['exam_id']}")
                        if uploaded:
                            files = {"file": uploaded}
                            with st.spinner("Evaluating..."):
                                resp = requests.post(f"{API_URL}/submit-exam/{st.session_state.student_id}/{exam['exam_id']}", files=files)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    st.success(f"Score: {data['score']}/{exam['total_marks']}")
                                    st.rerun()
                    
                    elif exam.get("submission_id"):
                        if st.button("View Result", key=f"view_{exam['exam_id']}"):
                            result = requests.get(f"{API_URL}/submission-result/{exam['submission_id']}").json()
                            st.markdown(f"### Score: {result['percentage']}%")
                            st.markdown(f"**{result['total_marks']} / {result['max_marks']} marks**")
                            
                            if result.get('questions'):
                                for q in result['questions'][:3]:
                                    with st.expander(f"Question {q['question_number']}"):
                                        st.write(q['question_text'])
                                        st.write(f"Marks: {q['marks_awarded']}/{q['max_marks']}")
                                        if q.get('ai_feedback'):
                                            st.info(q['ai_feedback'])
            
            # Leaderboard
            st.markdown("### 🏆 Leaderboard")
            try:
                leaderboard = requests.get(f"{API_URL}/leaderboard").json()
                if leaderboard:
                    for i, s in enumerate(leaderboard[:5]):
                        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                        st.markdown(f"<div class='card'><b>{medal}</b> {s['name']} - {s['average_score']}% ({s['exams_taken']} exams)</div>", unsafe_allow_html=True)
            except:
                pass
                
        except Exception as e:
            st.error("Failed to load dashboard")

# ==================================
# MAIN
# ==================================

def main():
    if 'nav' not in st.session_state:
        st.session_state.nav = "Home"
    if 'admin_logged' not in st.session_state:
        st.session_state.admin_logged = False
    if 'teacher_logged' not in st.session_state:
        st.session_state.teacher_logged = False
    if 'student_logged' not in st.session_state:
        st.session_state.student_logged = False
    
    load_css()
    
    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.nav = "Home"
            st.rerun()
    with col2:
        if st.button("👑 Admin", use_container_width=True):
            st.session_state.nav = "Admin"
            st.rerun()
    with col3:
        if st.button("👨‍🏫 Teacher", use_container_width=True):
            st.session_state.nav = "Teacher"
            st.rerun()
    with col4:
        if st.button("👨‍🎓 Student", use_container_width=True):
            st.session_state.nav = "Student"
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.nav == "Home":
        home_page()
    elif st.session_state.nav == "Admin":
        admin_mode()
    elif st.session_state.nav == "Teacher":
        teacher_mode()
    elif st.session_state.nav == "Student":
        student_mode()
    
    st.markdown('<div class="footer"><p>© 2024 EduEval AI - Smart Examination & Evaluation Engine</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
