import streamlit as st
import pandas as pd
import speech_recognition as sr
import re
import io
import time

from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="نظام فحص لوحات السيارات",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 نظام فحص لوحات السيارات")


# =========================================================
# Session State
# =========================================================

if "matched_plate" not in st.session_state:
    st.session_state.matched_plate = None

if "spoken_text" not in st.session_state:
    st.session_state.spoken_text = ""


# =========================================================
# رفع ملف Excel
# =========================================================

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"]
)

plates = []


if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        # ---------------------------------------------
        # تنظيف أسماء الأعمدة
        # ---------------------------------------------

        cleaned_columns = {}

        for column in df.columns:

            clean_column = str(column).strip()

            # إزالة المسافات
            clean_column = clean_column.replace(
                " ",
                ""
            )

            # توحيد ة / ه
            clean_column = clean_column.replace(
                "ة",
                "ه"
            )

            # توحيد أ / إ / آ
            clean_column = clean_column.replace(
                "أ",
                "ا"
            )

            clean_column = clean_column.replace(
                "إ",
                "ا"
            )

            clean_column = clean_column.replace(
                "آ",
                "ا"
            )

            cleaned_columns[column] = clean_column


        # ---------------------------------------------
        # البحث عن عمود اللوحات
        # ---------------------------------------------

        plate_column = None

        possible_names = [
            "اللوحه",
            "لوحه",
            "اللوحات",
            "لوحات",
            "رقماللوحه",
            "رقماللوحات",
            "رقماللوحة",
            "رقماللوحات"
        ]

        for original_column, clean_column in cleaned_columns.items():

            if clean_column in possible_names:

                plate_column = original_column

                break


        # ---------------------------------------------
        # إذا لم يتم العثور على العمود
        # ---------------------------------------------

        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود «اللوحة» في ملف Excel."
            )

            st.write(
                "أسماء الأعمدة الموجودة في الملف:"
            )

            st.write(
                list(df.columns)
            )


        else:

            # -----------------------------------------
            # قراءة اللوحات
            # -----------------------------------------

            plates = (
                df[plate_column]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            st.success(
                f"✅ تم تحميل {len(plates)} لوحة بنجاح."
            )


    except Exception as e:

        st.error(
            f"حدث خطأ أثناء قراءة ملف Excel: {e}"
        )


# =========================================================
# تحويل الأرقام العربية إلى إنجليزية
# =========================================================

def normalize_numbers(text):

    arabic_numbers = "٠١٢٣٤٥٦٧٨٩"
    english_numbers = "0123456789"

    table = str.maketrans(
        arabic_numbers,
        english_numbers
    )

    return str(text).translate(table)


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

    text = normalize_numbers(text)

    text = text.lower()

    # إزالة المسافات والعلامات
    text = re.sub(
        r"[\s\-_,.!؟،:؛]+",
        "",
        text
    )

    return text


# =========================================================
# تجهيز الصوت
# =========================================================

def prepare_audio(audio_bytes):

    try:

        audio = AudioSegment.from_file(
            io.BytesIO(audio_bytes)
        )

        # تحويل إلى Mono
        audio = audio.set_channels(1)

        # 16 kHz
        audio = audio.set_frame_rate(16000)

        # 16 bit
        audio = audio.set_sample_width(2)

        return audio

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء قراءة الملف الصوتي: {e}"
        )

        return None


# =========================================================
# تحويل الصوت إلى نص
# =========================================================

def audio_to_text(audio_bytes):

    recognizer = sr.Recognizer()

    audio = prepare_audio(
        audio_bytes
    )

    if audio is None:

        return ""

    if len(audio) == 0:

        return ""


    # ---------------------------------------------
    # تقسيم الصوت إلى مقاطع
    # ---------------------------------------------

    chunk_length = 8000  # 8 ثواني

    chunks = []

    for start in range(
        0,
        len(audio),
        chunk_length
    ):

        end = min(
            start + chunk_length,
            len(audio)
        )

        chunk = audio[start:end]

        chunks.append(chunk)


    recognized_parts = []


    # ---------------------------------------------
    # شريط التقدم
    # ---------------------------------------------

    progress = st.progress(
        0,
        text="🎙️ جاري تحويل التسجيل إلى نص..."
    )


    # ---------------------------------------------
    # التعرف على المقاطع
    # ---------------------------------------------

    for index, chunk in enumerate(chunks):

        try:

            wav_buffer = io.BytesIO()

            chunk.export(
                wav_buffer,
                format="wav"
            )

            wav_buffer.seek(0)


            with sr.AudioFile(
                wav_buffer
            ) as source:

                audio_data = recognizer.record(
                    source
                )


            text = ""


            # -----------------------------------------
            # إعادة المحاولة في حالة مشكلة الاتصال
            # -----------------------------------------

            for attempt in range(3):

                try:

                    text = recognizer.recognize_google(
                        audio_data,
                        language="ar-SA"
                    )

                    break

                except sr.RequestError:

                    if attempt < 2:

                        time.sleep(1)

                    else:

                        text = ""


            if text:

                recognized_parts.append(
                    text
                )


        except sr.UnknownValueError:

            pass


        except sr.RequestError:

            pass


        except Exception:

            pass


        progress.progress(
            (index + 1) / len(chunks),
            text="🎙️ جاري تحويل التسجيل إلى نص..."
        )


    progress.empty()


    return " ".join(
        recognized_parts
    ).strip()


# =========================================================
# البحث عن اللوحة
# =========================================================

def find_exact_plate(
    spoken_text,
    plates
):

    if not spoken_text:

        return None

    if not plates:

        return None


    spoken_clean = clean_text(
        spoken_text
    )


    # =====================================================
    # مطابقة كاملة فقط
    # =====================================================

    for plate in plates:

        plate_clean = clean_text(
            plate
        )


        # تطابق كامل 100%
        if spoken_clean == plate_clean:

            # إرجاع نفس اللوحة الموجودة في Excel
            return plate


    return None


# =========================================================
# معالجة التسجيل
# =========================================================

def process_audio(audio_bytes):

    if not plates:

        st.warning(
            "⚠️ ارفعي ملف Excel أولًا."
        )

        return


    # مسح النتيجة القديمة
    st.session_state.matched_plate = None

    st.session_state.spoken_text = ""


    # ---------------------------------------------
    # تحويل الصوت إلى نص
    # ---------------------------------------------

    spoken_text = audio_to_text(
        audio_bytes
    )


    st.session_state.spoken_text = (
        spoken_text
    )


    # ---------------------------------------------
    # البحث عن تطابق كامل
    # ---------------------------------------------

    matched_plate = find_exact_plate(
        spoken_text,
        plates
    )


    st.session_state.matched_plate = (
        matched_plate
    )


# =========================================================
# مصدر التسجيل
# =========================================================

st.divider()

st.header("🎙️ مصدر التسجيل")


tab1, tab2 = st.tabs(
    [
        "🎙️ تسجيل من التطبيق",
        "📁 رفع تسجيل من الجوال"
    ]
)


# =========================================================
# تسجيل من التطبيق
# =========================================================

with tab1:

    audio_recorded = mic_recorder(

        start_prompt="🎙️ بدء التسجيل",

        stop_prompt="⏹️ إيقاف التسجيل",

        just_once=True,

        use_container_width=True,

        key="recorder"

    )


    if audio_recorded is not None:

        audio_bytes = audio_recorded["bytes"]

        process_audio(
            audio_bytes
        )


# =========================================================
# رفع تسجيل من الجوال
# =========================================================

with tab2:

    uploaded_audio = st.file_uploader(

        "📁 اختاري أي ملف صوتي من ملفات الهاتف",

        # لا يوجد فلتر للامتداد
        type=None,

        key="audio_upload"

    )


    if uploaded_audio is not None:

        audio_bytes = uploaded_audio.read()

        process_audio(
            audio_bytes
        )


# =========================================================
# عرض النص الذي فهمه النظام
# =========================================================

if st.session_state.spoken_text:

    st.divider()

    st.write(
        f"🎙️ **النظام فهم:** "
        f"{st.session_state.spoken_text}"
    )


# =========================================================
# عرض النتيجة
# =========================================================

st.divider()

st.header("📋 النتيجة")


if st.session_state.matched_plate:

    st.success(
        f"✅ {st.session_state.matched_plate} "
        f"موجودة في الملف"
    )

else:

    if st.session_state.spoken_text:

        st.error(
            "❌ اللوحة غير موجودة في الملف"
        )

    else:

        st.info(
            "🎙️ سجلي أو ارفعي تسجيلًا للبحث عن اللوحة."
        )
