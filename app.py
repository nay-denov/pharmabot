"""
Pharmacy Communication Training System
Streamlit + OpenAI API
"""

import streamlit as st
import json
import os
from openai import OpenAI
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Фармацевтични грижи — Комуникационен тренинг",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# CLINICAL UI — Full CSS Override
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import professional font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ── */
    .stApp {
        background-color: #f8f9fb;
    }
    html, body, [class*="css"], .stMarkdown, .stMarkdown p,
    .stSelectbox label, .stTextInput label {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #1a1a2e;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    /* ── Typography ── */
    h1 { font-size: 1.5rem !important; font-weight: 700 !important; color: #0f2b46 !important; letter-spacing: -0.3px; }
    h2 { font-size: 1.25rem !important; font-weight: 600 !important; color: #0f2b46 !important; }
    h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #1a3a5c !important; }
    h4 { font-size: 1rem !important; font-weight: 600 !important; color: #1a3a5c !important; }
    p, li { font-size: 0.925rem; line-height: 1.65; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #0f2b46;
        border-right: none;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #c8d6e5 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label {
        color: #8fa8c4 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
    }

    /* ── Sidebar buttons ── */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255,255,255,0.06);
        color: #c8d6e5;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.8rem;
        padding: 0.55rem 1rem;
        width: 100%;
        transition: all 0.15s ease;
        text-transform: none;
        letter-spacing: 0;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255,255,255,0.12);
        border-color: rgba(255,255,255,0.25);
        color: #ffffff;
    }

    /* ── Sidebar alert box (scenario hint) ── */
    section[data-testid="stSidebar"] .stAlert {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #c8d6e5;
        border-radius: 6px;
    }
    section[data-testid="stSidebar"] .stAlert p {
        color: #c8d6e5 !important;
        font-size: 0.85rem;
    }

    /* ── Chat messages ── */
    .stChatMessage {
        background-color: #ffffff;
        border: 1px solid #e8ecf1;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }

    /* ── Chat input ── */
    .stChatInput {
        border-color: #d0d7de;
    }
    .stChatInput textarea {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.925rem !important;
    }

    /* ── Main content buttons ── */
    .main .stButton > button {
        background-color: #0f2b46;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.85rem;
        padding: 0.6rem 1.5rem;
        transition: all 0.15s ease;
    }
    .main .stButton > button:hover {
        background-color: #1a3a5c;
        color: #ffffff;
    }
    .main .stButton > button:active {
        background-color: #0a1f33;
    }

    /* ── Tabs (feedback) ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #f0f2f5;
        border-radius: 8px;
        padding: 3px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 0.5rem 1.25rem;
        font-size: 0.8rem;
        font-weight: 500;
        color: #555;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f2b46 !important;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* ── Form inputs ── */
    .stTextInput input {
        border-radius: 6px;
        border: 1px solid #d0d7de;
        padding: 0.6rem 0.85rem;
        font-size: 0.9rem;
        background: #ffffff;
    }
    .stTextInput input:focus {
        border-color: #0f2b46;
        box-shadow: 0 0 0 2px rgba(15,43,70,0.1);
    }

    /* ── Form submit button ── */
    .stFormSubmitButton > button {
        background-color: #0f2b46 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.65rem 2rem !important;
        font-size: 0.9rem !important;
        width: 100%;
    }
    .stFormSubmitButton > button:hover {
        background-color: #1a3a5c !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: #0f2b46 !important;
    }

    /* ── Selectbox dropdown ── */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 6px;
    }

    /* ── Login card ── */
    .login-card {
        background: #ffffff;
        border: 1px solid #e0e4ea;
        border-radius: 12px;
        padding: 2.5rem 2rem 1rem 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        max-width: 420px;
        margin: 0 auto;
    }
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .login-header h2 {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #0f2b46 !important;
        margin-bottom: 0.25rem;
    }
    .login-header p {
        color: #6b7c93;
        font-size: 0.85rem;
        margin: 0;
    }
    .login-logo {
        width: 48px;
        height: 48px;
        background: #0f2b46;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        color: white;
        font-weight: 700;
        font-size: 1.2rem;
    }

    /* ── Feedback panel ── */
    .feedback-header {
        background: #f0f2f5;
        border: 1px solid #e0e4ea;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .feedback-header h3 {
        margin: 0 0 0.15rem 0;
        font-size: 0.95rem !important;
    }
    .feedback-header p {
        margin: 0;
        color: #6b7c93;
        font-size: 0.8rem;
    }

    /* ── Divider override ── */
    hr {
        border: none;
        border-top: 1px solid #e8ecf1;
        margin: 1rem 0;
    }

    /* ── Caption ── */
    .stCaption, small {
        color: #8896a6 !important;
        font-size: 0.78rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def load_patients():
    patients_file = Path(__file__).parent / "patients.json"
    with open(patients_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_students():
    students_file = Path(__file__).parent / "students.txt"
    try:
        with open(students_file, "r", encoding="utf-8") as f:
            return [
                line.strip().lower()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []


def check_login(email, course_code):
    correct_code = get_secret("COURSE_CODE", "pharma2025")
    if course_code != correct_code:
        return False, "Невалиден код за достъп."

    students = load_students()
    if not students:
        return True, ""

    if email.lower().strip() in students:
        return True, ""
    else:
        return False, "Този имейл не е регистриран в системата."


def get_openai_client():
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        st.error("Системна грешка: Липсва API конфигурация. Свържете се с администратора.")
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


def generate_feedback(client, messages, patient_data):
    conversation_text = "\n".join([
        f"{'ФАРМАЦЕВТ' if m['role'] == 'user' else 'ПАЦИЕНТ'}: {m['content']}"
        for m in messages
    ])

    feedback_prompt = patient_data.get("feedback_prompt", DEFAULT_FEEDBACK_PROMPT)

    prompt = f"""{feedback_prompt}

---
ИНФОРМАЦИЯ ЗА ПАЦИЕНТА:
Име: {patient_data['name']}
Възраст: {patient_data.get('age', 'неизвестна')}
Описание: {patient_data.get('description', '')}
Ключова информация: {patient_data.get('key_info', '')}

---
ТРАНСКРИПТ НА КОНСУЛТАЦИЯТА:

{conversation_text}

---
ВАЖНО: Обратната връзка трябва да е на БЪЛГАРСКИ език.
Отговорът трябва да съдържа точно 3 секции, разделени с |||
Не слагай заглавие на секция преди съдържанието.

Секция 1: Клинична оценка (правилност на решенията, безопасност)
|||
Секция 2: Комуникативни умения (въпроси, емпатия, структура)
|||
Секция 3: Препоръки за подобрение (конкретен план)
"""

    response = client.chat.completions.create(
        model=get_secret("MODEL_NAME", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3000,
    )
    return response.choices[0].message.content


def save_conversation(email, patient_name, messages, feedback=""):
    history_dir = Path(__file__).parent / "history"
    history_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_email = email.replace("@", "_at_").replace(".", "_")
    safe_patient = patient_name.replace(" ", "_")
    filename = f"{safe_email}_{safe_patient}_{timestamp}.json"

    record = {
        "student_email": email,
        "patient": patient_name,
        "timestamp": datetime.now().isoformat(),
        "messages": messages,
        "feedback": feedback,
    }

    with open(history_dir / filename, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


DEFAULT_FEEDBACK_PROMPT = """Ти си експерт по фармацевтична комуникация и оценител на комуникативни умения.
Анализирай следния разговор между фармацевт-студент и симулиран пациент.

Предостави ПОДРОБНА обратна връзка по следните области:

КЛИНИЧНА ОЦЕНКА:
- Правилност на препоръката
- Задал ли е студентът ключовите въпроси
- Безопасност на решенията
- Пропуснати важни аспекти

КОМУНИКАТИВНИ УМЕНИЯ:
- Отворени въпроси (брой и примери)
- Затворени въпроси (брой и уместност)
- Обобщаване и парафразиране
- Емпатичен отговор
- Използване на разбираем език

ПРЕПОРЪКИ ЗА ПОДОБРЕНИЕ:
- Какво е направено добре (конкретни примери)
- Какво може да се подобри (конкретни предложения)
- Обща оценка по скала от 1 до 5

Бъди конструктивен, справедлив и балансиран. Започни с положителното."""


# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback_text" not in st.session_state:
    st.session_state.feedback_text = ""
if "current_patient" not in st.session_state:
    st.session_state.current_patient = None


# ─────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ─────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 2, 1.2])
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-header">
                <div class="login-logo">ФГ</div>
                <h2>Фармацевтични грижи</h2>
                <p>Система за комуникационен тренинг</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Имейл", placeholder="ime.familia@uni.bg")
            course_code = st.text_input("Код за достъп", type="password", placeholder="Получавате го от преподавателя")
            submitted = st.form_submit_button("Вход")

            if submitted:
                if not email or not course_code:
                    st.error("Моля, попълнете и двете полета.")
                else:
                    ok, msg = check_login(email, course_code)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.user_email = email.strip().lower()
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("При проблеми с достъпа се обърнете към преподавателя на курса.")

    st.stop()


# ─────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────

patients = load_patients()
client = get_openai_client()


# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### Панел за управление")
    st.divider()

    # Patient selector
    patient_labels = [f"{p['name']}, {p.get('age', '?')} г." for p in patients]
    selected_idx = st.selectbox(
        "ПАЦИЕНТСКИ КАЗУС",
        range(len(patients)),
        format_func=lambda i: patient_labels[i],
    )
    selected_patient = patients[selected_idx]

    # Scenario description
    st.info(selected_patient.get("scenario_hint", ""))

    # Reset on patient change
    if st.session_state.current_patient != selected_patient["name"]:
        st.session_state.current_patient = selected_patient["name"]
        st.session_state.messages = []
        st.session_state.feedback_text = ""

    st.divider()

    # Session controls
    if st.button("Нова сесия"):
        st.session_state.messages = []
        st.session_state.feedback_text = ""
        st.rerun()

    # Message count
    msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.caption(f"Съобщения в тази сесия: {msg_count}")

    st.divider()
    st.caption(f"Потребител: {st.session_state.user_email}")

    if st.button("Изход"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ── CHAT AREA ────────────────────────────────────────────────

st.markdown(f"## Консултация — {selected_patient['name']}")
st.divider()

# Initialize with patient's opening message
if not st.session_state.messages:
    opening = selected_patient.get("opening_message", "Здравейте, имам нужда от помощ.")
    st.session_state.messages.append({"role": "assistant", "content": opening})

# Render messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=None):
            st.markdown(f"**Фармацевт:** {msg['content']}")
    else:
        with st.chat_message("assistant", avatar=None):
            st.markdown(f"**Пациент:** {msg['content']}")


# ── FEEDBACK DISPLAY ─────────────────────────────────────────

if st.session_state.feedback_text:
    st.divider()

    st.markdown("""
    <div class="feedback-header">
        <h3>Анализ на консултацията</h3>
        <p>Автоматизирана оценка на комуникативните умения и клиничната адекватност</p>
    </div>
    """, unsafe_allow_html=True)

    parts = st.session_state.feedback_text.split("|||")

    if len(parts) >= 3:
        tab1, tab2, tab3 = st.tabs([
            "Клинична оценка",
            "Комуникативни умения",
            "Препоръки за подобрение"
        ])
        with tab1:
            st.markdown(parts[0].strip())
        with tab2:
            st.markdown(parts[1].strip())
        with tab3:
            st.markdown(parts[2].strip())
    else:
        # Fallback: show as single block
        st.markdown(st.session_state.feedback_text)

    st.divider()
    st.caption('Натиснете "Нова сесия" в панела отляво, за да започнете нов разговор.')


# ── INPUT + ASSESSMENT TRIGGER ───────────────────────────────

if not st.session_state.feedback_text:
    # Chat input
    if user_input := st.chat_input("Напишете съобщение към пациента..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner(""):
            try:
                response = chat_with_patient(
                    client,
                    st.session_state.messages,
                    selected_patient["system_prompt"]
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Грешка при комуникация с AI: {e}")
                st.session_state.messages.pop()

        st.rerun()

    # Assessment button (only after enough messages)
    if len(st.session_state.messages) >= 4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Приключване и оценка на консултацията"):
            with st.spinner("Генериране на обратна връзка..."):
                try:
                    feedback = generate_feedback(
                        client, st.session_state.messages, selected_patient
                    )
                    st.session_state.feedback_text = feedback

                    save_conversation(
                        st.session_state.user_email,
                        selected_patient["name"],
                        st.session_state.messages,
                        feedback
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Грешка при генериране на обратна връзка: {e}")
