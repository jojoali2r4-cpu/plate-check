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

        # ---------------------------------------------
        # تنظيف أسماء الأعمدة
        # ---------------------------------------------

        cleaned_columns = {}

        for column in df.columns:

            clean_column = str(column).strip()

            clean_column = clean_column.replace(" ", "")
            clean_column = clean_column.replace("ة", "ه")
            clean_column = clean_column.replace("أ", "ا")
            clean_column = clean_column.replace("إ", "ا")
            clean_column = clean_column.replace("آ", "ا")

            cleaned_columns[column] = clean_column


        # ---------------------------------------------
        # أسماء محتملة لعمود اللوحات
        # ---------------------------------------------

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


        # ---------------------------------------------
        # إذا لم نجد العمود
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

    "لام": "ل"
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
# تنظيف النص
# =========================================================

def basic_clean(text):

    text = normalize_numbers(text)

    text = str(text).lower()

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

    return text


# =========================================================
# تنظيف لوحة Excel
# =========================================================

def normalize_plate(plate):

    text = basic_clean(
        plate
    )

    # الاحتفاظ بالحروف والأرقام فقط
    text = re.sub(
        r"[^0-9\u0621-\u064A]",
        "",
        text
    )

    return text


# =========================================================
# تحويل كلمة إلى حرف أو رقم
# =========================================================

def convert_spoken_token(token):

    token = basic_clean(
        token
    )

    # إزالة بعض العلامات
    token = re.sub(
        r"[^\u0621-\u064A0-9]",
        "",
        token
    )

    # رقم مكتوب كرقم
    if token.isdigit():

        return token


    # حرف منطوق
    if token in ARABIC_LETTERS:

        return ARABIC_LETTERS[token]


    # رقم منطوق
    if token in DIGIT_WORDS:

        return DIGIT_WORDS[token]


    return None


# =========================================================
# تحويل الكلام إلى مجموعات محتملة للوحات
# =========================================================

def extract_spoken_candidates(spoken_text):

    text = basic_clean(
        spoken_text
    )

    # تقسيم الكلام إلى كلمات
    raw_tokens = re.findall(
        r"[\u0621-\u064A0-9]+",
        text
    )


    converted_tokens = []

    for token in raw_tokens:

        converted = convert_spoken_token(
            token
        )

        if converted is not None:

            converted_tokens.append(
                converted
            )

        else:

            # إذا كانت الكلمة تحتوي رقمًا
            numbers = re.findall(
                r"\d+",
                token
            )

            if numbers:

                for number in numbers:

                    converted_tokens.append(
                        number
                    )


    candidates = []


    # =====================================================
    # إنشاء تسلسلات محتملة
    # =====================================================

    for start in range(
        len(converted_tokens)
    ):

        current = ""

        for end in range(
            start,
            min(
                start + 12,
                len(converted_tokens)
            )
        ):

            current += converted_tokens[end]

            candidates.append(
                current
            )


    # إزالة التكرار
    candidates = list(
        dict.fromkeys(
            candidates
        )
    )

    return candidates


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
    # اللوحات الموجودة فعليًا في Excel
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
    # أول محاولة:
    # الكلام كله يكون لوحة واحدة
    # =====================================================

    full_text = basic_clean(
        spoken_text
    )

    # إزالة كلمات الربط
    filler_words = [
        "اللوحة",
        "لوحة",
        "رقم",
        "الرقم",
        "هي",
        "هو",
        "موقع",
        "موجودة",
        "موجود",
        "من",
        "في"
    ]

    words = full_text.split()

    useful_words = []

    for word in words:

        if word not in filler_words:

            useful_words.append(
                word
            )

    converted_full = ""

    all_converted = True

    for word in useful_words:

        converted = convert_spoken_token(
            word
        )

        if converted is not None:

            converted_full += converted

        else:

            # إذا كانت الكلمة رقمًا أو تحتوي أرقامًا
            numbers = re.findall(
                r"\d+",
                word
            )

            if numbers:

                converted_full += "".join(
                    numbers
                )

            else:

                all_converted = False


    if converted_full in normalized_plates:

        return normalized_plates[
            converted_full
        ]


    # =====================================================
    # المحاولة الثانية:
    # استخراج تسلسلات كاملة من الكلام
    #
    # مهم جدًا:
    # لا توجد مطابقة جزئية داخل رقم آخر.
    # =====================================================

    candidates = extract_spoken_candidates(
        spoken_text
    )


    # =====================================================
    # مقارنة كل مرشح مع لوحة كاملة في Excel
    # =====================================================

    for candidate in candidates:

        if candidate in normalized_plates:

            return normalized_plates[
                candidate
            ]


    # =====================================================
    # لا يوجد تطابق
    # =====================================================

    return None


# =========================================================
# تجهيز الصوت
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

    # 15 ثانية لتقليل عدد الطلبات
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
    # شريط التقدم
    # =====================================================

    progress = st.progress(
        0,
        text="🎙️ جاري تحويل التسجيل..."
    )


    # =====================================================
    # التعرف على الصوت
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


    # تحويل الصوت
    spoken_text = audio_to_text(
        audio_bytes
    )


    st.session_state.spoken_text = (
        spoken_text
    )


    # البحث عن اللوحة
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

        # يسمح باختيار الملفات الصوتية المختلفة
        type=None,

        key="
