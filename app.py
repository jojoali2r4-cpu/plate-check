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

if "processing" not in st.session_state:
    st.session_state.processing = False


# =========================================================
# رفع ملف Excel
# =========================================================

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"],
    key="excel_upload"
)

plates = []


if uploaded_file is not None:

    try:

        df = pd.read_excel(uploaded_file)

        # -------------------------------------------------
        # تنظيف أسماء الأعمدة
        # -------------------------------------------------

        cleaned_columns = {}

        for column in df.columns:

            clean_column = str(column).strip()

            clean_column = clean_column.replace(" ", "")
            clean_column = clean_column.replace("ة", "ه")
            clean_column = clean_column.replace("أ", "ا")
            clean_column = clean_column.replace("إ", "ا")
            clean_column = clean_column.replace("آ", "ا")

            cleaned_columns[column] = clean_column


        # -------------------------------------------------
        # أسماء الأعمدة المقبولة
        # -------------------------------------------------

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


        # -------------------------------------------------
        # إذا لم نجد العمود
        # -------------------------------------------------

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

            # -------------------------------------------------
            # قراءة اللوحات
            # -------------------------------------------------

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
            f"❌ حدث خطأ أثناء قراءة ملف Excel: {e}"
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
# تنظيف النص الأساسي
# =========================================================

def basic_clean(text):

    text = normalize_numbers(text)

    text = str(text).lower()

    # توحيد بعض الحروف
    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ى", "ي")

    # إزالة التشكيل
    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )

    return text.strip()


# =========================================================
# أسماء الحروف العربية
# =========================================================

ARABIC_LETTERS = {

    "الف": "ا",
    "ألف": "ا",
    "الفه": "ا",

    "باء": "ب",
    "با": "ب",
    "باءه": "ب",

    "تاء": "ت",
    "تا": "ت",

    "ثاء": "ث",
    "ثا": "ث",

    "جيم": "ج",
    "جا": "ج",

    "حاء": "ح",
    "حا": "ح",

    "خاء": "خ",
    "خا": "خ",

    "دال": "د",

    "ذال": "ذ",

    "راء": "ر",
    "را": "ر",

    "زاي": "ز",
    "زايه": "ز",
    "زاي": "ز",

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
    "يا": "ي"
}


# =========================================================
# الأرقام المنطوقة
# =========================================================

DIGIT_WORDS = {

    "صفر": "0",
    "زيرو": "0",

    "واحد": "1",
    "واحدة": "1",

    "اثنين": "2",
    "اثنان": "2",
    "اتنين": "2",

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
# كلمات يتم تجاهلها
# =========================================================

FILLER_WORDS = {
    "اللوحة",
    "لوحة",
    "اللوحه",
    "لوحه",
    "رقم",
    "الرقم",
    "هي",
    "هو",
    "موقع",
    "موجود",
    "موجودة",
    "الموجودة",
    "في",
    "الملف",
    "من",
    "و"
}


# =========================================================
# تنظيف لوحة Excel
# =========================================================

def normalize_plate(plate):

    text = basic_clean(plate)

    # تحويل الأرقام العربية
    text = normalize_numbers(text)

    # إزالة المسافات والعلامات
    text = re.sub(
        r"[^0-9\u0621-\u064A]",
        "",
        text
    )

    return text


# =========================================================
# تحويل كلمة منطوقة إلى حرف أو رقم
# =========================================================

def convert_spoken_word(word):

    word = basic_clean(word)

    # -----------------------------------------------------
    # إذا كانت الكلمة رقمًا مكتوبًا
    # -----------------------------------------------------

    if word.isdigit():
        return word


    # -----------------------------------------------------
    # حرف عربي منطوق
    # -----------------------------------------------------

    if word in ARABIC_LETTERS:

        return ARABIC_LETTERS[word]


    # -----------------------------------------------------
    # رقم منطوق
    # -----------------------------------------------------

    if word in DIGIT_WORDS:

        return DIGIT_WORDS[word]


    return None


# =========================================================
# تحويل الكلام المنطوق إلى صيغة لوحة
# =========================================================

def spoken_to_plate(text):

    text = basic_clean(text)

    # تحويل الأرقام العربية
    text = normalize_numbers(text)

    # فصل الكلام
    words = re.findall(
        r"[\u0621-\u064A0-9]+",
        text
    )

    result = ""

    for word in words:

        # تجاهل الكلمات غير المهمة
        if word in FILLER_WORDS:
            continue


        converted = convert_spoken_word(
            word
        )


        if converted is not None:

            result += converted

            continue


        # -------------------------------------------------
        # إذا كانت الكلمة تحتوي أرقامًا
        # -------------------------------------------------

        numbers = re.findall(
            r"\d+",
            word
        )

        if numbers:

            result += "".join(
                numbers
            )


    return result


# =========================================================
# تحويل الصوت إلى WAV
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
            f"❌ لا يمكن قراءة الملف الصوتي: {e}"
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

    # 20 ثانية لتقليل عدد طلبات Google
    chunk_length = 20000

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
    # شريط التقدم
    # =====================================================

    progress = st.progress(
        0,
        text="🎙️ جاري تحويل التسجيل..."
    )


    # =====================================================
    # التعرف على الكلام
    # =====================================================

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
            text="🎙️ جاري تحويل التسجيل..."
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
    # تجهيز اللوحات الموجودة في Excel
    # =====================================================

    normalized_plates = {}

    for plate in plates:

        normalized = normalize_plate(
            plate
        )

        if normalized:

            normalized_plates[
                normalized
            ] = plate


    # =====================================================
    # تحويل الكلام إلى لوحة
    # =====================================================

    spoken_plate = spoken_to_plate(
        spoken_text
    )


    # =====================================================
    # تطابق كامل 100%
    # =====================================================

    if spoken_plate in normalized_plates:

        return normalized_plates[
            spoken_plate
        ]


    # =====================================================
    # لا توجد مطابقة
    #
    # ممنوع هنا:
    # - partial matching
    # - similarity
    # - اقتراحات
    # - البحث عن جزء من الرقم
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


    # مسح النتيجة القديمة
    st.session_state.matched_plate = None
    st.session_state.spoken_text = ""


    # =====================================================
    # تحويل التسجيل
    # =====================================================

    spoken_text = audio_to_text(
        audio_bytes
    )


    st.session_state.spoken_text = spoken_text


    # =====================================================
    # البحث
    # =====================================================

    matched_plate = find_matching_plate(
        spoken_text,
        plates
    )


    st.session_state.matched_plate = matched_plate


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
# التسجيل من التطبيق
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
