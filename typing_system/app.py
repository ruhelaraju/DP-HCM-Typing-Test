import streamlit as st
import time
import pandas as pd
from difflib import SequenceMatcher
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Delhi Police HCM Typing Examination", layout="wide")

TEST_DURATION = 600
CSV_FILE = "student_results.csv"
PARAGRAPH_FILE = "daily_paragraph.txt"

# ---------------- SESSION ----------------
if "role" not in st.session_state:
    st.session_state.role = "student"

if "page" not in st.session_state:
    st.session_state.page = "login"

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "typed_text" not in st.session_state:
    st.session_state.typed_text = ""

if "attempt_checked" not in st.session_state:
    st.session_state.attempt_checked = False

# ---------------- CSS GOVERNMENT STYLE ----------------
st.markdown("""
<style>
body { background-color: #f5f5f5; }
.header { text-align:center; font-size:32px; font-weight:bold; color:#003366; }

.timer-box {
    position: fixed;
    top: 90px;
    left: 20px;
    background-color: #003366;
    color: white;
    padding: 15px 25px;
    font-size: 22px;
    font-weight: bold;
    border-radius: 8px;
    z-index: 9999;
}

textarea { font-size: 18px !important; }

.mistake { color:red; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# ---------------- DISABLE COPY PASTE ----------------
st.markdown("""
<script>
document.addEventListener('contextmenu', event => event.preventDefault());
document.addEventListener('copy', event => event.preventDefault());
document.addEventListener('paste', event => event.preventDefault());
document.addEventListener('cut', event => event.preventDefault());
</script>
""", unsafe_allow_html=True)

# ---------------- FUNCTION: CHECK ALREADY ATTEMPTED ----------------
def already_attempted(name):
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        return name in df["Name"].values
    return False

# ---------------- FUNCTION: HIGHLIGHT MISTAKES ----------------
def highlight_mistakes(original, typed):
    matcher = SequenceMatcher(None, original, typed)
    result = ""

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result += typed[j1:j2]
        else:
            result += f"<span class='mistake'>{typed[j1:j2]}</span>"

    return result

# ---------------- LOGIN PAGE ----------------
if st.session_state.page == "login":

    st.markdown('<div class="header">Delhi Police HCM Typing Examination Portal</div>', unsafe_allow_html=True)

    role = st.radio("Login As:", ["Student", "Admin"])

    if role == "Student":
        if st.button("Proceed as Student"):
            st.session_state.page = "student_home"
            st.rerun()

    else:
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")

        if st.button("Login as Admin"):
            if username == "admin" and password == "admin123":
                st.session_state.page = "admin_panel"
                st.rerun()
            else:
                st.error("Invalid Credentials")

# ---------------- STUDENT HOME ----------------
elif st.session_state.page == "student_home":

    st.title("Typing Test")

    name = st.text_input("Enter Name")
    category = st.selectbox("Select Category", ["Gen", "OBC", "EWS", "SC", "ST"])

    if st.button("Start Test"):

        if not name:
            st.error("Enter your name")
            st.stop()

        if already_attempted(name):
            st.error("You have already attempted the test. Multiple attempts not allowed.")
            st.stop()

        if os.path.exists(PARAGRAPH_FILE):
            st.session_state.name = name
            st.session_state.category = category
            st.session_state.start_time = time.time()
            st.session_state.page = "exam"
            st.session_state.submitted = False
            st.session_state.typed_text = ""
            st.rerun()
        else:
            st.error("Paragraph not uploaded by admin.")

# ---------------- EXAM PAGE ----------------
elif st.session_state.page == "exam":

    with open(PARAGRAPH_FILE, "r", encoding="utf-8") as f:
        paragraph = f.read()

    elapsed = time.time() - st.session_state.start_time
    remaining = TEST_DURATION - elapsed

    if remaining <= 0:
        remaining = 0
        st.session_state.submitted = True

    minutes = int(remaining // 60)
    seconds = int(remaining % 60)

    st.markdown(f'<div class="timer-box">⏱ {minutes:02d}:{seconds:02d}</div>', unsafe_allow_html=True)

    st.write(f"Name: {st.session_state.name}")
    st.write(f"Category: {st.session_state.category}")
    st.write("---")

    st.subheader("Type the following paragraph:")
    st.write(paragraph)
    st.write("---")

    st.session_state.typed_text = st.text_area(
        "Typing Area",
        height=250,
        disabled=st.session_state.submitted
    )

    if st.button("Submit Test") and not st.session_state.submitted:
        st.session_state.submitted = True

    # ---------------- RESULT ----------------
    if st.session_state.submitted:

        typed = st.session_state.typed_text
        original_part = paragraph[:len(typed)]

        matcher = SequenceMatcher(None, original_part, typed)
        mistakes = sum(1 for tag, *_ in matcher.get_opcodes() if tag != "equal")

        time_taken = (time.time() - st.session_state.start_time) / 60
        gross_speed = (len(typed)/5)/time_taken if time_taken>0 else 0
        final_speed = max(gross_speed - mistakes, 0)

        final_speed_int = int(final_speed)

        if final_speed_int < 30:
            marks = "Disqualify"
        elif final_speed_int == 30:
            marks = 10
        elif 31 <= final_speed_int <= 35:
            marks = 12
        elif 36 <= final_speed_int <= 40:
            marks = 15
        elif 41 <= final_speed_int <= 45:
            marks = 18
        elif 46 <= final_speed_int <= 50:
            marks = 21
        else:
            marks = 25

        st.success(f"Raw Speed (Gross Speed): {round(gross_speed,2)} WPM")
        st.error(f"Mistakes: {mistakes}")
        st.success(f"Final Speed: {round(final_speed,2)} WPM")
        st.info(f"Marks: {marks}")

        # Highlight mistakes
        st.subheader("Typed Paragraph with Mistakes Highlighted")
        highlighted = highlight_mistakes(original_part, typed)
        st.markdown(highlighted, unsafe_allow_html=True)

        # Save Result (only once)
        if not os.path.exists(CSV_FILE) or st.session_state.name not in pd.read_csv(CSV_FILE)["Name"].values:

            data = {
                "Name": st.session_state.name,
                "Category": st.session_state.category,
                "Raw Speed": round(gross_speed,2),
                "Final Speed": round(final_speed,2),
                "Mistakes": mistakes,
                "Marks": marks,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            df = pd.DataFrame([data])

            if os.path.exists(CSV_FILE):
                df.to_csv(CSV_FILE, mode="a", header=False, index=False)
            else:
                df.to_csv(CSV_FILE, index=False)

    if not st.session_state.submitted:
        time.sleep(1)
        st.rerun()

# ---------------- ADMIN PANEL ----------------
elif st.session_state.page == "admin_panel":

    st.title("Admin Dashboard")

    uploaded_file = st.file_uploader("Upload Daily Paragraph (.txt)", type=["txt"])
    if uploaded_file:
        with open(PARAGRAPH_FILE, "w", encoding="utf-8") as f:
            f.write(uploaded_file.read().decode("utf-8"))
        st.success("Paragraph Uploaded Successfully")

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        st.subheader("Student Results")
        st.dataframe(df)

        st.download_button(
            "Download Results CSV",
            df.to_csv(index=False),
            "student_results.csv",
            "text/csv"
        )


