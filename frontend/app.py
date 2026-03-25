# app.py - Complete Frontend with All 11 Advanced Features (No Empty Spaces)
import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
import pandas as pd
import time
import plotly.graph_objects as go
import plotly.express as px
import base64
import os
import cv2
import numpy as np
from PIL import Image
import speech_recognition as sr
import wave

API_URL = "https://edueval-ai.onrender.com"

# ==================================
# CUSTOM CSS - MINIMAL SPACING
# ==================================

def load_css():
    st.markdown("""
    <style>
    .stApp { background: #FFFFFF; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    .main .block-container { padding: 0.5rem 1rem 0.5rem 1rem !important; max-width: 100% !important; }
    .main-header { background: linear-gradient(135deg, #667EEA 0%, #764BA2 50%, #F59E0B 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.75rem; text-align: center; }
    .main-header h1 { color: white; font-size: 1.5rem; font-weight: 800; margin: 0; }
    .main-header p { color: rgba(255,255,255,0.95); margin-top: 0.1rem; font-size: 0.7rem; }
    .card { background: #FFFFFF; border-radius: 10px; padding: 0.6rem; margin-bottom: 0.6rem; border: 1px solid #E5E7EB; transition: all 0.2s ease; }
    .card:hover { border-color: #8B5CF6; transform: translateY(-1px); }
    .card h2 { font-size: 1rem; margin-bottom: 0.2rem; }
    .card h3 { font-size: 0.9rem; margin-bottom: 0.2rem; }
    .card p { font-size: 0.75rem; color: #6B7280; margin: 0; }
    .stats-card { background: #F9FAFB; border-radius: 10px; padding: 0.5rem; text-align: center; border: 1px solid #E5E7EB; }
    .stats-number { font-size: 1.3rem; font-weight: 800; background: linear-gradient(135deg, #8B5CF6, #7C3AED); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0.2rem 0; }
    .admin-card, .teacher-card, .student-card { border-radius: 10px; padding: 0.6rem; margin-bottom: 0.6rem; border: 2px solid; }
    .admin-card { background: #FEF3C7; border-color: #F59E0B; }
    .teacher-card { background: #EFF6FF; border-color: #8B5CF6; }
    .student-card { background: #F0FDF4; border-color: #10B981; }
    .risk-card-low { background: #F0FDF4; border-radius: 8px; padding: 0.4rem; border-left: 3px solid #10B981; font-size: 0.7rem; }
    .risk-card-medium { background: #FFF7ED; border-radius: 8px; padding: 0.4rem; border-left: 3px solid #F59E0B; font-size: 0.7rem; }
    .risk-card-high { background: #FEF2F2; border-radius: 8px; padding: 0.4rem; border-left: 3px solid #EF4444; font-size: 0.7rem; }
    .stButton > button { background: linear-gradient(135deg, #8B5CF6, #7C3AED) !important; color: white !important; border: none !important; padding: 0.3rem 0.6rem !important; font-weight: 600 !important; border-radius: 6px !important; width: 100% !important; font-size: 0.75rem !important; }
    .footer { text-align: center; padding: 0.5rem; margin-top: 0.5rem; background: #F9FAFB; font-size: 0.65rem; color: #9CA3AF; border-top: 1px solid #E5E7EB; }
    .floating-ai { position: fixed; bottom: 15px; right: 15px; z-index: 1000; }
    .chat-toggle-btn { background: linear-gradient(135deg, #8B5CF6, #7C3AED); border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 20px; cursor: pointer; color: white; display: flex; align-items: center; justify-content: center; }
    .chat-window { position: fixed; bottom: 65px; right: 15px; width: 280px; height: 350px; background: white; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.15); display: flex; flex-direction: column; z-index: 999; border: 1px solid #E5E7EB; }
    .chat-header { background: linear-gradient(135deg, #8B5CF6, #7C3AED); padding: 6px; color: white; display: flex; justify-content: space-between; font-weight: 600; font-size: 0.7rem; border-radius: 10px 10px 0 0; }
    .chat-messages { flex: 1; overflow-y: auto; padding: 6px; background: #F9FAFB; font-size: 0.7rem; }
    .chat-input-area { padding: 5px; border-top: 1px solid #E5E7EB; display: flex; gap: 4px; background: white; }
    .chat-input-area input { flex: 1; padding: 4px 6px; border: 1px solid #E5E7EB; border-radius: 12px; font-size: 0.7rem; }
    .user-msg { text-align: right; margin: 3px 0; }
    .user-msg div { background: #8B5CF6; color: white; padding: 4px 6px; border-radius: 10px; display: inline-block; max-width: 85%; font-size: 0.7rem; }
    .bot-msg { text-align: left; margin: 3px 0; }
    .bot-msg div { background: white; padding: 4px 6px; border-radius: 10px; border: 1px solid #E5E7EB; display: inline-block; max-width: 85%; font-size: 0.7rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.2rem; background: #F9FAFB; border-radius: 8px; padding: 0.2rem; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 0.3rem 0.8rem !important; font-size: 0.75rem !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #8B5CF6, #7C3AED) !important; color: white !important; }
    .stExpander { border: none; }
    .streamlit-expanderHeader { font-size: 0.8rem; background: #F9FAFB; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ==================================
# CHATBOT COMPONENT
# ==================================

def ai_chatbot():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    
    st.markdown('<div class="floating-ai"><button class="chat-toggle-btn">🤖</button></div>', unsafe_allow_html=True)
    if st.button("🤖", key="chat_toggle", help="AI Assistant"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
    
    if st.session_state.chat_open:
        st.markdown('<div class="chat-window"><div class="chat-header"><span>🤖 AI Assistant</span></div><div class="chat-messages">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history[-12:]:
            if msg["type"] == "user":
                st.markdown(f'<div class="user-msg"><div>{msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg"><div>{msg["content"]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
        user_input = st.text_input("", key="chat_input", placeholder="Ask...", label_visibility="collapsed")
        send = st.button("Send", key="chat_send")
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        if send and user_input:
            st.session_state.chat_history.append({"type": "user", "content": user_input})
            try:
                user_type = "student" if st.session_state.get("nav") == "Student" else "teacher"
                user_id = st.session_state.get("student_id") if user_type == "student" else st.session_state.get("teacher_id", 1)
                resp = requests.post(f"{API_URL}/chat", json={"user_id": user_id, "user_type": user_type, "message": user_input})
                ai_resp = resp.json().get("response", "I'm here to help!") if resp.status_code == 200 else "Hello!"
            except:
                ai_resp = "Hello! How can I help?"
            st.session_state.chat_history.append({"type": "bot", "content": ai_resp})
            st.rerun()

# ==================================
# GRAPH FUNCTIONS
# ==================================

def performance_trend(scores, labels):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=scores, mode='lines+markers', line=dict(color='#8B5CF6', width=2), marker=dict(size=6), fill='tozeroy', fillcolor='rgba(139,92,246,0.1)'))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='white', plot_bgcolor='#F9FAFB', title_font_size=12)
    return fig

def class_comparison(your_score, class_avg, topper):
    fig = go.Figure(data=[go.Bar(x=['You', 'Class', 'Topper'], y=[your_score, class_avg, topper], marker_color=['#8B5CF6', '#F59E0B', '#10B981'], text=[f"{your_score}%", f"{class_avg}%", f"{topper}%"], textposition='auto')])
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    return fig

def question_chart(questions):
    q_nums = [q['q_no'] for q in questions]
    obtained = [q['marks'] for q in questions]
    max_marks = [q['max'] for q in questions]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=q_nums, y=obtained, name='Obtained', marker_color='#8B5CF6'))
    fig.add_trace(go.Bar(x=q_nums, y=[m-o for m,o in zip(max_marks, obtained)], name='Lost', marker_color='#EF4444', base=obtained))
    fig.update_layout(height=250, barmode='stack', margin=dict(l=20, r=20, t=30, b=20))
    return fig

def correct_wrong_pie(correct, wrong):
    fig = go.Figure(data=[go.Pie(labels=['Correct', 'Wrong'], values=[correct, wrong], marker_colors=['#10B981', '#EF4444'], hole=0.3)])
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
    return fig

# ==================================
# VOICE RECORDING
# ==================================

def record_audio():
    st.info("🎙️ Speak your answer (click button and speak)")
    if st.button("🎤 Start Recording", key="voice_record"):
        try:
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            RECORD_SECONDS = 10
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf = wave.open("temp.wav", 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            with open("temp.wav", 'rb') as f:
                audio_bytes = f.read()
            recognizer = sr.Recognizer()
            with sr.AudioFile("temp.wav") as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
            os.remove("temp.wav")
            st.success(f"Recognized: {text}")
            return text
        except Exception as e:
            st.error(f"Error: {e}")
            return ""
    return ""

# ==================================
# CAMERA SCAN
# ==================================

def camera_scan():
    st.info("📸 Take a photo of your answer sheet")
    picture = st.camera_input("Scan your answer", key="camera_scan")
    if picture:
        image = Image.open(picture)
        import pytesseract
        text = pytesseract.image_to_string(image)
        st.success(f"Extracted text: {text[:200]}...")
        return text
    return ""

# ==================================
# HOME PAGE
# ==================================

def home_page():
    st.markdown('<div class="main-header"><h1>🎓 EduEval AI</h1><p>AI-Powered Smart Examination & Evaluation Engine</p></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="card"><h2>✨ Welcome</h2><p>AI-powered exam generation, evaluation, and personalized learning.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stats-card"><div>⚡ AI Evaluation</div><div class="stats-number">500+</div><div>Exams Evaluated</div></div>', unsafe_allow_html=True)
    
    st.markdown("## 👥 Choose Your Role")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👑 Admin Mode", key="home_admin", use_container_width=True):
            st.session_state.nav = "Admin"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 Teacher Mode", key="home_teacher", use_container_width=True):
            st.session_state.nav = "Teacher"
            st.rerun()
    with col3:
        if st.button("👨‍🎓 Student Mode", key="home_student", use_container_width=True):
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
            user = st.text_input("Username", key="admin_user")
        with col2:
            pwd = st.text_input("Password", type="password", key="admin_pwd")
        if st.button("Login", key="admin_login"):
            resp = requests.post(f"{API_URL}/admin/login", json={"username": user, "password": pwd})
            if resp.status_code == 200 and resp.json().get("success"):
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Invalid")
    else:
        st.success("Welcome Admin!")
        if st.button("Logout", key="admin_logout"):
            st.session_state.admin_logged = False
            st.rerun()
        tab1, tab2 = st.tabs(["Pending", "Approved"])
        with tab1:
            resp = requests.get(f"{API_URL}/admin/pending-teachers")
            if resp.status_code == 200:
                for t in resp.json():
                    st.markdown(f'<div class="card"><h3>{t["name"]}</h3><p>Email: {t["email"]}<br>Subject: {t["subject"]}</p></div>', unsafe_allow_html=True)
                    if st.button(f"Approve", key=f"approve_{t['id']}"):
                        requests.post(f"{API_URL}/admin/approve-teacher", json={"teacher_id": t['id'], "status": "APPROVED"})
                        st.rerun()
        with tab2:
            resp = requests.get(f"{API_URL}/admin/approved-teachers")
            if resp.status_code == 200 and resp.json():
                st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)

# ==================================
# TEACHER MODE
# ==================================

def teacher_mode():
    if not st.session_state.get("teacher_logged", False):
        st.markdown('<div class="teacher-card"><h2>👨‍🏫 Teacher Access</h2><p>Login to create exams</p></div>', unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", key="teacher_email")
            with col2:
                pwd = st.text_input("Password", type="password", key="teacher_pwd")
            if st.button("Login", key="teacher_login"):
                resp = requests.post(f"{API_URL}/teacher/login", json={"email": email, "password": pwd})
                if resp.status_code == 200 and resp.json().get("success"):
                    d = resp.json()
                    st.session_state.teacher_logged = True
                    st.session_state.teacher_id = d["teacher_id"]
                    st.session_state.teacher_name = d["name"]
                    st.rerun()
                else:
                    st.error("Login failed")
        with register_tab:
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name", key="reg_name")
                email = st.text_input("Email", key="reg_email")
                subject = st.text_input("Subject", key="reg_subject")
            with col2:
                pwd = st.text_input("Password", type="password", key="reg_pwd")
                confirm = st.text_input("Confirm", type="password", key="reg_confirm")
            if st.button("Register", key="teacher_reg"):
                if pwd == confirm:
                    resp = requests.post(f"{API_URL}/teacher/register", json={"teacher_id": f"T{int(time.time())}", "name": name, "email": email, "password": pwd, "subject": subject})
                    if resp.status_code == 200 and resp.json().get("success"):
                        st.success("Registered! Wait for approval.")
                    else:
                        st.error("Failed")
    else:
        st.markdown(f'<div class="teacher-card"><h3>👋 Welcome, {st.session_state.teacher_name}!</h3></div>', unsafe_allow_html=True)
        if st.button("Logout", key="teacher_logout"):
            st.session_state.teacher_logged = False
            st.rerun()
        
        tabs = st.tabs(["📚 Exams", "📦 Bulk Upload", "📊 Analytics"])
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("Subject", key="exam_subject")
                chapter = st.text_input("Chapter", key="exam_chapter")
                class_lvl = st.selectbox("Class", [str(i) for i in range(1, 13)], key="exam_class")
            with col2:
                duration = st.selectbox("Duration", ["1 hour", "1.5 hours", "2 hours"], key="exam_duration")
                adaptive = st.selectbox("Adaptive Level", ["easy", "standard", "hard"], key="exam_adaptive")
            if st.button("Generate Exam", key="gen_exam"):
                with st.spinner("Generating..."):
                    payload = {"subject": subject, "chapter": chapter, "class_level": class_lvl, "duration": duration, "adaptive_level": adaptive, "partA_bloom": "Remember", "partB_bloom": "Understand", "partC_bloom": "Apply"}
                    resp = requests.post(f"{API_URL}/generate-exam", json=payload, params={"teacher_id": st.session_state.teacher_id})
                    if resp.status_code == 200:
                        st.session_state.generated = resp.json()
                        st.success("Exam generated!")
            if st.session_state.get("generated"):
                st.json(st.session_state.generated["exam"])
                if st.button("Publish Exam", key="publish"):
                    requests.post(f"{API_URL}/publish-exam/{st.session_state.generated['exam_id']}", params={"teacher_id": st.session_state.teacher_id})
                    st.success("Published!")
        
        with tabs[1]:
            st.markdown("### Bulk Upload ZIP")
            exam_id = st.number_input("Exam ID", min_value=1, key="bulk_exam")
            zip_file = st.file_uploader("Choose ZIP", type=["zip"], key="bulk_zip")
            if zip_file and st.button("Upload", key="bulk_upload"):
                files = {"zip_file": zip_file}
                resp = requests.post(f"{API_URL}/bulk-upload", files=files, params={"exam_id": exam_id})
                if resp.status_code == 200:
                    st.success("Uploaded!")
        
        with tabs[2]:
            resp = requests.get(f"{API_URL}/exams")
            if resp.status_code == 200:
                exams = resp.json()
                if exams:
                    selected = st.selectbox("Select Exam", [e['exam_id'] for e in exams])
                    exam_id = [e['id'] for e in exams if e['exam_id'] == selected][0]
                    analytics = requests.get(f"{API_URL}/exam-analytics/{exam_id}").json()
                    col1, col2, col3 = st.columns(3)
                    with col1: st.metric("Students", analytics['total_students'])
                    with col2: st.metric("Avg Score", f"{analytics['average_score']:.1f}%")
                    with col3: st.metric("Highest", f"{analytics['highest_score']}%")

# ==================================
# STUDENT MODE
# ==================================

def student_mode():
    if not st.session_state.get("student_logged", False):
        st.markdown('<div class="student-card"><h2>👨‍🎓 Student Access</h2><p>Login to take exams</p></div>', unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            col1, col2 = st.columns(2)
            with col1:
                sid = st.text_input("Student ID", key="student_id")
            with col2:
                pwd = st.text_input("Password", type="password", key="student_pwd")
            if st.button("Login", key="student_login"):
                resp = requests.post(f"{API_URL}/student/login", json={"student_id": sid, "password": pwd})
                if resp.status_code == 200 and resp.json().get("success"):
                    d = resp.json()
                    st.session_state.student_logged = True
                    st.session_state.student_id = d["student_id"]
                    st.session_state.student_name = d["name"]
                    st.session_state.student_lang = d.get("language", "english")
                    st.rerun()
                else:
                    st.error("Invalid")
        with register_tab:
            col1, col2 = st.columns(2)
            with col1:
                sid = st.text_input("Student ID", key="reg_sid")
                name = st.text_input("Name", key="reg_sname")
                class_lvl = st.selectbox("Class", [str(i) for i in range(1, 13)], key="reg_class")
                lang = st.selectbox("Language", ["english", "tamil", "hindi"], key="reg_lang")
            with col2:
                pwd = st.text_input("Password", type="password", key="reg_spwd")
                confirm = st.text_input("Confirm", type="password", key="reg_sconfirm")
            if st.button("Register", key="student_reg"):
                if pwd == confirm:
                    resp = requests.post(f"{API_URL}/student/register", json={"student_id": sid, "name": name, "password": pwd, "class_level": class_lvl, "language": lang, "section": "A"})
                    if resp.status_code == 200 and resp.json().get("success"):
                        st.success("Registered! Please login.")
                    else:
                        st.error("Failed")
    else:
        st.markdown(f'<div class="student-card"><h3>👋 Welcome, {st.session_state.student_name}!</h3></div>', unsafe_allow_html=True)
        if st.button("Logout", key="student_logout"):
            st.session_state.student_logged = False
            st.rerun()
        
        dashboard = requests.get(f"{API_URL}/student-dashboard/{st.session_state.student_id}").json()
        leaderboard = requests.get(f"{API_URL}/leaderboard").json()
        
        tabs = st.tabs(["📚 Exams", "📈 Performance", "🏆 Leaderboard", "🎓 Certificates", "💼 Career", "🤖 AI Chat"])
        
        with tabs[0]:
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Exams Taken", dashboard['statistics']['total_exams_taken'])
            with col2: st.metric("Streak", dashboard['student'].get('streak_days', 0))
            with col3: st.metric("Badges", len(dashboard['student'].get('badges', [])))
            
            for exam in dashboard["exams"]:
                with st.expander(f"{exam['exam_name']} - {exam['subject']}"):
                    if exam["status"] == "NOT_ATTEMPTED":
                        st.write("Upload your answer sheet")
                        upload_type = st.radio("Input Method", ["Upload File", "Voice Input", "Camera Scan"], horizontal=True, key=f"method_{exam['exam_id']}")
                        answer_text = ""
                        if upload_type == "Upload File":
                            uploaded = st.file_uploader("Choose file", type=["pdf", "jpg", "png"], key=f"file_{exam['exam_id']}")
                            if uploaded:
                                files = {"file": uploaded}
                                with st.spinner("Evaluating..."):
                                    r = requests.post(f"{API_URL}/submit-exam/{st.session_state.student_id}/{exam['exam_id']}", files=files)
                                    if r.status_code == 200:
                                        data = r.json()
                                        st.success(f"Score: {data['score']}")
                                        st.rerun()
                        elif upload_type == "Voice Input":
                            answer_text = record_audio()
                            if answer_text and st.button("Submit Voice Answer", key=f"voice_submit_{exam['exam_id']}"):
                                with st.spinner("Evaluating..."):
                                    r = requests.post(f"{API_URL}/submit-exam/{st.session_state.student_id}/{exam['exam_id']}", files={"file": ("answer.txt", answer_text)})
                                    if r.status_code == 200:
                                        st.success("Submitted!")
                                        st.rerun()
                        else:
                            answer_text = camera_scan()
                            if answer_text and st.button("Submit Scan", key=f"scan_submit_{exam['exam_id']}"):
                                with st.spinner("Evaluating..."):
                                    r = requests.post(f"{API_URL}/submit-exam/{st.session_state.student_id}/{exam['exam_id']}", files={"file": ("answer.txt", answer_text)})
                                    if r.status_code == 200:
                                        st.success("Submitted!")
                                        st.rerun()
                    
                    elif exam.get("submission_id"):
                        if st.button("View Result", key=f"view_{exam['exam_id']}"):
                            result = requests.get(f"{API_URL}/submission-result/{exam['submission_id']}").json()
                            st.markdown(f"### Score: {result['percentage']:.1f}%")
                            st.markdown(f"**{result['total_marks']} / {result['max_marks']} marks**")
                            st.info(f"🤖 Predicted Next Score: {result.get('predicted_next_score', 0):.1f}%")
                            
                            behavior = result.get('behavior_analysis', {})
                            if behavior:
                                st.markdown(f"**Learning Pace:** {behavior.get('learning_pace', 'Average')} | **Consistency:** {behavior.get('consistency', 'Medium')}")
                                for rec in behavior.get('recommendations', [])[:2]:
                                    st.markdown(f"📌 {rec}")
                            
                            if result.get('weak_topics'):
                                st.markdown("### ⚠️ Weak Topics")
                                for t in result['weak_topics'][:3]:
                                    st.markdown(f"- {t}")
                            
                            for q in result['questions'][:3]:
                                with st.expander(f"Q{q['question_number']} - {q['marks_awarded']}/{q['max_marks']}"):
                                    st.write(q['question_text'])
                                    if q.get('ai_explanation'):
                                        st.info(f"💡 {q['ai_explanation'][:200]}...")
                            
                            if st.button("📥 Download Certificate", key=f"cert_{exam['submission_id']}"):
                                cert_resp = requests.get(f"{API_URL}/generate-certificate/{exam['submission_id']}")
                                if cert_resp.status_code == 200:
                                    st.download_button("Save PDF", cert_resp.content, f"certificate_{exam['submission_id']}.pdf", "application/pdf")
        
        with tabs[1]:
            st.markdown("### Performance Analysis")
            scores = []
            labels = []
            for exam in dashboard["exams"]:
                if exam.get("submission_id"):
                    result = requests.get(f"{API_URL}/submission-result/{exam['submission_id']}").json()
                    scores.append(result['percentage'])
                    labels.append(exam['exam_name'][:8])
            if scores:
                st.plotly_chart(performance_trend(scores, labels), use_container_width=True)
                your_score = scores[-1] if scores else 0
                class_avg = leaderboard[0]['average_score'] if leaderboard else 70
                topper = leaderboard[0]['average_score'] if leaderboard else 95
                st.plotly_chart(class_comparison(your_score, class_avg, topper), use_container_width=True)
                
                behavior = requests.get(f"{API_URL}/student-behavior/{st.session_state.student_id}").json()
                if behavior:
                    st.markdown(f"**Total Exams:** {behavior.get('total_exams', 0)} | **Avg Time:** {behavior.get('average_time', 0)}s | **Improvement:** {behavior.get('improvement_rate', 0):.1f}%")
        
        with tabs[2]:
            st.markdown("### 🏆 Leaderboard")
            for i, s in enumerate(leaderboard[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                st.markdown(f"<div class='card'><div style='display:flex;justify-content:space-between'><span><b>{medal}</b> {s['name']}</span><span><b>{s['average_score']}%</b> | {s['exams_taken']} exams</span></div></div>", unsafe_allow_html=True)
        
        with tabs[3]:
            st.markdown("### 🎓 Your Certificates")
            submissions = [e for e in dashboard["exams"] if e.get("submission_id")]
            for s in submissions:
                if st.button(f"Get Certificate - {s['exam_name']}", key=f"cert_btn_{s['exam_id']}"):
                    cert = requests.get(f"{API_URL}/generate-certificate/{s['submission_id']}")
                    if cert.status_code == 200:
                        st.download_button("Download PDF", cert.content, f"certificate_{s['exam_id']}.pdf", "application/pdf")
        
        with tabs[4]:
            st.markdown("### 💼 Career Guidance")
            career = requests.get(f"{API_URL}/career-guidance/{st.session_state.student_id}").json()
            interests = st.text_area("Your career interests", value=career.get('recommendations', ''), height=80)
            if st.button("Get Guidance", key="career_btn"):
                resp = requests.post(f"{API_URL}/career-guidance/{st.session_state.student_id}", data={"career_interests": interests})
                if resp.status_code == 200:
                    st.success("Saved! Check recommendations soon.")
        
        with tabs[5]:
            st.markdown("### 🤖 AI Learning Assistant")
            st.info("Ask me anything about your studies, weak topics, or exam preparation!")
            user_q = st.text_input("Your question:", key="ai_q")
            if st.button("Ask AI", key="ask_ai"):
                with st.spinner("Thinking..."):
                    resp = requests.post(f"{API_URL}/chat", json={"user_id": st.session_state.student_id, "user_type": "student", "message": user_q})
                    if resp.status_code == 200:
                        st.markdown(f"<div class='card'><b>🤖 AI:</b> {resp.json()['response']}</div>", unsafe_allow_html=True)

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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.nav = "Home"
            st.rerun()
    with col2:
        if st.button("👑 Admin", key="nav_admin", use_container_width=True):
            st.session_state.nav = "Admin"
            st.rerun()
    with col3:
        if st.button("👨‍🏫 Teacher", key="nav_teacher", use_container_width=True):
            st.session_state.nav = "Teacher"
            st.rerun()
    with col4:
        if st.button("👨‍🎓 Student", key="nav_student", use_container_width=True):
            st.session_state.nav = "Student"
            st.rerun()
    
    if st.session_state.nav == "Home":
        home_page()
    elif st.session_state.nav == "Admin":
        admin_mode()
    elif st.session_state.nav == "Teacher":
        teacher_mode()
    elif st.session_state.nav == "Student":
        student_mode()
    
    if st.session_state.nav in ["Teacher", "Student"]:
        ai_chatbot()
    
    st.markdown('<div class="footer"><p>© 2024 EduEval AI - Smart Examination & Evaluation Engine</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
