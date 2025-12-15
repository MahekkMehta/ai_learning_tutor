import streamlit as st
import google.generativeai as genai
import pdfplumber
import sqlite3, json, re, io
from datetime import datetime
from gtts import gTTS
from PIL import Image
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import speech_recognition as sr   # 🔊 VOICE ADDITION

# =====================================================
# APP CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Learning Tutor – Pro",
    page_icon="🧠",
    layout="wide"
)

# =====================================================
# SESSION STATE
# =====================================================
st.session_state.setdefault("dark_mode", False)

DEFAULTS = {
    "doc_text": "",
    "summary": "",
    "questions": [],
    "scores": [],
    "weak_areas": [],
    "ready": False
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# =====================================================
# DYNAMIC THEME + ANIMATIONS (UNCHANGED)
# =====================================================
theme = "dark" if st.session_state.dark_mode else "light"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {"#0f172a" if theme=="dark" else "#f6f8fb"};
    color: {"#e5e7eb" if theme=="dark" else "#111827"};
    transition: all 0.3s ease;
}}

.card {{
    background: {"#1e293b" if theme=="dark" else "white"};
    padding: 1.5rem;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    margin-bottom: 1.5rem;
}}

.metric-card {{
    background: linear-gradient(135deg, #6366f1, #818cf8);
    color: white;
    padding: 1.4rem;
    border-radius: 16px;
    text-align: center;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# GEMINI CONFIG
# =====================================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# =====================================================
# DATABASE
# =====================================================
DB = sqlite3.connect("ai_tutor.db", check_same_thread=False)
CUR = DB.cursor()

CUR.execute("""
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY,
    role TEXT,
    content TEXT,
    ts TEXT
)
""")

CUR.execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY,
    question TEXT,
    answer TEXT,
    score INTEGER,
    strengths TEXT,
    weaknesses TEXT,
    model_answer TEXT
)
""")

CUR.execute("""
CREATE TABLE IF NOT EXISTS image_history (
    id INTEGER PRIMARY KEY,
    image_name TEXT,
    summary TEXT,
    ts TEXT
)
""")

DB.commit()

# =====================================================
# UTILS
# =====================================================
def extract_text(pdf):
    text = ""
    with pdfplumber.open(pdf) as p:
        for page in p.pages:
            if page.extract_text():
                text += page.extract_text() + " "
    return re.sub(r"\s+", " ", text)

def safe_json(txt):
    txt = txt.replace("```json", "").replace("```", "")
    match = re.search(r"(\{.*\}|\[.*\])", txt, re.DOTALL)
    return json.loads(match.group(1)) if match else {}

def speak(text):
    file = "voice.mp3"
    gTTS(text).save(file)
    return file

# 🔊 VOICE ADDITION (UTILITY)
def speech_to_text(audio_bytes):
    r = sr.Recognizer()
    audio = sr.AudioData(audio_bytes, sample_rate=16000, sample_width=2)
    try:
        return r.recognize_google(audio)
    except:
        return ""

# =====================================================
# AI CORE
# =====================================================
def summarize(text):
    return MODEL.generate_content(
        f"Create a clear, structured learning summary:\n{text[:8000]}"
    ).text.strip()

def generate_questions(summary):
    return safe_json(
        MODEL.generate_content(
            f"Generate EXACTLY 5 higher-order questions as JSON array:\n{summary}"
        ).text
    )

def evaluate(question, answer):
    return safe_json(
        MODEL.generate_content(f"""
Return JSON only:
{{
  "score": 0-10,
  "strengths": "",
  "weaknesses": "",
  "model_answer": ""
}}

QUESTION: {question}
ANSWER: {answer}
SUMMARY: {st.session_state.summary}
""").text
    )

def summarize_image(uploaded_file):
    uploaded_file.seek(0)
    image = Image.open(io.BytesIO(uploaded_file.read()))
    response = MODEL.generate_content(
        ["Analyze this image clearly and educationally.", image]
    )
    return response.text.strip()

def tutor_agent(question, mode):
    avg = sum(st.session_state.scores)/len(st.session_state.scores) if st.session_state.scores else 0
    level = "Beginner" if avg < 4 else "Intermediate" if avg < 7 else "Advanced"

    if mode == "Free":
        prompt = f"You are an expert tutor. Level: {level}\n\n{question}"
    else:
        prompt = f"""
You are an adaptive tutor.
Level: {level}

DOCUMENT SUMMARY:
{st.session_state.summary}

QUESTION:
{question}
"""
    return MODEL.generate_content(prompt).text.strip()

# =====================================================
# PDF EXPORT (RESTORED)
# =====================================================
def export_pdf():
    file = "learning_report.pdf"
    doc = SimpleDocTemplate(file, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    avg = round(sum(st.session_state.scores)/len(st.session_state.scores),2) if st.session_state.scores else 0
    content.append(Paragraph("<b>AI Learning Report</b>", styles["Title"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Average Score: {avg}", styles["Normal"]))
    content.append(Spacer(1, 12))

    for r in CUR.execute("SELECT * FROM assessments").fetchall():
        content.append(Paragraph(f"Q: {r[1]}", styles["Normal"]))
        content.append(Paragraph(f"Score: {r[3]}/10", styles["Normal"]))
        content.append(Spacer(1, 8))

    doc.build(content)
    return file

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div style="text-align:center">
<h1>🧠 AI Learning Tutor – Pro</h1>
<p style="opacity:0.8">Multimodal • Adaptive • Persistent</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR (FULLY RESTORED)
# =====================================================
with st.sidebar:
    st.markdown("## ⚙ Control Panel")

    with st.expander("🌗 Appearance", expanded=True):
        st.session_state.dark_mode = st.toggle("Dark Mode", st.session_state.dark_mode)

    with st.expander("📘 Document Learning"):
        pdf = st.file_uploader("Upload PDF", type="pdf")
        if pdf and st.button("Analyze PDF", use_container_width=True):
            st.session_state.doc_text = extract_text(pdf)
            st.session_state.summary = summarize(st.session_state.doc_text)
            st.session_state.questions = generate_questions(st.session_state.summary)
            st.session_state.ready = True
            st.success("PDF analyzed")

    # ✅ IMAGE LEARNING RESTORED
    with st.expander("🖼 Image Learning"):
        img = st.file_uploader("Upload Image", type=["png","jpg","jpeg"])
        if img and st.button("Analyze Image", use_container_width=True):
            img_summary = summarize_image(img)
            CUR.execute(
                "INSERT INTO image_history VALUES (NULL,?,?,?)",
                (img.name, img_summary, datetime.now().isoformat())
            )
            DB.commit()
            st.image(img, use_container_width=True)
            st.write(img_summary)

    # ✅ REPORTS RESTORED
    with st.expander("📄 Reports"):
        if st.button("Export PDF", use_container_width=True):
            st.download_button(
                "Download",
                open(export_pdf(), "rb"),
                file_name="learning_report.pdf",
                use_container_width=True
            )

# =====================================================
# TABS
# =====================================================
tabs = st.tabs(["📘 Learn", "💬 Tutor", "📝 Assessment", "📊 Dashboard", "🕘 History"])

# ---------------- LEARN ----------------
with tabs[0]:
    if st.session_state.ready:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Document Summary")
        st.write(st.session_state.summary)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- ASSESSMENT (VOICE ENABLED)
with tabs[2]:
    if st.session_state.ready:
        for i, q in enumerate(st.session_state.questions, 1):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### Question {i}")
            st.write(q)

            a = st.text_area("Your Answer", key=f"a{i}")

            # 🔊 VOICE INPUT
            audio = st.audio_input("🎙️ Speak your answer", key=f"mic{i}")
            if audio:
                spoken = speech_to_text(audio.getvalue())
                st.info(spoken)
                a = a + " " + spoken

            if st.button("Evaluate", key=f"e{i}", use_container_width=True):
                r = evaluate(q, a)
                st.session_state.scores.append(r["score"])
                st.success(f"Score: {r['score']}/10")

            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- DASHBOARD ----------------
with tabs[3]:
    avg = round(sum(st.session_state.scores)/len(st.session_state.scores),2) if st.session_state.scores else 0
    col1, col2, col3 = st.columns(3)

    col1.markdown(f'<div class="metric-card"><h2>{avg}</h2>Average Score</div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card"><h2>{len(st.session_state.scores)}</h2>Attempts</div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-card"><h2>{len(set(st.session_state.weak_areas))}</h2>Weak Areas</div>', unsafe_allow_html=True)

# ---------------- HISTORY ----------------
with tabs[4]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Chat History")
    for r,c,_ in CUR.execute("SELECT role, content, ts FROM chat ORDER BY id DESC LIMIT 10"):
        st.markdown(f"**{r}:** {c}")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("© AI Learning Tutor – Pro")

# ---------------- TUTOR ----------------
with tabs[1]:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Ask the Tutor")

    mode = st.radio(
        "Tutor Mode",
        ["Free", "From Document"],
        horizontal=True
    )

    question = st.text_area("Ask your question")

    if st.button("Get Answer", use_container_width=True):
        if question.strip():
            reply = tutor_agent(question, mode)
            st.markdown("#### Tutor Response")
            st.write(reply)

            CUR.execute(
                "INSERT INTO chat VALUES (NULL,?,?,?)",
                ("User", question, datetime.now().isoformat())
            )
            CUR.execute(
                "INSERT INTO chat VALUES (NULL,?,?,?)",
                ("Tutor", reply, datetime.now().isoformat())
            )
            DB.commit()
        else:
            st.warning("Please enter a question.")

    st.markdown('</div>', unsafe_allow_html=True)
