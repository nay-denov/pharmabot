import streamlit as st
import json
import os
from openai import OpenAI
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# 1. КОНФИГУРАЦИЯ И CSS (ВИЗУАЛЕН СТИЛ)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Система за Фармацевтични Грижи",
    page_icon="🏥", # По-неутрална икона
    layout="wide",  # Използваме целия екран за по-модерен вид
    initial_sidebar_state="expanded"
)

# Custom CSS за професионален "Medical/Clinical" вид
st.markdown("""
<style>
    /* Основни цветове и шрифт */
    .stApp {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Стилизиране на чат балоните */
    .stChatMessage {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Скриване на стандартното меню на Streamlit за по-чист вид */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Стилизиране на страничната лента */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* Бутоните - по-строги */
    .stButton>button {
        border-radius: 4px;
        font-weight: 500;
        border: 1px solid #ced4da;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 2. ПОМОЩНИ ФУНКЦИИ (Остават същите, но с малки промени)
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
        # Fallback данни, ако няма json файл (за тест)
        return [{"name": "Тестов Пациент", "age": 50, "scenario_hint": "Примерен сценарий", "system_prompt": "Ти си пациент."}]

def get_openai_client():
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        st.error("Системна грешка: Липсва конфигурация на API.")
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
    Изискваме от AI да върне структуриран отговор, за да го покажем красиво.
    """
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    
    # Променяме промпта да бъде по-аналитичен
    prompt = f"""
    Действай като старши преподавател по Фармация. Анализирай разговора по-долу.
    
    Разговор:
    {conversation_text}
    
    Контекст на пациента: {patient_data.get('description', '')}
    
    Твоята задача е да даде три отделни секции:
    1. КЛИНИЧНА ОЦЕНКА: Правилно ли беше идентифициран проблема? Беше ли препоръката безопасна?
    2. КОМУНИКАЦИЯ: Отворени/затворени въпроси, емпатия, структура.
    3. ПРЕПОРЪКИ: Какво конкретно да промени студентът следващия път.
    
    Не използвай обръщения като "Здравей", мини директно към анализа.
    """
    
    response = client.chat.completions.create(
        model=get_secret("MODEL_NAME", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ─────────────────────────────────────────────────────────────
# 3. ИНТЕРФЕЙС: ЛОГИН (ИЗЧИСТЕН)
# ─────────────────────────────────────────────────────────────

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback_text" not in st.session_state:
    st.session_state.feedback_text = ""

if not st.session_state.authenticated:
    # Центриран, чист логин прозорец
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🏥 Вход в системата")
        st.markdown("**Катедра Фармацевтични грижи**")
        
        with st.form("login_form"):
            email = st.text_input("Електронна поща", placeholder="name@uni.bg")
            code = st.text_input("Код за достъп", type="password")
            submitted = st.form_submit_button("Влез", use_container_width=True)
            
            if submitted:
                # Тук сложете вашата логика за проверка (за тест пуска всичко)
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────
# 4. ОСНОВЕН ЕКРАН (РАБОТЕН ПЛОТ)
# ─────────────────────────────────────────────────────────────

patients = load_patients()
client = get_openai_client()

# --- HEADER ---
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.markdown("### Виртуална симулация на пациент")
    st.caption("Упражнение по снемане на анамнеза и консултиране")
with top_col2:
    if st.button("Изход", use_container_width=True):
        st.session_state.clear()
        st.rerun()
st.markdown("---")

# --- LAYOUT: SIDEBAR (Controls) + MAIN (Chat) ---
# Използваме Sidebar само за настройки, за да не разсейва

with st.sidebar:
    st.markdown("### Настройки на сесията")
    
    # Избор на пациент без емотикони
    patient_names = [p['name'] for p in patients]
    selected_idx = st.selectbox("Избор на казус", range(len(patients)), format_func=lambda i: patient_names[i])
    selected_patient = patients[selected_idx]
    
    st.info(f"**Сценарий:**\n{selected_patient.get('scenario_hint', '')}")

    # Reset Logic
    if "current_patient_name" not in st.session_state or st.session_state.current_patient_name != selected_patient['name']:
        st.session_state.current_patient_name = selected_patient['name']
        st.session_state.messages = []
        st.session_state.feedback_text = ""
        st.rerun()

    st.markdown("---")
    if st.button("Рестартирай сесията", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback_text = ""
        st.rerun()

# --- MAIN CHAT AREA ---

# Контейнер за чата, за да не се смесва с обратната връзка
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        # Официално начално съобщение
        welcome_msg = selected_patient.get("opening_message", "Здравейте.")
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

    for msg in st.session_state.messages:
        # Използваме вградените икони "user" и "assistant" вместо емотикони
        # или може да сложите 'avatar=None' за съвсем чист вид
        role_icon = "user" if msg["role"] == "user" else "assistant"
        avatar_img = None # Може да сложите URL към лого, ако искате
        
        with st.chat_message(msg["role"], avatar=avatar_img):
            st.write(msg["content"])

# --- INPUT AREA ---
# Показваме полето само ако няма генерирана обратна връзка
if not st.session_state.feedback_text:
    user_input = st.chat_input("Въведете вашия въпрос към пациента...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container: # Force render in the chat container
             with st.chat_message("user"):
                st.write(user_input)

        with st.spinner("Пациентът отговаря..."):
            ai_response = chat_with_patient(client, st.session_state.messages, selected_patient["system_prompt"])
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()

# --- FEEDBACK SECTION ---
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns([1, 2, 1])

with col_f2:
    # Централен бутон за приключване
    if not st.session_state.feedback_text:
        if st.button("Приключи консултацията и анализирай", use_container_width=True, type="primary"):
            with st.spinner("Генериране на доклад..."):
                fb = generate_feedback_structured(client, st.session_state.messages, selected_patient)
                st.session_state.feedback_text = fb
                st.rerun()

# --- ПОКАЗВАНЕ НА ДОКЛАДА (Ако има такъв) ---
if st.session_state.feedback_text:
    st.markdown("### 📋 Доклад за представянето")
    
    # Разделяме обратната връзка на табове за по-прегледно четене
    tab1, tab2, tab3 = st.tabs(["Клинична оценка", "Комуникативни умения", "Препоръки"])
    
    # Тъй като GPT връща текст, тук просто го показваме. 
    # В по-сложна версия може да накараме GPT да връща JSON и да го парснем.
    
    with tab1:
        st.info("Преглед на клиничните решения и безопасността.")
        st.markdown(st.session_state.feedback_text) # В реална ситуация бихме разделили текста
        
    with tab2:
        st.success("Анализ на използваните техники (Calgary-Cambridge).")
        st.markdown("*(Тук ще се появи специфичната част за комуникация)*")
        
    with tab3:
        st.warning("Ключови области за подобрение.")
        st.markdown("*(Тук ще се появят конкретните съвети)*")
