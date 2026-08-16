import streamlit as st
import pandas as pd
import speech_recognition as sr
import re
import io

from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment
from rapidfuzz import fuzz


# =========================
# إعداد الصفحة
# =========================

st.set_page_config(
    page_title="نظام فحص لوحات السيارات",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 نظام فحص لوحات السيارات")


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
        df = pd.read_excel(uploaded_file)

        if "اللوحه" not in df.columns:

            st.error(
                "لم يتم العثور على عمود «اللوحه» في ملف Excel."
            )

        else:

            plates = (
                df["اللوحه"]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            st.success(
                f"تم تحميل {len(plates)} لوحة بنجاح."
            )

    except Exception as e:

        st.error(
            f"حدث خطأ أثناء قراءة ملف Excel: {e}"
        )


# =========================
# تحويل الأرقام العربية
# =========================

def normalize_numbers(text):

    arabic_numbers = "٠١٢٣٤٥٦٧٨٩"
    english_numbers = "0123456789"

    table = str.maketrans(
        arabic_numbers,
        english_numbers
    )

    return text.translate(table)


# =========================
# تنظيف النص
# =========================

def clean_text(text):

    text = normalize_numbers(text)

    text = text.lower()

    text = re.sub(
        r"[\s\-_,.!؟،]+",
        "",
        text
    )

    return text


# =========================
# تحويل الصوت إلى WAV
# =========================

def convert_to_wav(audio_bytes):

    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes)
    )

    wav_buffer = io.BytesIO()

    audio.export(
        wav_buffer,
        format="wav"
    )

    wav_buffer.seek(0)

    return wav_buffer


# =========================
# تحويل الصوت إلى نص
# =========================

def audio_to_text(audio_bytes):

    recognizer = sr.Recognizer()

    try:

        wav_file = convert_to_wav(audio_bytes)

        with sr.AudioFile(wav_file) as source:

            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(
            audio_data,
            language="ar-SA"
        )

        return text

    except sr.UnknownValueError:

        return ""

    except Exception as e:

        st.error(
            f"حدث خطأ أثناء تحويل الصوت إلى نص: {e}"
        )

        return ""


# =========================
# البحث عن اللوحات
# =========================
def find_matching_plates(spoken_text, plates):
    if not spoken_text or not plates:
        return []

    spoken_text = normalize_numbers(str(spoken_text))

    # توحيد المسافات
    spoken_text = re.sub(r"\s+", " ", spoken_text).strip()

    matches = []

    # استخراج الأرقام من الكلام
    numbers = re.findall(r"\d+", spoken_text)

    # تكوين أرقام اللوحات من:
    # 7260
    # أو 72 60
    candidates = []

    for i, number in enumerate(numbers):

        if len(number) == 4:
            candidates.append(number)

        elif (
            len(number) == 2
            and i + 1 < len(numbers)
            and len(numbers[i + 1]) == 2
        ):
            candidates.append(
                number + numbers[i + 1]
            )

    candidates = list(dict.fromkeys(candidates))

    # البحث عن كل رقم كامل داخل اللوحات
    for candidate in candidates:

        possible_plates = []

        for plate in plates:

            plate_text = normalize_numbers(
                str(plate)
            )

            plate_digits = "".join(
                re.findall(r"\d", plate_text)
            )

            if plate_digits == candidate:
                possible_plates.append(plate)

        # إذا وجدنا لوحة بنفس الرقم
        # نستخدم الحروف كعامل إضافي
        for plate in possible_plates:

            plate_text = clean_text(str(plate))

            # النص المنطوق كاملًا
            spoken_clean = clean_text(
                spoken_text
            )

            # تطابق كامل أولًا
            if plate_text in spoken_clean:
                matches.append(plate)

            else:
                # نأخذ درجة تشابه للكلام
                # مع المحافظة على الرقم الصحيح
                score = fuzz.partial_ratio(
                    plate_text,
                    spoken_clean
                )

                if score >= 55:
                    matches.append(plate)

    return list(dict.fromkeys(matches))




# =========================
# واجهة التسجيل
# =========================

st.divider()

st.header("🎙️ مصدر التسجيل")

tab1, tab2 = st.tabs(
    [
        "🎙️ تسجيل من التطبيق",
        "📁 رفع تسجيل جاهز"
    ]
)


# =========================
# تسجيل من التطبيق
# =========================

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

        if plates:

            spoken_text = audio_to_text(
                audio_bytes
            )

            matches = find_matching_plates(
                spoken_text,
                plates
            )

            st.session_state.matches = matches


# =========================
# رفع تسجيل جاهز
# =========================

with tab2:

    uploaded_audio = st.file_uploader(

        "🎵 اختاري تسجيلًا من الهاتف",

        type=[
            "wav",
            "mp3",
            "m4a",
            "ogg",
            "webm"
        ],

        key="audio_upload"

    )

    if uploaded_audio is not None:

        if plates:

            audio_bytes = uploaded_audio.read()

            spoken_text = audio_to_text(
                audio_bytes
            )

            matches = find_matching_plates(
                spoken_text,
                plates
            )

            st.session_state.matches = matches


# =========================
# عرض النتائج
# =========================

st.divider()

st.header("📋 اللوحات المتطابقة")


if "matches" not in st.session_state:

    st.session_state.matches = []


if st.session_state.matches:

    st.success(
        f"تم العثور على {len(st.session_state.matches)} لوحة مطابقة."
    )

    for plate in st.session_state.matches:

        st.write(
            f"🚨 **{plate}**"
        )

else:

    st.info(
        "لا توجد مطابقات حتى الآن."
    )
