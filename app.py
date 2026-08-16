import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
def audio_to_text(audio_bytes):
    recognizer = sr.Recognizer()

    try:
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_bytes)

        with sr.AudioFile("temp_audio.wav") as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language="ar-SA")
        return text

    except sr.UnknownValueError:
        return ""

    except Exception:
        return ""

st.set_page_config(
    page_title="نظام فحص لوحات السيارات",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 نظام فحص لوحات السيارات")
st.write("ارفعي ملف اللوحات ثم ابدئي التسجيل الصوتي.")

# =========================
# رفع ملف Excel
# =========================

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"]
)

plates = []

if uploaded_file is not None:
    try:
        df = pd.read_excel(
            uploaded_file
        )

        if "اللوحه" not in df.columns:
            st.error("لم يتم العثور على عمود «اللوحه» في الملف.")

        else:
            plates = (
                df["اللوحه"]
                .dropna()
                .astype(str)
                .str.replace(" ", "", regex=False)
                .tolist()
            )

            st.success(
                f"تم تحميل {len(plates)} لوحة بنجاح."
            )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")


st.divider()


# =========================
# التسجيل الصوتي
# =========================

st.subheader("🎙️ التسجيل الصوتي")

audio = mic_recorder(
    start_prompt="🎙️ بدء التسجيل",
    stop_prompt="⏹️ إيقاف التسجيل",
    just_once=True,
    use_container_width=True,
    key="car_plate_recorder"
    format="wav"
)


# =========================
# بعد انتهاء التسجيل
# =========================

if audio is not None:

    audio_bytes = audio["bytes"]

    # تحويل التسجيل الصوتي إلى نص
    spoken_text = audio_to_text(audio_bytes)
    st.write("النص الذي تم التعرف عليه:", spoken_text)

    # البحث عن لوحة مطابقة
    if spoken_text and plates:

        from rapidfuzz import process, fuzz

        result = process.extractOne(
            spoken_text,
            plates,
            scorer=fuzz.ratio
        )

        if result and result[1] >= 65:
            matched_plate = result[0]

            st.session_state.matches = [matched_plate]

        else:
            st.session_state.matches = []

    else:
        st.session_state.matches = []


st.divider()


# =========================
# نتائج المطابقة
# =========================

st.subheader("📋 اللوحات المتطابقة")

if "matches" not in st.session_state:
    st.session_state.matches = []

if st.session_state.matches:
    st.table(st.session_state.matches)

else:
    st.info("لا توجد مطابقات حتى الآن.")
