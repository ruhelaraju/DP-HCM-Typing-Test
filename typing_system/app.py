import streamlit as st
import time
import pandas as pd
from difflib import SequenceMatcher
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Government Typing Examination", layout="wide")

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
textarea {
    font-size: 18px !important;
}
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

# ---------------- LOGIN PAGE ----------------
if st.session_state.page == "login":

    st.markdown('<div class="header">Government Typing Examination Portal</div>', unsafe_allow_html=True)

    role = st.radio("Login As:", ["Student", "Admin"])

    if role == "Student":
        st.session_state.role = "student"
        if st.button("Proceed as Student"):
            st.session_state.page = "student_home"
            st.rerun()

    else:
        st.session_state.role = "admin"
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
    category = st.selectbox("Select Category", ["10 WPM", "25 WPM", "40 WPM"])

    if st.button("Start Test"):

        if name and category and os.path.exists(PARAGRAPH_FILE):
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

    # TIMER
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

    st.session_state.typed_text = st.text_area("Typing Area", height=250)

    if st.button("Submit Test"):
        st.session_state.submitted = True

    # RESULT
    if st.session_state.submitted:

        typed = st.session_state.typed_text
        original_part = paragraph[:len(typed)]

        matcher = SequenceMatcher(None, original_part, typed)

        mistakes = sum(1 for tag, *_ in matcher.get_opcodes() if tag != "equal")

        time_taken = (time.time() - st.session_state.start_time) / 60
        gross_speed = (len(typed)/5)/time_taken if time_taken>0 else 0
        final_speed = max(gross_speed - mistakes, 0)

        if final_speed < 30:
            marks = "Disqualify"
        elif final_speed == 30:
            marks = 10
        elif 31 <= final_speed <= 35:
            marks = 12
        elif 36 <= final_speed <= 40:
            marks = 15
        elif 41 <= final_speed <= 45:
            marks = 18
        elif 46 <= final_speed <= 50:
            marks = 21
        else:
            marks = 25

        st.success(f"Final Speed: {round(final_speed,2)} WPM")
        st.info(f"Mistakes: {mistakes}")
        st.info(f"Marks: {marks}")

        data = {
            "Name": st.session_state.name,
            "Category": st.session_state.category,
            "Final Speed": round(final_speed,2),
            "Mistakes": mistakes,
            "Marks": marks
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

        st.download_button("Download Results CSV", df.to_csv(index=False), "results.csv")