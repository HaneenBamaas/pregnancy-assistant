__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="مساعد الحمل الذكي | AI Pregnancy Assistant",
    page_icon="🤰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');
:root {
    --rose: #C2657A; --rose-lt: #F2D6DC; --sage: #7A9E8E;
    --warm: #8B6F6F; --text: #2C1F1F; --border: #E8D5D5;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; }
[data-testid="stSidebar"] { background: linear-gradient(160deg, #FDF0F3 0%, #F0EBF8 100%); }
.app-header {
    background: linear-gradient(135deg, #C2657A 0%, #9B4E8E 60%, #7A9E8E 100%);
    border-radius: 20px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
}
.app-header h1 { font-family: 'DM Serif Display', serif; color: white; font-size: 2rem; margin: 0; }
.app-header p  { color: rgba(255,255,255,0.85); font-size: 1rem; margin: 0.4rem 0 0; font-family: 'Amiri', serif; }
.lang-badge {
    display: inline-block; background: rgba(255,255,255,0.2); color: white;
    border-radius: 20px; padding: 0.2rem 0.8rem; font-size: 0.8rem; margin-top: 0.6rem;
}
.msg-row { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem; }
.msg-row.user { flex-direction: row-reverse; }
.avatar {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0;
}
.avatar.bot  { background: linear-gradient(135deg, #C2657A, #9B4E8E); }
.avatar.user { background: linear-gradient(135deg, #7A9E8E, #4E8E7A); }
.bubble { max-width: 72%; padding: 0.9rem 1.2rem; border-radius: 18px; font-size: 0.97rem; line-height: 1.65; }
.bubble.bot  { background: white; border: 1px solid #E8D5D5; border-top-left-radius: 4px; color: #2C1F1F; }
.bubble.user { background: linear-gradient(135deg, #7A9E8E, #4E8E7A); color: white; border-top-right-radius: 4px; }
.bubble[dir="rtl"] { font-family: 'Amiri', serif; font-size: 1.05rem; }
.stButton > button {
    background: linear-gradient(135deg, #C2657A, #9B4E8E) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
}
.status-ok  { color: #2E7D32; background: #E8F5E9; border-radius: 8px; padding: 0.3rem 0.8rem; font-size: 0.85rem; }
.status-err { color: #C62828; background: #FFEBEE; border-radius: 8px; padding: 0.3rem 0.8rem; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def detect_language(text):
    ar = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    en = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    return "ar" if ar > en else "en"


def render_message(role, content):
    lang = detect_language(content)
    direction = "rtl" if lang == "ar" else "ltr"
    emoji = "🤰" if role == "assistant" else "👤"
    bubble = "bot" if role == "assistant" else "user"
    avatar = "bot" if role == "assistant" else "user"

    st.markdown(f"""
    <div class="msg-row {'user' if role=='user' else ''}">
        <div class="avatar {avatar}">{emoji}</div>
        <div class="bubble {bubble}" dir="{direction}">{content}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Load QA chain ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_qa_chain(api_key, db_path):
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

    db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )

    prompt_template = """
You are a specialized, compassionate medical assistant for pregnancy care.

LANGUAGE RULES:
- If the question contains Arabic, respond ENTIRELY in Arabic.
- If the question is in English, respond ENTIRELY in English.
- Never mix languages.

GUIDELINES:
1. Use ONLY information from the provided documents.
2. If symptoms sound severe, advise seeing a doctor immediately.
3. Be warm, kind, and professional.
4. If info not in documents, advise consulting a doctor.
5. Patient safety is top priority.

Context: {context}
Question: {question}
Answer:
"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
        validate_template=False
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=False
    )


# ── Process question ──────────────────────────────────────────────────────────
def process_question(question):
    if not st.session_state["system_ready"]:
        st.warning("⚠️ Please load the system first.")
        return

    st.session_state["messages"].append({
        "role": "user",
        "content": question
    })

    with st.spinner("🤔 Thinking..."):
        try:
            result = st.session_state["qa_chain"].invoke({"query": question})
            answer = result["result"] if isinstance(result, dict) else str(result)

            lang = detect_language(answer)

            disclaimer = (
                "\n\n⚠️ *هذه المعلومات للتوعية فقط. استشيري طبيبك دائماً.*"
                if lang == "ar"
                else "\n\n⚠️ *For informational purposes only. Always consult your doctor.*"
            )

            st.session_state["messages"].append({
                "role": "assistant",
                "content": answer + disclaimer
            })

        except Exception as e:
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"❌ Error: {e}"
            })


# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "system_ready" not in st.session_state:
    st.session_state["system_ready"] = False

if "qa_chain" not in st.session_state:
    st.session_state["qa_chain"] = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings / الإعدادات")
    st.markdown("---")

    # Secure API key from Streamlit secrets
    api_key_input = st.secrets["GOOGLE_API_KEY"]

    # Correct ChromaDB path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "chroma_db")

    # Debug info
    st.write("📂 DB Path:", db_path)
    st.write("✅ Exists:", os.path.exists(db_path))

    load_clicked = st.button("🚀 Load System", use_container_width=True)

    st.markdown("---")
    st.markdown("### 📖 Sample Questions")

    st.markdown("**English:**")

    for q in [
        "What vitamins should I take?",
        "Is coffee safe during pregnancy?",
        "What are common pregnancy symptoms?",
        "Exercise tips for pregnant women?"
    ]:
        if st.button(q, key=f"en_{q}", use_container_width=True):
            st.session_state["prefill"] = q

    st.markdown("**العربية:**")

    for q in [
        "ما أعراض الحمل الشائعة؟",
        "هل القهوة آمنة أثناء الحمل؟",
        "ما الفيتامينات التي يجب تناولها؟",
        "نصائح للرياضة أثناء الحمل"
    ]:
        if st.button(q, key=f"ar_{q}", use_container_width=True):
            st.session_state["prefill"] = q

    st.markdown("---")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    st.markdown("""
    <div style='font-size:0.75rem; color:#9E8585; margin-top:1rem;'>
    ⚠️ For informational purposes only.<br>
    Always consult your doctor.<br><br>
    للمعلومات فقط. استشيري طبيبك دائماً.
    </div>
    """, unsafe_allow_html=True)


# ── Load system ───────────────────────────────────────────────────────────────
if load_clicked:
    if not os.path.exists(db_path):
        st.error(f"⚠️ chroma_db folder not found at: {db_path}")
    else:
        with st.spinner("⏳ Loading AI system — please wait 1-2 minutes..."):
            try:
                qa = load_qa_chain(api_key_input, db_path)
                st.session_state["qa_chain"] = qa
                st.session_state["system_ready"] = True
                st.success("✅ System loaded! Ask in Arabic or English.")

            except Exception as e:
                st.error(f"❌ Error: {e}")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🤰 AI Pregnancy Care Assistant</h1>
    <p>مساعدة الحمل الذكية — رعاية شاملة بلغتك</p>
    <span class="lang-badge">🇸🇦 عربي</span>
    <span class="lang-badge">🇺🇸 English</span>
</div>
""", unsafe_allow_html=True)


# Status
col1, col2 = st.columns([3, 1])

with col2:
    if st.session_state["system_ready"]:
        st.markdown(
            '<span class="status-ok">✅ Ready</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="status-err">⏸ Not Loaded</span>',
            unsafe_allow_html=True
        )


# ── Chat ──────────────────────────────────────────────────────────────────────
if not st.session_state["messages"]:
    st.markdown("""
    <div style='text-align:center; padding:2rem 0; color:#9E8585;'>
        <div style='font-size:3rem;'>🤰</div>
        <p style='font-size:1.1rem; color:#C2657A;'>
            Welcome! Ask me anything about pregnancy.
        </p>
        <p style='font-family:"Amiri",serif; font-size:1.1rem;'>
            أهلاً! اسأليني أي سؤال عن الحمل.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    for msg in st.session_state["messages"]:
        render_message(msg["role"], msg["content"])


# ── Auto-process sidebar clicks ───────────────────────────────────────────────
if st.session_state.get("prefill"):
    auto_q = st.session_state.pop("prefill")
    process_question(auto_q)
    st.rerun()


# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown("---")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Question",
        placeholder="Type your question in Arabic or English... / اكتبي سؤالك بالعربي أو الإنجليزي...",
        height=90,
        label_visibility="collapsed"
    )

    col_a, col_b = st.columns([5, 1])

    with col_b:
        submitted = st.form_submit_button(
            "➤ Send",
            use_container_width=True
        )


if submitted and user_input.strip():
    process_question(user_input.strip())
    st.rerun()

