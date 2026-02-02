import streamlit as st
import json
import os
from openai import OpenAI
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# 1. CONFIGURATION & ENTERPRISE CSS
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Фармацевтични грижи",
    layout="wide",
    initial_sidebar_state="expanded"
)

# STRICT CLINICAL CSS OVERRIDE
st.markdown("""
<style>
    /* 1. Global Reset - White & Grey scale */
    .stApp {
        background-color: #f4f6f9; /* Light grey background for contrast */
    }
    
    /* 2. Typography - Standard Enterprise Fonts */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #212529;
    }
    
    /* 3. Header Styling */
    h1, h2, h3 {
        color: #0d3d56; /* Dark Medical Blue */
        font-weight: 600;
        letter-spacing: -0.5px;
    }

    /* 4. Chat Message - Log Style (Not Bubble Style) */
    .stChatMessage {
        background-color: white;
        border-radius: 4px; /* Sharp corners */
        border-left: 4px solid #dee2e6; /* Status bar on left */
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        padding: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Differentiate User (Student) vs Assistant (Patient) via CSS */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        border-left-color: #0056b3; /* Blue for Student */
    }
    div[data-testid="stChatMessage"]:nth-child(even) {
        border-left-color: #28a745; /* Green for Patient */
    }

    /* 5. Inputs & Buttons - Enterprise Flat Design */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 2px;
        border: 1px solid #ced4da;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 2px;
        background-color: #ffffff;
        color: #333;
        border: 1px solid #ccc;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        border-color: #0056b3;
        color: #0056b3;
        background-color: #f8f9fa;
    }

    /* Primary Action Button Style */
    div[data-testid="stHorizontalBlock"] .stButton>button {
         background-color: #0056b3;
         color: white;
         border: none;
    }

    /* 6. Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 7. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 2. HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

def load_patients():
    try:
        patients_file = Path(__file__).parent / "patients.json"
        with open(patients_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fallback for testing without file
        return [{
            "name": "Омар Х.", 
            "age": 65, 
            "scenario_hint": "Пациент със суха кашлица. История на хипертония.", 
            "system_prompt": "Ти си Омар, на 65. Имаш суха кашлица. Не споменаваш, че пиеш лекарства за кръвно, докато не те попитат."
        }]

def get_openai_client():
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        st.error("SYSTEM ERROR: Missing API Configuration.")
        st.stop()
    return OpenAI(api_key=api_key)

def chat_with_patient(client, messages, system_prompt):
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    response = client.chat.completions.create(
        model=get_secret("MODEL_NAME", "gpt-4o"),
        messages=full_messages,
        temperature=0.7,
        max_tokens=800,
    )
    return response.choices[0].message.content

def generate_feedback_structured(client, messages, patient_data):
    """
    Returns feedback separated by '|||' to allow splitting into tabs.
    """
    conversation_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
    
    prompt = f"""
    ROLES: Evaluator is a Clinical Pharmacy Professor. User is a Student.
    TASK: Assess the consultation below.
    OUTPUT FORMAT: Strictly separate sections with "|||". Do not use markdown headers for the section titles, just the content.
    
    Order of sections:
    1. CLINICAL SAFETY & ACCURACY (Text content only)
    2. COMMUNICATION SKILLS (Text content only)
    3. IMPROVEMENT PLAN (Text content only)
    
    CONTEXT:
    Patient: {patient_data['name']}
    Scenario: {patient_data.get('scenario_hint', '')}
    
    TRANSCRIPT:
    {conversation_text}
    """
    
    response = client.chat.completions.create(
        model=get_secret("MODEL_NAME", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ─────────────────────────────────────────────────────────────
# 3. LOGIN SCREEN (MINIMALIST)
# ─────────────────────────────────────────────────────────────

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("### СИСТЕМА ЗА ФАРМАЦЕВТИЧНИ ГРИЖИ")
        st.markdown("---")
        with st.form("login"):
            email = st.text_input("Потребител (Email)")
            code = st.text_input("Код за достъп", type="password")
            if st.form_submit_button("ВХОД В СИСТЕМАТА"):
                # Add validation logic here
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────
# 4. MAIN WORKSPACE
# ─────────────────────────────────────────────────────────────

# State Init
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback_raw" not in st.session_state:
    st.session_state.feedback_raw = ""

patients = load_patients()
client = get_openai_client()

# --- SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.markdown("**ПАНЕЛ ЗА УПРАВЛЕНИЕ**")
    st.markdown("---")
    
    # Patient Selector
    patient_names = [p['name'] for p in patients]
    selected_idx = st.selectbox("Избор на Пациентски Казус", range(len(patients)), format_func=lambda i: patient_names[i])
    selected_patient = patients[selected_idx]
    
    # Reset Logic check
    if "current_patient_id" not in st.session_state or st.session_state.current_patient_id != selected_patient['name']:
        st.session_state.current_patient_id = selected_patient['name']
        st.session_state.messages = []
        st.session_state.feedback_raw = ""
        st.rerun()

    st.markdown("---")
    st.markdown("**ИНФОРМАЦИЯ ЗА КАЗУСА**")
    st.warning(selected_patient.get('scenario_hint', ''))
    
    st.markdown("---")
    if st.button("НОВА СЕСИЯ (ИЗЧИСТВАНЕ)"):
        st.session_state.messages = []
        st.session_state.feedback_raw = ""
        st.rerun()

# --- MAIN AREA ---

st.markdown(f"#### КОНСУЛТАЦИЯ: {selected_patient['name'].upper()}")
st.markdown("---")

# CHAT DISPLAY (LOG STYLE)
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        # Initial Message
        welcome = selected_patient.get("opening_message", "Здравейте.")
        st.session_state.messages.append({"role": "assistant", "content": welcome})

    for msg in st.session_state.messages:
        # Clean rendering without avatars/emojis
        # We use the CSS to distinguish them by border color
        with st.chat_message(msg["role"], avatar=None):
            # Adding a text label to clarify speaker
            speaker = "СТУДЕНТ" if msg["role"] == "user" else "ПАЦИЕНТ"
            st.markdown(f"**{speaker}:** {msg['content']}")

# INPUT AREA
# Only show input if feedback is not generated yet
if not st.session_state.feedback_raw:
    user_input = st.chat_input("Въведете въпрос към пациента...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user", avatar=None):
                st.markdown(f"**СТУДЕНТ:** {user_input}")
        
        with st.spinner("Обработка на отговор..."):
            ai_resp = chat_with_patient(client, st.session_state.messages, selected_patient["system_prompt"])
            st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            st.rerun()

# --- ASSESSMENT MODULE ---
st.markdown("<br>", unsafe_allow_html=True)

if not st.session_state.feedback_raw:
    # Button to trigger assessment
    if len(st.session_state.messages) > 2:
        if st.button("ПРИКЛЮЧВАНЕ И ОЦЕНКА НА КОМУНИКАЦИЯТА"):
            with st.spinner("Генериране на академичен анализ..."):
                fb = generate_feedback_structured(client, st.session_state.messages, selected_patient)
                st.session_state.feedback_raw = fb
                st.rerun()
else:
    # DISPLAY FEEDBACK
    st.markdown("### ОЦЕНКА НА ПРЕДСТАВЯНЕТО")
    
    # Logic to split the response by the separator "|||"
    parts = st.session_state.feedback_raw.split("|||")
    
    # Ensure we have 3 parts, otherwise display raw text
    if len(parts) >= 3:
        tab1, tab2, tab3 = st.tabs(["КЛИНИЧНА БЕЗОПАСНОСТ", "КОМУНИКАЦИЯ", "ПЛАН ЗА ПОДОБРЕНИЕ"])
        
        with tab1:
            st.markdown(parts[0].strip())
        with tab2:
            st.markdown(parts[1].strip())
        with tab3:
            st.markdown(parts[2].strip())
    else:
        st.error("Форматът на анализа не беше разпознат. Показване на суров текст:")
        st.write(st.session_state.feedback_raw)
    
    if st.button("ЗАТВАРЯНЕ НА ДОКЛАДА"):
        st.session_state.feedback_raw = ""
        st.rerun()
