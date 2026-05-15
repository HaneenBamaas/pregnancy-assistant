import streamlit as st
import os
import warnings
import zipfile
import requests
warnings.filterwarnings('ignore')

# ── Auto-download chroma_db from Google Drive ─────────────────────────────────
GDRIVE_FILE_ID = "1xRTyiExd-l2-XRiw97X7ojGEdsPnkggi"
DB_ZIP_PATH    = "chroma_db.zip"
DB_FOLDER_PATH = "chroma_db"

def download_from_gdrive(file_id, dest):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={"id": file_id}, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
    if token:
        response = session.get(URL, params={"id": file_id, "confirm": token}, stream=True)
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

def ensure_db():
    if not os.path.exists(DB_FOLDER_PATH):
        if not os.path.exists(DB_ZIP_PATH):
            with st.status("📥 Downloading database (first time only)...", expanded=True) as status:
                st.write("⏳ This may take 1-3 minutes...")
                try:
                    download_from_gdrive(GDRIVE_FILE_ID, DB_ZIP_PATH)
                    st.write("✅ Download complete! Extracting...")
                    with zipfile.ZipFile(DB_ZIP_PATH, 'r') as z:
                        z.extractall(".")
                    st.write("✅ Database ready!")
                    status.update(label="✅ Database loaded!", state="complete")
                except Exception as e:
                    status.update(label=f"❌ Download failed: {e}", state="error")
                    st.stop()
        else:
            with st.spinner("📦 Extracting database..."):
                with zipfile.ZipFile(DB_ZIP_PATH, 'r') as z:
                    z.extractall(".")

ensure_db()


# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="مساعد الحمل الذكي | AI Pregnancy Assistant",
    page_icon="🤰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset & Root */
:root {
    --rose:     #C2657A;
    --rose-lt:  #F2D6DC;
    --blush:    #FAF0F2;
    --sage:     #7A9E8E;
    --sage-lt:  #D4EAE2;
    --cream:    #FDF8F5;
    --warm:     #8B6F6F;
    --text:     #2C1F1F;
    --muted:    #9E8585;
    --border:   #E8D5D5;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #FDF0F3 0%, #F0EBF8 100%);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'DM Serif Display', serif;
    color: var(--rose);
}

/* ── Header ── */
.app-header {
    background: linear-gradient(135deg, #C2657A 0%, #9B4E8E 60%, #7A9E8E 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}
.app-header h1 {
    font-family: 'DM Serif Display', serif;
    color: white;
    font-size: 2rem;
    margin: 0;
    line-height: 1.2;
}
.app-header p {
    color: rgba(255,255,255,0.85);
    font-size: 1rem;
    margin: 0.4rem 0 0;
    font-family: 'Amiri', serif;
}
.lang-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    color: white;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
    margin-top: 0.6rem;
}

/* ── Chat bubbles ── */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 0.5rem 0 1rem;
}
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.avatar.bot  { background: linear-gradient(135deg, var(--rose), #9B4E8E); }
.avatar.user { background: linear-gradient(135deg, var(--sage), #4E8E7A); }

.bubble {
    max-width: 72%;
    padding: 0.9rem 1.2rem;
    border-radius: 18px;
    font-size: 0.97rem;
    line-height: 1.65;
    word-wrap: break-word;
}
.bubble.bot {
    background: white;
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
    color: var(--text);
    box-shadow: 0 2px 12px rgba(194,101,122,0.08);
}
.bubble.user {
    background: linear-gradient(135deg, var(--sage) 0%, #4E8E7A 100%);
    color: white;
    border-top-right-radius: 4px;
}
.bubble[dir="rtl"] { font-family: 'Amiri', serif; font-size: 1.05rem; }

/* ── Disclaimer ── */
.disclaimer {
    background: var(--rose-lt);
    border-left: 3px solid var(--rose);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    font-size: 0.82rem;
    color: var(--warm);
    margin-top: 0.5rem;
}

/* ── Input area ── */
.stTextArea textarea {
    border: 1.5px solid var(--border) !important;
    border-radius: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    resize: none !important;
    background: white !important;
    color: var(--text) !important;
}
.stTextArea textarea:focus {
    border-color: var(--rose) !important;
    box-shadow: 0 0 0 3px rgba(194,101,122,0.12) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--rose), #9B4E8E) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.5rem 1.5rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Status pills */
.status-ok  { color: #2E7D32; background: #E8F5E9; border-radius: 8px; padding: 0.3rem 0.8rem; font-size:0.85rem; }
.status-err { color: #C62828; background: #FFEBEE; border-radius: 8px; padding: 0.3rem 0.8rem; font-size:0.85rem; }

/* Sample questions */
.sample-btn {
    background: var(--blush);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.5rem 0.9rem;
    font-size: 0.83rem;
    color: var(--warm);
    cursor: pointer;
    transition: all 0.2s;
    margin: 0.2rem;
    display: inline-block;
}
.sample-btn:hover { background: var(--rose-lt); border-color: var(--rose); }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    ar = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    en = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    if ar > en:
        return "ar"
    return "en"

def render_message(role: str, content: str):
    lang = detect_language(content)
    direction = "rtl" if lang == "ar" else "ltr"
    avatar_emoji = "🤰" if role == "assistant" else "👤"
    avatar_class = "bot" if role == "assistant" else "user"
    bubble_class = "bot" if role == "assistant" else "user"

    st.markdown(f"""
    <div class="msg-row {'user' if role=='user' else ''}">
        <div class="avatar {avatar_class}">{avatar_emoji}</div>
        <div class="bubble {bubble_class}" dir="{direction}">{content}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Backend loader ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_qa_chain(api_key: str, db_path: str):
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    db = Chroma(persist_directory=db_path, embedding_function=embeddings)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )

    prompt_template = """
You are a specialized, compassionate medical assistant for pregnancy care.

LANGUAGE RULES (STRICTLY FOLLOW):
- If the question contains Arabic text, respond ENTIRELY in Arabic (فصحى).
- If the question is in English, respond ENTIRELY in English.
- Never mix languages in one response.

GUIDELINES:
1. Use ONLY information from the provided documents.
2. If symptoms sound severe, advise seeing a doctor immediately.
3. Be warm, kind, and professional.
4. If the information is not in the documents, advise consulting a doctor.
5. Patient safety is the top priority.
6. Keep answers concise (3-5 sentences for simple questions, more for detailed ones).

Context: {context}
Question: {question}

Answer (same language as question):
"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
        validate_template=False
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=False
    )
    return qa

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ الإعدادات / Settings")
    st.markdown("---")

    # API Key
    api_key_input = st.text_input(
        "🔑 Google Gemini API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", "AIzaSyCqcBdkZGYVHHS2AojJsBsXv5Xhe6Be66Y"),
        placeholder="AIza..."
    )

    # Vector DB path — always use local chroma_db (auto-downloaded)
    db_path = "chroma_db"
    st.info("📂 Database: auto-managed from Google Drive")

    # Load button
    load_clicked = st.button("🚀 Load System", use_container_width=True)

    st.markdown("---")
    st.markdown("### 📖 Sample Questions")
    st.markdown("**English:**")

    sample_en = [
        "What vitamins should I take?",
        "Is coffee safe during pregnancy?",
        "What are common pregnancy symptoms?",
        "Exercise tips for pregnant women?"
    ]
    sample_ar = [
        "ما أعراض الحمل الشائعة؟",
        "هل القهوة آمنة أثناء الحمل؟",
        "ما الفيتامينات التي يجب تناولها؟",
        "نصائح للرياضة أثناء الحمل"
    ]

    for q in sample_en:
        if st.button(q, key=f"en_{q}", use_container_width=True):
            st.session_state["prefill"] = q

    st.markdown("**العربية:**")
    for q in sample_ar:
        if st.button(q, key=f"ar_{q}", use_container_width=True):
            st.session_state["prefill"] = q

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    st.markdown("""
    <div style='font-size:0.75rem; color:#9E8585; margin-top:1rem;'>
    ⚠️ This assistant is informational only.<br>
    Always consult your healthcare provider.<br><br>
    هذا المساعد للمعلومات فقط.<br>
    استشيري طبيبك دائماً.
    </div>
    """, unsafe_allow_html=True)

# ── Main Area ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🤰 AI Pregnancy Care Assistant</h1>
    <p>مساعدة الحمل الذكية — رعاية شاملة بلغتك</p>
    <span class="lang-badge">🇸🇦 عربي</span>
    <span class="lang-badge">🇺🇸 English</span>
</div>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "system_ready" not in st.session_state:
    st.session_state["system_ready"] = False
if "qa_chain" not in st.session_state:
    st.session_state["qa_chain"] = None

# Load system when button clicked
if load_clicked:
    if not api_key_input:
        st.error("⚠️ Please enter your Gemini API Key.")
    elif not os.path.exists(db_path):
        st.error(f"⚠️ Vector DB not found. Please refresh the page and wait for the database to download.")
    else:
        with st.spinner("⏳ Loading AI system — this may take 1-2 minutes on first run..."):
            try:
                qa = load_qa_chain(api_key_input, db_path)
                st.session_state["qa_chain"] = qa
                st.session_state["system_ready"] = True
                st.success("✅ System loaded! You can now ask questions in Arabic or English.")
            except Exception as e:
                st.error(f"❌ Error loading system: {e}")

# Status indicator
col1, col2 = st.columns([3, 1])
with col2:
    if st.session_state["system_ready"]:
        st.markdown('<span class="status-ok">✅ System Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-err">⏸ Not Loaded</span>', unsafe_allow_html=True)

# ── Chat area ──────────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state["messages"]:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0; color: #9E8585;'>
            <div style='font-size:3rem;'>🤰</div>
            <p style='font-family: "DM Serif Display", serif; font-size:1.1rem; color:#C2657A;'>
                Welcome! Ask me anything about pregnancy.
            </p>
            <p style='font-family: "Amiri", serif; font-size:1.1rem;'>
                أهلاً! اسأليني أي سؤال عن الحمل والأمومة.
            </p>
            <p style='font-size:0.85rem;'>← Use the sample questions in the sidebar to get started</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state["messages"]:
            render_message(msg["role"], msg["content"])


# ── Process question helper ────────────────────────────────────────────────────
def process_question(question: str):
    if not st.session_state["system_ready"]:
        st.warning("⚠️ Please load the system first using the sidebar.")
        return
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.spinner("🤔 Thinking..."):
        try:
            result = st.session_state["qa_chain"].invoke({"query": question})
            answer = result["result"] if isinstance(result, dict) else str(result)
            lang = detect_language(answer)
            if lang == "ar":
                disclaimer = "\n\n⚠️ *هذه المعلومات للتوعية فقط. يُرجى استشارة طبيبك دائماً.*"
            else:
                disclaimer = "\n\n⚠️ *This is for informational purposes only. Always consult your doctor.*"
            st.session_state["messages"].append({"role": "assistant", "content": answer + disclaimer})
        except Exception as e:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"❌ Error: {e}\n\nPlease check your API key and try again."
            })

# Auto-process sidebar sample question clicks
if st.session_state.get("prefill"):
    auto_q = st.session_state.pop("prefill")
    process_question(auto_q)
    st.rerun()

# ── Input area ─────────────────────────────────────────────────────────────────
st.markdown("---")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your question / سؤالك",
        placeholder="Type your question in Arabic or English... / اكتبي سؤالك بالعربي أو الإنجليزي...",
        height=90,
        label_visibility="collapsed"
    )
    col_a, col_b = st.columns([5, 1])
    with col_b:
        submitted = st.form_submit_button("➤ Send", use_container_width=True)

if submitted and user_input.strip():
    process_question(user_input.strip())
    st.rerun()
