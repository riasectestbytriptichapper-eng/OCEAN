import streamlit as st
from email.message import EmailMessage
import smtplib
import traceback

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="OCEAN Personality Test", layout="centered")

# -------------------------------------------------
# CALLBACK (MUST BE TOP-LEVEL)
# -------------------------------------------------
def set_response(q_idx, value):
    st.session_state.responses[q_idx] = value

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "show_test" not in st.session_state:
    st.session_state.show_test = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "email_sent" not in st.session_state:
    st.session_state.email_sent = False

if "responses" not in st.session_state:
    st.session_state.responses = {}

if "info" not in st.session_state:
    st.session_state.info = {}

if "scores" not in st.session_state:
    st.session_state.scores = {"O":0,"C":0,"E":0,"A":0,"ES":0}

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("OCEAN Personality Assessment")

# -------------------------------------------------
# USER INFO FORM
# -------------------------------------------------
with st.form("info_form"):
    Name = st.text_input("Full Name")
    Age = st.number_input("Age", min_value=10, max_value=100, step=1)
    Education = st.text_input("Education")
    School = st.text_input("School / University")
    Subjects = st.text_input("Subjects")
    Hobbies = st.text_area("Hobbies")
    Dream = st.text_area("Your 'Impossible' Dream")
    Email = st.text_input("Email")
    Phone = st.text_input("Phone Number")

    start = st.form_submit_button("Start Test")

if start:
    st.session_state.info = {
        "Name": Name,
        "Age": Age,
        "Education": Education,
        "School": School,
        "Subjects": Subjects,
        "Hobbies": Hobbies,
        "Dream": Dream,
        "Email": Email,
        "Phone": Phone
    }
    st.session_state.show_test = True

if not st.session_state.show_test:
    st.stop()

# -------------------------------------------------
# QUESTIONS (OCEAN)
# -------------------------------------------------
questions = [
    ("I enjoy meeting new people and being the center of attention.", "E"),
    ("I keep my tasks well-organized and complete work on time.", "C"),
    ("I stay calm even in stressful situations.", "ES"),
    ("I enjoy learning new things and exploring new ideas.", "O"),
    ("I care about others' feelings and try to help them.", "A"),

    ("I like participating in group discussions.", "E"),
    ("I am detail-oriented in my work.", "C"),
    ("I bounce back quickly after disappointments.", "ES"),
    ("I am curious and enjoy intellectual challenges.", "O"),
    ("I avoid conflicts and try to maintain harmony.", "A"),

    ("I feel energized when I'm around others.", "E"),
    ("I take responsibilities seriously.", "C"),
    ("I don’t get anxious easily when performing under pressure.", "ES"),
    ("I enjoy artistic or creative activities.", "O"),
    ("I enjoy cooperating with others on shared goals.", "A"),

    ("I am energetic and enthusiastic in group settings.", "E"),
    ("I plan ahead before starting a task.", "C"),
    ("I can keep my emotions in check during difficult times.", "ES"),
    ("I get excited about trying new experiences.", "O"),
    ("I am considerate and polite in interactions.", "A"),

    ("I enjoy being part of social or team activities.", "E"),
    ("I follow through on commitments consistently.", "C"),
    ("I handle setbacks without getting overly upset.", "ES"),
    ("I am open to different opinions and perspectives.", "O"),
    ("I try to be empathetic and understanding.", "A"),
]

st.header("Rate each statement (1 = Strongly Disagree, 5 = Strongly Agree)")

# -------------------------------------------------
# QUESTION BUTTONS (CORRECT PATTERN)
# -------------------------------------------------
for idx, (q, _) in enumerate(questions):
    st.write(f"**{q}**")

    if idx not in st.session_state.responses:
        st.session_state.responses[idx] = 0

    cols = st.columns(5)

    for val in range(1, 6):
        with cols[val - 1]:

            st.button(
                str(val),
                key=f"q{idx}_{val}",
                on_click=set_response,
                args=(idx, val)
            )

            # RED INDICATOR (single source of truth)
            if st.session_state.responses[idx] == val:
                st.markdown(
                    """
                    <div style="
                        height:6px;
                        background-color:#ff2b2b;
                        margin-top:4px;
                        border-radius:4px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# -------------------------------------------------
# SUBMIT BUTTON (LOCKED UNTIL COMPLETE)
# -------------------------------------------------
all_answered = (
    len(st.session_state.responses) == len(questions)
    and all(v > 0 for v in st.session_state.responses.values())
)

submit = st.button("Submit Test", disabled=not all_answered)

# -------------------------------------------------
# SCORE CALCULATION
# -------------------------------------------------
if submit and not st.session_state.submitted:
    scores = {"O":0,"C":0,"E":0,"A":0,"ES":0}

    for idx, (_, trait) in enumerate(questions):
        scores[trait] += st.session_state.responses[idx]

    st.session_state.scores = scores
    st.session_state.submitted = True

# -------------------------------------------------
# EMAIL LOGIC
# -------------------------------------------------
if st.session_state.submitted and not st.session_state.email_sent:
    info = st.session_state.info
    scores = st.session_state.scores

    email_body = f"""
Name: {info['Name']}
Age: {info['Age']}
Education: {info['Education']}
School: {info['School']}
Subjects: {info['Subjects']}
Hobbies: {info['Hobbies']}
Dream: {info['Dream']}
Email: {info['Email']}
Phone: {info['Phone']}

--- OCEAN SCORES ---
Openness: {scores['O']}
Conscientiousness: {scores['C']}
Extraversion: {scores['E']}
Agreeableness: {scores['A']}
Emotional Stability: {scores['ES']}

--- Detailed Responses ---
"""

    for idx, (q, trait) in enumerate(questions):
        email_body += f"{q} [{trait}]: {st.session_state.responses[idx]}\n"

    try:
        sender = st.secrets["EMAIL"]
        receiver = st.secrets["RECEIVER"]
        password = st.secrets["EMAIL_PASSWORD"]
    except Exception:
        st.error("Missing EMAIL, RECEIVER, or EMAIL_PASSWORD in Streamlit secrets.")
        st.stop()

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"OCEAN Test Results – {info['Name']}"
    msg.set_content(email_body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        st.session_state.email_sent = True
    except Exception:
        st.error("Failed to send email.")
        st.code(traceback.format_exc())
        st.stop()

# -------------------------------------------------
# FINAL CONFIRMATION
# -------------------------------------------------
if st.session_state.email_sent:
    st.success(
        "Your results have been securely sent to Tripti Chapper Careers Counselling.\n"
        "Please contact them to receive your personalized report."
    )
