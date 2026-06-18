import streamlit as st
import pandas as pd
from PIL import Image, ImageOps, ImageDraw
import os
import random
import time
import unicodedata
from streamlit_autorefresh import st_autorefresh

IMAGE_FOLDER = "images"
CSV_FILE = "questions.csv"

QUESTION_COUNT = 40
TIME_LIMIT = 20

MAX_WIDTH = 450
MAX_HEIGHT = 650

st.set_page_config(page_title="Chạy trạm giải phẫu", layout="wide")


def normalize(text):
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


@st.cache_data
def load_questions():
    return pd.read_csv(CSV_FILE, dtype=str).fillna("")


questions = load_questions()


def make_order():
    return random.sample(range(len(questions)), min(QUESTION_COUNT, len(questions)))


def start_exam():
    st.session_state.started = True
    st.session_state.order = make_order()
    st.session_state.index = 0
    st.session_state.question_id = 0
    st.session_state.correct = 0
    st.session_state.wrong = 0
    st.session_state.answered = False
    st.session_state.show_answer = False
    st.session_state.result = ""
    st.session_state.start_time = time.time()


def reset_home():
    st.session_state.started = False
    st.session_state.order = []
    st.session_state.index = 0
    st.session_state.question_id = 0
    st.session_state.correct = 0
    st.session_state.wrong = 0
    st.session_state.answered = False
    st.session_state.show_answer = False
    st.session_state.result = ""
    st.session_state.start_time = time.time()


def next_question():
    st.session_state.index += 1
    st.session_state.question_id += 1
    st.session_state.answered = False
    st.session_state.show_answer = False
    st.session_state.result = ""
    st.session_state.start_time = time.time()


def current_question():
    if st.session_state.index >= len(st.session_state.order):
        return None
    return questions.iloc[st.session_state.order[st.session_state.index]]


def footer():
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; color:gray; font-size:14px;">
            © 2026 Thuykongu<br>
            Contact: kakaka1549@gmail.com
        </div>
        """,
        unsafe_allow_html=True
    )


if "started" not in st.session_state:
    reset_home()


st.title("Chạy trạm giải phẫu")


if not st.session_state.started:
    st.write(f"Mỗi lượt: {QUESTION_COUNT} chi tiết bất kì.")
    st.write(f"Thời gian mỗi chi tiết: {TIME_LIMIT} giây.")

    if st.button("Bắt đầu"):
        start_exam()
        st.rerun()

    footer()
    st.stop()


st_autorefresh(interval=1000, key="timer_refresh")

q = current_question()


if q is None:
    total = st.session_state.correct + st.session_state.wrong
    percent = round(st.session_state.correct / total * 100, 1) if total else 0

    st.success("Xong bài.")
    st.write(f"Tổng câu: {total}")
    st.write(f"Đúng: {st.session_state.correct}")
    st.write(f"Sai: {st.session_state.wrong}")
    st.write(f"Điểm: {st.session_state.correct}/{QUESTION_COUNT}")
    st.write(f"Tỉ lệ đúng: {percent}%")

    if st.button("Làm lượt mới"):
        start_exam()
        st.rerun()

    if st.button("Về màn hình bắt đầu"):
        reset_home()
        st.rerun()

    footer()
    st.stop()


elapsed = int(time.time() - st.session_state.start_time)
time_left = max(0, TIME_LIMIT - elapsed)


if time_left <= 0 and not st.session_state.answered:
    st.session_state.answered = True
    st.session_state.show_answer = True
    st.session_state.wrong += 1
    st.session_state.result = "Hết giờ"
    st.rerun()


col1, col2 = st.columns([2, 1])


with col1:
    image_path = os.path.join(IMAGE_FOLDER, str(q["image"]))

    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    img.thumbnail((MAX_WIDTH, MAX_HEIGHT))

    x = int(q["x"])
    y = int(q["y"])

    draw = ImageDraw.Draw(img)
    r = 8
    draw.ellipse((x - r, y - r, x + r, y + r), fill="red")

    st.image(img)


with col2:
    st.subheader("Trả lời")
    st.metric("Thời gian còn lại", f"{time_left}s")
    st.write(f"Câu: {st.session_state.index + 1}/{len(st.session_state.order)}")

    answer_key = f"user_answer_{st.session_state.question_id}"
    form_key = f"answer_form_{st.session_state.question_id}"

    with st.form(form_key, clear_on_submit=False):
        user_answer = st.text_input(
            "Nhập đáp án",
            key=answer_key,
            disabled=st.session_state.answered
        )

        submitted = st.form_submit_button(
            "Nộp",
            disabled=st.session_state.answered
        )

    if submitted and not st.session_state.answered:
        elapsed_now = int(time.time() - st.session_state.start_time)

        st.session_state.answered = True
        st.session_state.show_answer = True

        if elapsed_now > TIME_LIMIT:
            st.session_state.wrong += 1
            st.session_state.result = "Hết giờ"
        elif normalize(user_answer) == normalize(q["answer"]):
            st.session_state.correct += 1
            st.session_state.result = "Đúng"
        else:
            st.session_state.wrong += 1
            st.session_state.result = "Sai"

        st.rerun()

    if st.session_state.result == "Đúng":
        st.success("Đúng")
    elif st.session_state.result == "Sai":
        st.error("Sai")
    elif st.session_state.result == "Hết giờ":
        st.error("Hết giờ")

    if st.session_state.show_answer:
        st.write("Đáp án đúng:")
        st.info(str(q["answer"]))

    if st.button("Câu tiếp"):
        next_question()
        st.rerun()

    st.divider()

    done = st.session_state.correct + st.session_state.wrong
    percent = round(st.session_state.correct / done * 100, 1) if done else 0

    st.write(f"Đã làm: {done}/{QUESTION_COUNT}")
    st.write(f"Đúng: {st.session_state.correct}")
    st.write(f"Sai: {st.session_state.wrong}")
    st.write(f"Tỉ lệ đúng: {percent}%")

    if st.button("Dừng bài"):
        st.session_state.index = len(st.session_state.order)
        st.rerun()


footer()
