# app.py - Complete Frontend with Real Backend Data, Report Card, Leaderboard, Career Guidance
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

API_URL = "https://edueval-ai.onrender.com"

# ==================================
# CUSTOM CSS STYLING
# ==================================

def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    
    .main .block-container {
        padding: 0.5rem 1rem 1rem 1rem !important;
        max-width: 100% !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 50%, #F59E0B 100%);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .main-header h1 { color: white; font-size: 1.75rem; font-weight: 800; margin: 0; }
    .main-header p { color: rgba(255,255,255,0.95); margin-top: 0.25rem; font-size: 0.8rem; }
    
    .card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        border: 1px solid #E5E7EB;
        transition: all 0.2s ease;
    }
    .card:hover { border-color: #8B5CF6; transform: translateY(-2px); }
    .card h2 { font-size: 1.1rem; margin-bottom: 0.25rem; }
    .card h3 { font-size: 1rem; margin-bottom: 0.25rem; }
    .card p { font-size: 0.8rem; color: #6B7280; }
    
    .stats-card {
        background: #F9FAFB;
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
        border: 1px solid #E5E7EB;
    }
    
    .stats-number {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #8B5CF6, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.25rem 0;
    }
    
    .admin-card, .teacher-card, .student-card {
        border-radius: 12px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        border: 2px solid;
    }
    .admin-card { background: #FEF3C7; border-color: #F59E0B; }
    .teacher-card { background: #EFF6FF; border-color: #8B5CF6; }
    .student-card { background: #F0FDF4; border-color: #10B981; }
    
    .risk-card-low { background: #F0FDF4; border-radius: 10px; padding: 0.5rem; border-left: 3px solid #10B981; font-size: 0.8rem; }
    .risk-card-medium { background: #FFF7ED; border-radius: 10px; padding: 0.5rem; border-left: 3px solid #F59E0B; font-size: 0.8rem; }
    .risk-card-high { background: #FEF2F2; border-radius: 10px; padding: 0.5rem; border-left: 3px solid #EF4444; font-size: 0.8rem; }
    
    .stButton > button {
        background: linear-gradient(135deg, #8B5CF6, #7C3AED) !important;
        color: white !important;
        border: none !important;
        padding: 0.4rem 0.8rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        width: 100% !important;
        font-size: 0.8rem !important;
    }
    
    .footer {
        text-align: center;
        padding: 0.75rem;
        margin-top: 1rem;
        background: #F9FAFB;
        font-size: 0.7rem;
        color: #9CA3AF;
        border-top: 1px solid #E5E7EB;
    }
    
    .floating-ai {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    .chat-toggle-btn {
        background: linear-gradient(135deg, #8B5CF6, #7C3AED);
        border: none;
        border-radius: 50%;
        width: 45px;
        height: 45px;
        font-size: 22px;
        cursor: pointer;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .chat-window {
        position: fixed;
        bottom: 75px;
        right: 20px;
        width: 300px;
        height: 400px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        display: flex;
        flex-direction: column;
        z-index: 999;
        border: 1px solid #E5E7EB;
    }
    .chat-header {
        background: linear-gradient(135deg, #8B5CF6, #7C3AED);
        padding: 8px;
        color: white;
        display: flex;
        justify-content: space-between;
        font-weight: 600;
        font-size: 0.8rem;
        border-radius: 12px 12px 0 0;
    }
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 8px;
        background: #F9FAFB;
        font-size: 0.75rem;
    }
    .chat-input-area {
        padding: 6px;
        border-top: 1px solid #E5E7EB;
        display: flex;
        gap: 5px;
        background: white;
    }
    .chat-input-area input {
        flex: 1;
        padding: 5px 8px;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        font-size: 0.75rem;
    }
    .user-msg { text-align: right; margin: 4px 0; }
    .user-msg div { background: #8B5CF6; color: white; padding: 5px 8px; border-radius: 12px; display: inline-block; max-width: 85%; font-size: 0.75rem; }
    .bot-msg { text-align: left; margin: 4px 0; }
    .bot-msg div { background: white; padding: 5px 8px; border-radius: 12px; border: 1px solid #E5E7EB; display: inline-block; max-width: 85%; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================================
# GRAPH FUNCTIONS
# ==================================

def create_performance_trend(scores, labels):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=scores, mode='lines+markers', name='Your Score',
        line=dict(color='#8B5CF6', width=3), marker=dict(size=10, color='#10B981'),
        fill='tozeroy', fillcolor='rgba(139, 92, 246, 0.1)'
    ))
    fig.update_layout(
        title="Performance Trend", xaxis_title="Exams", yaxis_title="Score (%)",
        yaxis_range=[0, 100], height=350, paper_bgcolor='white', plot_bgcolor='#F9FAFB'
    )
    return fig

def create_class_comparison(your_score, class_avg, topper):
    fig = go.Figure(data=[go.Bar(
        x=['Your Score', 'Class Average', 'Topper'],
        y=[your_score, class_avg, topper],
        marker_color=['#8B5CF6', '#F59E0B', '#10B981'],
        text=[f"{your_score}%", f"{class_avg}%", f"{topper}%"], textposition='auto'
    )])
    fig.update_layout(title="Performance Comparison", yaxis_title="Score (%)", yaxis_range=[0, 100], height=350)
    return fig

def create_question_chart(questions_data):
    q_nums = [q['q_no'] for q in questions_data]
    obtained = [q['marks'] for q in questions_data]
    max_marks = [q['max_marks'] for q in questions_data]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=q_nums, y=obtained, name='Obtained', marker_color='#8B5CF6'))
    fig.add_trace(go.Bar(x=q_nums, y=[m-o for m,o in zip(max_marks, obtained)], name='Lost', marker_color='#EF4444', base=obtained))
    fig.update_layout(title="Question-wise Marks", xaxis_title="Question", yaxis_title="Marks", barmode='stack', height=350)
    return fig

def create_correct_wrong_pie(correct, wrong):
    fig = go.Figure(data=[go.Pie(labels=['Correct', 'Wrong'], values=[correct, wrong], marker_colors=['#10B981', '#EF4444'], hole=0.3)])
    fig.update_layout(title="Correct vs Wrong", height=300)
    return fig

def create_risk_distribution(risk_data):
    fig = go.Figure(data=[go.Pie(labels=list(risk_data.keys()), values=list(risk_data.values()), marker_colors=['#10B981', '#F59E0B', '#EF4444'], hole=0.3)])
    fig.update_layout(title="Risk Distribution", height=350)
    return fig

# ==================================
# PDF GENERATION
# ==================================

def generate_exam_pdf(metadata, exam):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=15)
    elements.append(Paragraph("Examination Paper", title_style))
    elements.append(Spacer(1, 8))
    
    data = [
        ["Exam ID", metadata.get('exam_id', 'N/A')], ["Class", metadata.get('class_level', 'N/A')],
        ["Subject", exam.get('subject', 'N/A')], ["Chapter", exam.get('chapter', 'N/A')],
        ["Duration", exam.get('duration', 'N/A')], ["Total Marks", str(exam.get('total_marks', 49))]
    ]
    table = Table(data, colWidths=[100, 250])
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    parts = exam.get("parts", {})
    for part_name, part_data in parts.items():
        elements.append(Paragraph(part_name, styles["Heading2"]))
        elements.append(Spacer(1, 6))
        for i, q in enumerate(part_data["questions"], 1):
            elements.append(Paragraph(f"{i}. {q['question']}", styles["Normal"]))
            elements.append(Spacer(1, 3))
            if "options" in q:
                for opt in q["options"]:
                    elements.append(Paragraph(f"   {opt}", styles["Normal"]))
                    elements.append(Spacer(1, 2))
            elements.append(Spacer(1, 4))
        elements.append(Spacer(1, 12))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================================
# AI CHATBOT
# ==================================

def ai_chatbot_component():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    
    st.markdown('<div class="floating-ai"><button class="chat-toggle-btn">🤖</button></div>', unsafe_allow_html=True)
    
    if st.button("🤖", key="chat_toggle_main", help="AI Assistant"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()
    
    if st.session_state.chat_open:
        st.markdown('<div class="chat-window"><div class="chat-header"><span>🤖 AI Assistant</span></div><div class="chat-messages">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history[-15:]:
            if msg["type"] == "user":
                st.markdown(f'<div class="user-msg"><div>{msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg"><div>{msg["content"]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
        user_input = st.text_input("", key="chat_input_main", placeholder="Ask me...", label_visibility="collapsed")
        send = st.button("Send", key="chat_send_main")
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        if send and user_input:
            st.session_state.chat_history.append({"type": "user", "content": user_input})
            try:
                user_type = "student" if st.session_state.get("nav_selection") == "Student" else "teacher"
                user_id = st.session_state.get("student_id") if user_type == "student" else st.session_state.get("teacher_id", 1)
                resp = requests.post(f"{API_URL}/chat", json={"user_id": user_id, "user_type": user_type, "message": user_input})
                ai_resp = resp.json().get("response", "I'm here to help!") if resp.status_code == 200 else "Hello! How can I help?"
            except:
                ai_resp = "Hello! I'm your AI Assistant. How can I help you?"
            st.session_state.chat_history.append({"type": "bot", "content": ai_resp})
            st.rerun()

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
        st.markdown("""
        <div class="card">
            <h2>✨ Welcome</h2>
            <p>AI-powered exam generation, evaluation, and personalized learning.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stats-card">
            <div>⚡ AI Evaluation</div>
            <div class="stats-number">500+</div>
            <div>Exams Evaluated</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("## 👥 Choose Your Role")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👑 Admin Mode", key="home_admin_main", use_container_width=True):
            st.session_state.nav_selection = "Admin"
            st.rerun()
    with col2:
        if st.button("👨‍🏫 Teacher Mode", key="home_teacher_main", use_container_width=True):
            st.session_state.nav_selection = "Teacher"
            st.rerun()
    with col3:
        if st.button("👨‍🎓 Student Mode", key="home_student_main", use_container_width=True):
            st.session_state.nav_selection = "Student"
            st.rerun()

# ==================================
# ADMIN MODE
# ==================================

def admin_mode():
    st.markdown('<div class="admin-card"><h2>👑 Admin Dashboard</h2><p>Manage teacher registrations</p></div>', unsafe_allow_html=True)
    
    if not st.session_state.get("admin_logged_in", False):
        col1, col2 = st.columns(2)
        with col1:
            admin_user = st.text_input("Username", key="admin_user_main")
        with col2:
            admin_pass = st.text_input("Password", type="password", key="admin_pass_main")
        
        if st.button("Login as Admin", key="admin_login_main", use_container_width=True):
            resp = requests.post(f"{API_URL}/admin/login", json={"username": admin_user, "password": admin_pass})
            if resp.status_code == 200 and resp.json().get("success"):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        st.success("Welcome, Admin!")
        if st.button("Logout", key="admin_logout_main", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()
        
        tab1, tab2 = st.tabs(["📋 Pending", "✅ Approved"])
        with tab1:
            resp = requests.get(f"{API_URL}/admin/pending-teachers")
            if resp.status_code == 200:
                pending = resp.json()
                if pending:
                    for t in pending:
                        st.markdown(f'<div class="card"><h3>{t["name"]}</h3><p>Email: {t["email"]}<br>Subject: {t["subject"]}</p></div>', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✅ Approve", key=f"admin_approve_{t['id']}"):
                                requests.post(f"{API_URL}/admin/approve-teacher", json={"teacher_id": t['id'], "status": "APPROVED"})
                                st.rerun()
                        with col2:
                            if st.button(f"❌ Reject", key=f"admin_reject_{t['id']}"):
                                requests.post(f"{API_URL}/admin/approve-teacher", json={"teacher_id": t['id'], "status": "REJECTED"})
                                st.rerun()
                else:
                    st.info("No pending approvals")
        with tab2:
            resp = requests.get(f"{API_URL}/admin/approved-teachers")
            if resp.status_code == 200 and resp.json():
                st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)

# ==================================
# TEACHER MODE
# ==================================

def teacher_mode():
    if not st.session_state.get("teacher_logged_in", False):
        st.markdown('<div class="teacher-card"><h2>👨‍🏫 Teacher Access</h2><p>Login to create exams and assignments</p></div>', unsafe_allow_html=True)
        
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", key="teacher_login_email_main")
            with col2:
                pwd = st.text_input("Password", type="password", key="teacher_login_pass_main")
            
            if st.button("Login", key="teacher_login_btn_main", use_container_width=True):
                resp = requests.post(f"{API_URL}/teacher/login", json={"email": email, "password": pwd})
                if resp.status_code == 200 and resp.json().get("success"):
                    d = resp.json()
                    st.session_state.teacher_logged_in = True
                    st.session_state.teacher_id = d["teacher_id"]
                    st.session_state.teacher_name = d["name"]
                    st.session_state.teacher_subject = d.get("subject", "")
                    st.rerun()
                else:
                    st.error("Login failed")
        
        with register_tab:
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", key="teacher_reg_name_main")
                email = st.text_input("Email", key="teacher_reg_email_main")
                subject = st.text_input("Subject", key="teacher_reg_subject_main")
            with col2:
                pwd = st.text_input("Password", type="password", key="teacher_reg_pass_main")
                confirm = st.text_input("Confirm Password", type="password", key="teacher_reg_confirm_main")
            
            if st.button("Register", key="teacher_reg_btn_main", use_container_width=True):
                if pwd == confirm:
                    resp = requests.post(f"{API_URL}/teacher/register", json={
                        "teacher_id": f"T{int(time.time())}", "name": name, "email": email,
                        "password": pwd, "subject": subject
                    })
                    if resp.status_code == 200 and resp.json().get("success"):
                        st.success("Registration successful! Wait for admin approval.")
                    else:
                        st.error("Registration failed")
    else:
        st.markdown(f'<div class="teacher-card"><h3>👋 Welcome, {st.session_state.teacher_name}!</h3><p>Subject: {st.session_state.teacher_subject}</p></div>', unsafe_allow_html=True)
        
        if st.button("Logout", key="teacher_logout_main", use_container_width=True):
            st.session_state.teacher_logged_in = False
            st.rerun()
        
        teacher_tabs = st.tabs(["📚 Exams", "📝 Assignments", "📦 Bulk Upload", "📊 Analytics"])
        
        with teacher_tabs[0]:
            st.markdown("### Create New Exam")
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("Subject", key="exam_subject_main")
                chapter = st.text_input("Chapter", key="exam_chapter_main")
                class_level = st.selectbox("Class", [str(i) for i in range(1, 13)], key="exam_class_main")
            with col2:
                duration = st.selectbox("Duration", ["1 hour", "1.5 hours", "2 hours"], key="exam_duration_main")
                partA = st.selectbox("Part A Level", ["Remember", "Understand", "Apply"], key="exam_parta_main")
                partB = st.selectbox("Part B Level", ["Understand", "Apply", "Analyze"], key="exam_partb_main")
            
            if st.button("Generate Exam", key="generate_exam_main"):
                with st.spinner("AI generating exam..."):
                    payload = {
                        "subject": subject, "chapter": chapter, "class_level": class_level,
                        "duration": duration, "partA_bloom": partA, "partB_bloom": partB, "partC_bloom": partB
                    }
                    resp = requests.post(f"{API_URL}/generate-exam", json=payload, params={"teacher_id": st.session_state.teacher_id})
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.generated_exam = data
                        st.success("Exam generated!")
                    else:
                        st.error("Failed to generate exam")
            
            if st.session_state.get("generated_exam"):
                exam_data = st.session_state.generated_exam
                st.markdown(f"### Exam: {exam_data['metadata']['exam_id']}")
                st.download_button("Download PDF", generate_exam_pdf(exam_data['metadata'], exam_data['exam']), file_name=f"{exam_data['metadata']['exam_id']}.pdf")
                if st.button("Publish Exam", key="publish_exam_main"):
                    resp = requests.post(f"{API_URL}/publish-exam/{exam_data['exam_id']}", params={"teacher_id": st.session_state.teacher_id})
                    if resp.status_code == 200:
                        st.success("Exam published!")
        
        with teacher_tabs[2]:
            st.markdown("### 📦 Bulk Upload Answer Sheets")
            st.info("Upload a ZIP file with folder structure: StudentID/answer.pdf")
            bulk_exam = st.number_input("Exam ID", min_value=1, value=1, key="bulk_exam_main")
            zip_file = st.file_uploader("Choose ZIP file", type=["zip"], key="bulk_zip_main")
            if zip_file and st.button("Process Bulk Upload", key="bulk_process_main"):
                with st.spinner("Processing..."):
                    files = {"zip_file": zip_file}
                    resp = requests.post(f"{API_URL}/bulk-upload", files=files, params={"exam_id": bulk_exam})
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"Processed {len(data.get('results', []))} files")
                        st.dataframe(pd.DataFrame(data.get('results', [])), use_container_width=True)
                    else:
                        st.error("Upload failed")
        
        with teacher_tabs[3]:
            st.markdown("### 📊 Exam Analytics")
            exams_resp = requests.get(f"{API_URL}/exams")
            if exams_resp.status_code == 200:
                exams = exams_resp.json()
                if exams:
                    exam_names = {f"{e['exam_id']} - {e['subject']}": e['id'] for e in exams}
                    selected = st.selectbox("Select Exam", list(exam_names.keys()), key="analytics_exam_main")
                    exam_id = exam_names[selected]
                    analytics = requests.get(f"{API_URL}/exam-analytics/{exam_id}").json()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric("Students", analytics['total_students'])
                    with col2: st.metric("Avg Score", f"{analytics['average_score']:.1f}%")
                    with col3: st.metric("Highest", f"{analytics['highest_score']}%")
                    with col4: st.metric("Lowest", f"{analytics['lowest_score']}%")
                    
                    fig_risk = create_risk_distribution(analytics['risk_distribution'])
                    st.plotly_chart(fig_risk, use_container_width=True)

# ==================================
# STUDENT MODE
# ==================================

def student_mode():
    if not st.session_state.get("student_logged_in", False):
        st.markdown('<div class="student-card"><h2>👨‍🎓 Student Access</h2><p>Login to take exams and track progress</p></div>', unsafe_allow_html=True)
        
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            col1, col2 = st.columns(2)
            with col1:
                sid = st.text_input("Student ID", key="student_login_id_main")
            with col2:
                pwd = st.text_input("Password", type="password", key="student_login_pass_main")
            
            if st.button("Login", key="student_login_btn_main", use_container_width=True):
                resp = requests.post(f"{API_URL}/student/login", json={"student_id": sid, "password": pwd})
                if resp.status_code == 200 and resp.json().get("success"):
                    d = resp.json()
                    st.session_state.student_logged_in = True
                    st.session_state.student_id = d["student_id"]
                    st.session_state.student_name = d["name"]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with register_tab:
            col1, col2 = st.columns(2)
            with col1:
                sid = st.text_input("Student ID", key="student_reg_id_main")
                name = st.text_input("Full Name", key="student_reg_name_main")
                class_lvl = st.selectbox("Class", [str(i) for i in range(1, 13)], key="student_reg_class_main")
            with col2:
                pwd = st.text_input("Password", type="password", key="student_reg_pass_main")
                confirm = st.text_input("Confirm Password", type="password", key="student_reg_confirm_main")
            
            if st.button("Register", key="student_reg_btn_main", use_container_width=True):
                if pwd == confirm:
                    resp = requests.post(f"{API_URL}/student/register", json={
                        "student_id": sid, "name": name, "password": pwd,
                        "class_level": class_lvl, "section": "A"
                    })
                    if resp.status_code == 200 and resp.json().get("success"):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Registration failed")
    else:
        st.markdown(f'<div class="student-card"><h3>👋 Welcome, {st.session_state.student_name}!</h3></div>', unsafe_allow_html=True)
        
        if st.button("Logout", key="student_logout_main", use_container_width=True):
            st.session_state.student_logged_in = False
            st.rerun()
        
        # Fetch real data
        dashboard = requests.get(f"{API_URL}/student-dashboard/{st.session_state.student_id}").json()
        leaderboard = requests.get(f"{API_URL}/leaderboard").json()
        career = requests.get(f"{API_URL}/career-guidance/{st.session_state.student_id}").json()
        
        student_tabs = st.tabs(["📚 Exams", "📈 Performance", "🏆 Leaderboard", "🎓 Achievements", "💼 Career Guidance"])
        
        with student_tabs[0]:
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Exams Taken", dashboard['statistics']['total_exams_taken'])
            with col2: st.metric("Avg Score", f"{dashboard['statistics']['average_score']}%")
            with col3: st.metric("Streak Days", dashboard['student'].get('streak_days', 0))
            
            for exam in dashboard["exams"]:
                with st.expander(f"{exam['exam_name']} - {exam['subject']}"):
                    st.write(f"Duration: {exam['duration']} | Marks: {exam['total_marks']}")
                    if exam["status"] == "NOT_ATTEMPTED":
                        uploaded = st.file_uploader("Upload Answer Sheet", type=["pdf", "jpg", "png"], key=f"upload_{exam['exam_id']}")
                        if uploaded:
                            files = {"file": uploaded}
                            with st.spinner("AI evaluating..."):
                                r = requests.post(f"{API_URL}/submit-exam/{st.session_state.student_id}/{exam['exam_id']}", files=files)
                                if r.status_code == 200:
                                    st.success("Submitted! AI evaluation complete.")
                                    st.rerun()
                    elif exam.get("submission_id"):
                        if st.button("View Result", key=f"view_{exam['exam_id']}"):
                            result = requests.get(f"{API_URL}/submission-result/{exam['submission_id']}").json()
                            st.markdown(f"### Score: {result['percentage']}%")
                            st.markdown(f"**{result['total_marks']} / {result['max_marks']} marks**")
                            if result.get('ai_feedback_summary'):
                                st.info(result['ai_feedback_summary'])
                            
                            # Download Report Card Button
                            if st.button("📥 Download Report Card", key=f"download_report_{exam['submission_id']}"):
                                report_resp = requests.get(f"{API_URL}/generate-report-card/{exam['submission_id']}")
                                if report_resp.status_code == 200:
                                    st.download_button(
                                        label="Save PDF", data=report_resp.content,
                                        file_name=f"report_card_{exam['submission_id']}.pdf", mime="application/pdf"
                                    )
        
        with student_tabs[1]:
            st.markdown("### 📊 Your Performance Analysis")
            
            # Get real performance data from submissions
            scores = []
            labels = []
            for exam in dashboard["exams"]:
                if exam.get("percentage"):
                    scores.append(exam["percentage"])
                    labels.append(exam['exam_name'][:10])
            
            if scores:
                fig_trend = create_performance_trend(scores, labels)
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Class comparison (mock from leaderboard)
                your_score = scores[-1] if scores else 0
                class_avg = leaderboard[0]['average_score'] if leaderboard else 70
                topper_score = leaderboard[0]['average_score'] if leaderboard else 95
                fig_compare = create_class_comparison(your_score, class_avg, topper_score)
                st.plotly_chart(fig_compare, use_container_width=True)
                
                # Mock question data for recent exam
                if dashboard["exams"] and dashboard["exams"][-1].get("submission_id"):
                    result = requests.get(f"{API_URL}/submission-result/{dashboard['exams'][-1]['submission_id']}").json()
                    if result.get("questions"):
                        q_data = [{"q_no": i+1, "marks": q['marks_awarded'], "max_marks": q['max_marks']} for i, q in enumerate(result["questions"])]
                        correct = sum(1 for q in result["questions"] if q['marks_awarded'] >= q['max_marks'] * 0.6)
                        wrong = len(result["questions"]) - correct
                        fig_pie = create_correct_wrong_pie(correct, wrong)
                        st.plotly_chart(fig_pie, use_container_width=True)
                        fig_q = create_question_chart(q_data)
                        st.plotly_chart(fig_q, use_container_width=True)
                        
                        if result.get("weak_topics"):
                            st.markdown("### ⚠️ Areas for Improvement")
                            for topic in result["weak_topics"][:3]:
                                st.markdown(f'<div class="risk-card-medium"><strong>📖 {topic}</strong> - Need more practice</div>', unsafe_allow_html=True)
            else:
                st.info("Complete an exam to see performance analysis")
        
        with student_tabs[2]:
            st.markdown("### 🏆 Leaderboard")
            if leaderboard:
                for i, s in enumerate(leaderboard[:10]):
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    st.markdown(f"""
                    <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
                        <div><span style="font-size: 1.2rem; font-weight: bold;">{medal}</span> {s['name']}</div>
                        <div><strong>{s['average_score']}%</strong> | {s['exams_taken']} exams</div>
                        <div>{' '.join([b.get('icon', '') for b in s['badges'][:3]])}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No leaderboard data yet")
        
        with student_tabs[3]:
            st.markdown("### 🎓 Your Achievements")
            badges = dashboard['student'].get('badges', [])
            if badges:
                for b in badges:
                    st.markdown(f"""
                    <div class="card" style="background: #FEF3C7;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="font-size: 2rem;">{b.get('icon', '🏆')}</div>
                            <div>
                                <strong>{b.get('name', 'Badge')}</strong><br>
                                <small>{b.get('description', '')}</small><br>
                                <small style="color: #6B7280;">Earned: {b.get('earned_at', 'N/A')[:10]}</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Complete exams to earn badges!")
        
        with student_tabs[4]:
            st.markdown("### 💼 Career Guidance")
            st.info("Upload your resume and tell us your interests for personalized career recommendations")
            
            col1, col2 = st.columns(2)
            with col1:
                career_interests = st.text_area("What are your career interests?", height=100, value=career.get('career_interests', '') if career.get('has_data') else "")
                resume_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"], key="resume_career")
            with col2:
                if career.get('has_data'):
                    st.markdown("### Your Skills")
                    for skill in career.get('skills', []):
                        st.markdown(f"✓ {skill}")
                    st.markdown("### Recommendations")
                    st.markdown(career.get('recommendations', ''))
            
            if st.button("Get Career Guidance", key="career_guidance_btn"):
                with st.spinner("Analyzing your profile..."):
                    resume_text = "Sample resume content" if resume_file else None
                    data = {"resume_text": resume_text, "career_interests": career_interests}
                    resp = requests.post(f"{API_URL}/career-guidance/{st.session_state.student_id}", data=data)
                    if resp.status_code == 200:
                        result = resp.json()
                        st.success("Analysis complete!")
                        st.markdown(f"### Your Skills: {', '.join(result.get('skills', []))}")
                        st.markdown(f"### Recommendations: {result.get('recommendations', '')}")
                        st.rerun()

# ==================================
# MAIN
# ==================================

def main():
    if 'nav_selection' not in st.session_state:
        st.session_state.nav_selection = "Home"
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'teacher_logged_in' not in st.session_state:
        st.session_state.teacher_logged_in = False
    if 'student_logged_in' not in st.session_state:
        st.session_state.student_logged_in = False
    
    load_css()
    
    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 Home", key="nav_home_main", use_container_width=True):
            st.session_state.nav_selection = "Home"
            st.rerun()
    with col2:
        if st.button("👑 Admin", key="nav_admin_main", use_container_width=True):
            st.session_state.nav_selection = "Admin"
            st.rerun()
    with col3:
        if st.button("👨‍🏫 Teacher", key="nav_teacher_main", use_container_width=True):
            st.session_state.nav_selection = "Teacher"
            st.session_state.teacher_logged_in = False
            st.rerun()
    with col4:
        if st.button("👨‍🎓 Student", key="nav_student_main", use_container_width=True):
            st.session_state.nav_selection = "Student"
            st.session_state.student_logged_in = False
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.nav_selection == "Home":
        home_page()
    elif st.session_state.nav_selection == "Admin":
        admin_mode()
    elif st.session_state.nav_selection == "Teacher":
        teacher_mode()
    elif st.session_state.nav_selection == "Student":
        student_mode()
    
    if st.session_state.nav_selection in ["Teacher", "Student"]:
        ai_chatbot_component()
    
    st.markdown('<div class="footer"><p>© 2024 EduEval AI - Smart Examination & Evaluation Engine</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
