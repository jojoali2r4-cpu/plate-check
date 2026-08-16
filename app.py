import streamlit as st
import pandas as pd
import speech_recognition as sr
import re
import io

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

        # تنظيف أسماء الأعمدة
        cleaned_columns = {}

        for column in df.columns:

            clean_column = str(column).strip()

            clean_column = clean_column.replace(" ", "")
            clean_column = clean_column.replace("ة", "ه")
            clean_column = clean_column.replace("أ", "ا")
            clean_column = clean_column.replace("إ", "ا")
            clean_column = clean_column.replace("آ", "ا")

            cleaned_columns[column] = clean_column

        # أسماء محتملة لعمود اللوحات
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

        plate_column = None

        for original_column, clean_column in cleaned_columns.items():

            if clean_column in possible_names:

                plate_column = original_column
                break

        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود «اللوحة» في ملف Excel."
            )

            st.write(
                "أسماء الأعمدة الموجودة:"
            )

            st.write(
                list(df.columns)
            )

        else:

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
# الأرقام العربية
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
# أسماء الحروف العربية
# =========================================================

ARABIC_LETTERS = {

    "الف": "ا",
    "ألف": "ا",

    "باء": "ب",
    "با": "ب",

    "تاء": "ت",
    "تا": "ت",

    "ثاء": "ث",
    "ثا": "ث",

    "جيم": "ج",
    "جيم": "ج",

    "حاء": "ح",
    "حا": "ح",

    "خاء": "خ",
    "خا": "خ",

    "دال": "د",

    "ذال": "ذ",

    "راء": "ر",
    "را": "ر",

    "زاي": "ز",
    "زاي": "ز",
    "زايه": "ز",

    "سين": "س",
    "سينه": "س",
    "سا": "س",

    "شين": "ش",
    "شينه": "ش",

    "صاد": "ص",
    "صا": "ص",

    "ضاد": "ض",
    "ضا": "ض",

    "طاء": "ط",
    "طا": "ط",

    "ظاء": "ظ",
    "ظا": "ظ",

    "عين": "ع",
    "عينه": "ع",

    "غين": "غ",
    "غينه": "غ",

    "فاء": "ف",
    "فا": "ف",

    "قاف": "ق",
    "قا": "ق",

    "كاف": "ك",
    "كا": "ك",

    "لام": "ل",

    "ميم": "م",

    "نون": "ن",

    "هاء": "ه",
    "ها": "ه",

    "واو": "و",

    "ياء": "ي",
    "يا": "ي",

    "لا": "ل"
}


# =========================================================
# أرقام مفردة منطوقة
# =========================================================

DIGIT_WORDS = {

    "صفر": "0",
    "زيرو": "0",

    "واحد": "1",
    "واحدة": "1",

    "اثنين": "2",
    "اثنان": "2",
    "اتنين": "2",
    "اثنين": "2",

    "ثلاثة": "3",
    "ثلاث": "3",

    "اربعة": "4",
    "أربعة": "4",
    "اربع": "4",

    "خمسة": "5",
    "خمس": "5",

    "ستة": "6",
    "ست": "6",

    "سبعة": "7",
    "سبع": "7",

    "ثمانية": "8",
    "ثمان": "8",

    "تسعة": "9",
    "تسع": "9"
}


# =========================================================
# تنظيف عام
# =========================================================

def basic_clean(text):

    text = normalize_numbers(text)

    text = str(text).lower()

    text = text.replace(
        "أ",
        "ا"
    )

    text = text.replace(
        "إ",
        "ا"
    )

    text = text.replace(
        "آ",
        "ا"
    )

    text = text.replace(
        "ى",
        "ي"
    )

    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )

    return text


# =========================================================
# تحويل نص اللوحة الموجودة في Excel
# =========================================================

def normalize_plate(plate):

    text = basic_clean(
        plate
    )

    # الاحتفاظ بالحروف العربية والأرقام فقط
    text = re.sub(
        r"[^0-9\u0621-\u064A]",
        "",
        text
    )

    return text


# =========================================================
# تحويل الكلام المنطوق إلى صيغة اللوحة
# =========================================================

def normalize_spoken_text(text):

    text = basic_clean(
        text
    )

    # إزالة التنوين والرموز
    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )

    # ---------------------------------------------
    # توحيد بعض الكلمات التي قد تظهر من Google
    # ---------------------------------------------

    replacements = {

        "الف": "ألف",
        "الالف": "ألف",

        "با": "باء",
        "تا": "تاء",
        "ثا": "ثاء",
        "جا": "جيم",
        "حا": "حاء",
        "خا": "خاء",

        "را": "راء",
        "سا": "سين",
        "شا": "شين",
        "صا": "صاد",
        "ضا": "ضاد",

        "طا": "طاء",
        "ظا": "ظاء",

        "عا": "عين",
        "غا": "غين",

        "فا": "فاء",
        "قا": "قاف",
        "كا": "كاف",

        "يا": "ياء"
    }

    for old, new in replacements.items():

        text = re.sub(
            rf"\b{old}\b",
            new,
            text
        )


    # ---------------------------------------------
    # تحويل أسماء الحروف
    # ---------------------------------------------

    # الأطول أولًا حتى لا يحصل تعارض
    letter_words = sorted(
        ARABIC_LETTERS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for word, letter in letter_words:

        text = re.sub(
            rf"\b{word}\b",
            letter,
            text
        )


    # ---------------------------------------------
    # تحويل الأرقام المنطوقة
    # ---------------------------------------------

    digit_words = sorted(
        DIGIT_WORDS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for word, digit in digit_words:

        text = re.sub(
            rf"\b{word}\b",
            digit,
            text
        )


    # ---------------------------------------------
    # إزالة كلمات الربط الشائعة
    # ---------------------------------------------

    filler_words = [
        "و",
        "الرقم",
        "رقم",
        "لوحة",
        "لوحه",
        "لوحات",
        "موقع",
        "موجود",
        "هي",
        "هو"
    ]

    for word in filler_words:

        text = re.sub(
            rf"\b{word}\b",
            " ",
            text
        )


    # ---------------------------------------------
    # إزالة أي شيء غير حروف وأرقام
    # ---------------------------------------------

    text = re.sub(
        r"[^0-9\u0621-\u064A]+",
        "",
        text
    )


    return text


# =========================================================
# تحويل الصوت إلى صيغة مناسبة
# =========================================================

def prepare_audio(audio_bytes):

    try:

        audio = AudioSegment.from_file(
            io.BytesIO(audio_bytes)
        )

        # Mono
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


    # =====================================================
    # تقسيم الصوت
    # =====================================================

    # 15 ثانية بدل 8 لتقليل عدد الطلبات
    chunk_length = 15000

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

        chunks.append(
            audio[start:end]
        )


    recognized_parts = []


    # =====================================================
    # معالجة المقاطع
    # =====================================================

    progress = st.progress(
        0,
        text="🎙️ جاري التعرف على التسجيل..."
    )


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


            try:

                text = recognizer.recognize_google(
                    audio_data,
                    language="ar-SA"
                )

            except sr.UnknownValueError:

                text = ""

            except sr.RequestError:

                text = ""


            if text:

                recognized_parts.append(
                    text
                )


        except Exception:

            pass


        progress.progress(
            (index + 1) / len(chunks),
            text="🎙️ جاري التعرف على التسجيل..."
        )


    progress.empty()


    return " ".join(
        recognized_parts
    ).strip()


# =========================================================
# البحث عن اللوحة
# =========================================================

def find_matching_plate(
    spoken_text,
    plates
):

    if not spoken_text:
        return None

    if not plates:
        return None


    # =====================================================
    # تحويل الكلام إلى صيغة موحدة
    # =====================================================

    spoken_normalized = normalize_spoken_text(
        spoken_text
    )


    # =====================================================
    # أولًا: تطابق كامل
    # =====================================================

    for plate in plates:

        plate_normalized = normalize_plate(
            plate
        )

        if spoken_normalized == plate_normalized:

            return plate


    # =====================================================
    # ثانيًا:
    # البحث عن لوحة كاملة داخل الكلام
    #
    # مهم:
    # لا نعرض أي اقتراحات.
    # نرجع فقط لوحة موجودة في Excel.
    # =====================================================

    for plate in plates:

        plate_normalized = normalize_plate(
            plate
        )

        if (
            plate_normalized
            and
            plate_normalized in spoken_normalized
        ):

            return plate


    # =====================================================
    # لا يوجد تطابق
    # =====================================================

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


    # مسح النتيجة السابقة
    st.session_state.matched_plate = None
    st.session_state.spoken_text = ""


    # تحويل الصوت
    spoken_text = audio_to_text(
        audio_bytes
    )


    st.session_state.spoken_text = (
        spoken_text
    )


    # البحث
    matched_plate = find_matching_plate(
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

        type=None,

        key="audio_upload"

    )


    if uploaded_audio is not None:

        audio_bytes = uploaded_audio.read()

        process_audio(
            audio_bytes
        )


# =========================================================
# النتيجة
# =========================================================

st.divider()

st.header("📋 النتيجة")


if st.session_state.matched_plate:

    st.success(
        f"✅ {st.session_state.matched_plate} موجودة في الملف"
    )

elif st.session_state.spoken_text:

    st.error(
        "❌ اللوحة غير موجودة في الملف"
    )

else:

    st.info(
        "🎙️ سجلي أو ارفعي تسجيلًا للبحث عن اللوحة."
    )
