"""
╔══════════════════════════════════════════════════════════════╗
║  Чатбот за обучение по комуникация – Фармацевтични грижи   ║
║  Pharmacy Communication Training Chatbot                     ║
║                                                              ║
║  Streamlit + OpenAI API                                      ║
║  Автор: [Вашето име]                                         ║
║  Версия: 1.0                                                 ║
╚══════════════════════════════════════════════════════════════╝

Как работи:
  1. Студентът влиза с имейл + код на курса
  2. Избира пациентски случай от менюто
  3. Провежда чат-разговор със симулиран пациент
  4. Натиска "Обратна връзка" и получава анализ на комуникацията си
  5. Може да прегледа минали разговори

Файлове, които трябва да редактирате:
  - patients.json   → добавяте/променяте пациентски случаи
  - students.txt    → списък с имейли на студентите
  - .streamlit/secrets.toml → API ключ и код на курса
"""

import streamlit as st
import json
import os
from openai import OpenAI
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ НА СТРАНИЦАТА
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Фармацевтични грижи – Обучение",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# ПОМОЩНИ ФУНКЦИИ
# ─────────────────────────────────────────────────────────────

def get_secret(key, default=""):
    """Взема стойност от secrets.toml или от environment variable."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


def load_patients():
    """Зарежда пациентските случаи от patients.json."""
    patients_file = Path(__file__).parent / "patients.json"
    with open(patients_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_students():
    """Зарежда списък с имейли от students.txt (по един на ред)."""
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
    """Проверява дали студентът има достъп."""
    correct_code = get_secret("COURSE_CODE", "pharma2025")
    if course_code != correct_code:
        return False, "Грешен код на курса."

    students = load_students()
    if not students:
        # Ако файлът е празен или липсва → пускаме всички (за тестване)
        return True, ""

    if email.lower().strip() in students:
        return True, ""
    else:
        return False, "Имейлът ви не е в списъка. Свържете се с преподавателя."


def get_openai_client():
    """Създава OpenAI клиент."""
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ Липсва OpenAI API ключ. Моля, конфигурирайте .streamlit/secrets.toml")
        st.stop()
    return OpenAI(api_key=api_key)


def chat_with_patient(client, messages, system_prompt):
    """Изпраща съобщение до OpenAI и получава отговор от 'пациента'."""
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = client.chat.completions.create(
        model=get_secret("MODEL_NAME", "gpt-4o"),
        messages=full_messages,
        temperature=0.7,
        max_tokens=800,
    )
    return response.choices[0].message.content


def generate_feedback(client, messages, patient_data):
    """Генерира обратна връзка за комуникацията на студента."""

    # Форматираме разговора като текст
    conversation_text = "\n".join([
        f"{'Фармацевт (студент)' if m['role'] == 'user' else 'Пациент'}: {m['content']}"
        for m in messages
    ])

    feedback_prompt = patient_data.get("feedback_prompt", DEFAULT_FEEDBACK_PROMPT)

    prompt = f"""{feedback_prompt}

---
## ИНФОРМАЦИЯ ЗА ПАЦИЕНТА (за справка при оценяването):
Име: {patient_data['name']}
Възраст: {patient_data.get('age', 'неизвестна')}
Описание на случая: {patient_data.get('description', '')}
Ключова информация, която студентът трябва да разбере: {patient_data.get('key_info', '')}

---
## РАЗГОВОР ЗА АНАЛИЗ:

{conversation_text}

---
Моля, предоставете обратната връзка на БЪЛГАРСКИ език.
"""

    response = client.chat.completions.create(
        model=get_secret("MODEL_NAME", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3000,
    )
    return response.choices[0].message.content


def save_conversation(email, patient_name, messages, feedback=""):
    """Запазва разговора във файл (за преглед от преподавателя)."""
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


# ─────────────────────────────────────────────────────────────
# ПРОМПТ ЗА ОБРАТНА ВРЪЗКА (по подразбиране)
# Може да се замени за всеки пациент поотделно в patients.json
# ─────────────────────────────────────────────────────────────

DEFAULT_FEEDBACK_PROMPT = """Ти си експерт по фармацевтична комуникация и оценител на комуникативни умения.
Анализирай следния разговор между фармацевт-студент и симулиран пациент.

Предостави ПОДРОБНА обратна връзка по следните области:

### 1. СТРУКТУРА НА КОНСУЛТАЦИЯТА
- Поздрав и представяне
- Установяване на причината за посещението
- Събиране на информация (анамнеза)
- Предоставяне на съвет/препоръка
- Приключване на разговора

### 2. КОМУНИКАТИВНИ УМЕНИЯ
- **Отворени въпроси**: Колко и какви отворени въпроса е задал студентът? (Примери от разговора)
- **Затворени въпроси**: Колко и какви? Уместно ли са използвани?
- **Обобщаване/Парафразиране**: Обобщил ли е студентът казаното от пациента?
- **Емпатичен отговор**: Проявил ли е съчувствие и разбиране?
- **Използване на разбираем език**: Избягвал ли е медицински жаргон?

### 3. КЛИНИЧНО СЪДЪРЖАНИЕ
- Задал ли е студентът подходящите въпроси за конкретния случай?
- Правилна ли е препоръката/съветът?
- Пропуснал ли е нещо важно?

### 4. ОБЩА ОЦЕНКА
- Какво е направено добре (конкретни примери)
- Какво може да се подобри (конкретни предложения)
- Обща оценка по скала от 1 до 5 (където 5 е отлично)

Бъди конструктивен, справедлив и балансиран. Започни с положителното.
Давай КОНКРЕТНИ примери от разговора."""


# ─────────────────────────────────────────────────────────────
# ИНТЕРФЕЙС: ВХОД
# ─────────────────────────────────────────────────────────────

# Инициализация на session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback_text" not in st.session_state:
    st.session_state.feedback_text = ""
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# Страница за вход
if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>💊 Фармацевтични грижи</h1>
        <h3>Чатбот за обучение по комуникация</h3>
        <p style="color: gray;">Упражнявайте комуникация с виртуални пациенти</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("📧 Университетски имейл", placeholder="ime.familia@uni.bg")
        course_code = st.text_input("🔑 Код на курса", type="password", placeholder="Получавате го от преподавателя")
        submitted = st.form_submit_button("Вход", use_container_width=True)

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

    st.markdown("---")
    st.caption("При проблеми с достъпа, свържете се с преподавателя.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# ИНТЕРФЕЙС: ГЛАВНА СТРАНИЦА (след вход)
# ─────────────────────────────────────────────────────────────

# Зареждаме пациентите
try:
    patients = load_patients()
except Exception as e:
    st.error(f"Грешка при зареждане на patients.json: {e}")
    st.stop()

client = get_openai_client()

# ─── Странична лента (Sidebar) ──────────────────────────────
with st.sidebar:
    st.markdown("## 💊 Навигация")
    st.markdown(f"**Студент:** {st.session_state.user_email}")
    st.divider()

    # Избор на пациент
    patient_names = [f"{p['name']} ({p.get('age', '?')} г.)" for p in patients]
    selected_idx = st.selectbox(
        "🧑‍⚕️ Изберете пациент:",
        range(len(patients)),
        format_func=lambda i: patient_names[i],
    )
    selected_patient = patients[selected_idx]

    # Показваме сценария (кратко описание)
    st.info(f"📋 **Сценарий:** {selected_patient.get('scenario_hint', 'Няма описание')}")

    # Ако пациентът се промени, нулираме чата
    if st.session_state.current_patient != selected_patient["name"]:
        st.session_state.current_patient = selected_patient["name"]
        st.session_state.messages = []
        st.session_state.feedback_text = ""
        st.session_state.show_feedback = False

    st.divider()

    # Бутони за действия
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Нов разговор", use_container_width=True):
            st.session_state.messages = []
            st.session_state.feedback_text = ""
            st.session_state.show_feedback = False
            st.rerun()

    with col2:
        feedback_btn = st.button(
            "📊 Обратна връзка",
            use_container_width=True,
            disabled=len(st.session_state.messages) < 2
        )

    st.divider()

    # Информация за студента
    msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.caption(f"📝 Изпратени съобщения: {msg_count}")

    st.divider()
    if st.button("🚪 Изход", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ─── Основна зона ───────────────────────────────────────────

st.markdown(f"### 💬 Разговор с: **{selected_patient['name']}**")

# Ако няма съобщения, показваме начално съобщение от пациента
if not st.session_state.messages:
    opening = selected_patient.get("opening_message", "Здравейте, имам нужда от помощ...")
    st.session_state.messages.append({"role": "assistant", "content": opening})

# Показваме съобщенията
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍⚕️"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤒"):
            st.write(msg["content"])

# ─── Обратна връзка ─────────────────────────────────────────

if feedback_btn and not st.session_state.show_feedback:
    with st.spinner("⏳ Генериране на обратна връзка... (може да отнеме 15–30 секунди)"):
        try:
            feedback = generate_feedback(client, st.session_state.messages, selected_patient)
            st.session_state.feedback_text = feedback
            st.session_state.show_feedback = True

            # Запазваме разговора
            save_conversation(
                st.session_state.user_email,
                selected_patient["name"],
                st.session_state.messages,
                feedback
            )
            st.rerun()
        except Exception as e:
            st.error(f"Грешка при генериране на обратна връзка: {e}")

if st.session_state.show_feedback:
    st.divider()
    st.markdown("## 📊 Обратна връзка за комуникацията")
    st.markdown(st.session_state.feedback_text)
    st.divider()
    st.info("💡 Натиснете **🔄 Нов разговор** в менюто, за да опитате отново с този пациент.")

# ─── Поле за въвеждане ──────────────────────────────────────

if not st.session_state.show_feedback:
    if user_input := st.chat_input("Напишете съобщение на пациента..."):
        # Добавяме съобщението на студента
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Получаваме отговор от „пациента"
        with st.spinner("Пациентът пише..."):
            try:
                response = chat_with_patient(
                    client,
                    st.session_state.messages,
                    selected_patient["system_prompt"]
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Грешка при комуникация с API: {e}")
                # Премахваме последното съобщение ако API-то е дало грешка
                st.session_state.messages.pop()

        st.rerun()
