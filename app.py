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

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None


# =========================================================
# رفع Excel
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

        plate_column = None

        for column in df.columns:

            col = str(column).strip()

            col = col.replace(" ", "")
            col = col.replace("ة", "ه")
            col = col.replace("أ", "ا")
            col = col.replace("إ", "ا")
            col = col.replace("آ", "ا")

            if col in [
                "اللوحه",
                "لوحه",
                "اللوحات",
                "لوحات",
                "رقماللوحه",
                "رقماللوحات",
                "رقماللوحة",
                "رقماللوحة"
            ]:

                plate_column = column
                break


        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود «اللوحة» في ملف Excel."
            )

            st.write(
                "الأعمدة الموجودة:"
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
            f"❌ حدث خطأ أثناء قراءة Excel: {e}"
        )


# =========================================================
# توحيد الأرقام
# =========================================================

def normalize_numbers(text):

    arabic = "٠١٢٣٤٥٦٧٨٩"
    english = "0123456789"

    table = str.maketrans(
        arabic,
        english
    )

    return str(text).translate(table)


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

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
# أسماء الحروف العربية
# =========================================================

LETTER_WORDS = {

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
    "سا": "س",

    "شين": "ش",
    "شا": "ش",

    "صاد": "ص",
    "صا": "ص",

    "ضاد": "ض",
    "ضا": "ض",

    "طاء": "ط",
    "طا": "ط",

    "ظاء": "ظ",
    "ظا": "ظ",

    "عين": "ع",
    "عا": "ع",

    "غين": "غ",
    "غا": "غ",

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
# الحروف لو Google كتبها كحروف منفردة
# =========================================================

SINGLE_LETTERS = set(
    "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
)


# =========================================================
# الأرقام المنطوقة
# =========================================================

NUMBER_WORDS = {

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

IGNORE_WORDS = {

    "لوحة",
    "اللوحة",
    "لوحه",
    "اللوحه",

    "رقم",
    "الرقم",

    "موقع",
    "الموقع",

    "موجود",
    "موجودة",
    "الموجود",
    "الموجودة",

    "في",
    "الملف",

    "هي",
    "هو",

    "من",
    "و"
}


# =========================================================
# تحويل لوحة Excel إلى شكل موحد
# =========================================================

def normalize_plate(plate):

    text = clean_text(plate)

    # توحيد بعض الحروف
    text = text.replace("ة", "ه")

    # إزالة أي شيء غير حرف أو رقم
    text = re.sub(
        r"[^0-9\u0621-\u064A]",
        "",
        text
    )

    return text


# =========================================================
# تحويل كلمة منطوقة
# =========================================================

def convert_spoken_word(word):

    word = clean_text(word)

    if word in IGNORE_WORDS:
        return ""

    # رقم مكتوب
    if word.isdigit():
        return word

    # رقم منطوق
    if word in NUMBER_WORDS:
        return NUMBER_WORDS[word]

    # اسم حرف
    if word in LETTER_WORDS:
        return LETTER_WORDS[word]

    # حرف منفرد
    if len(word) == 1 and word in SINGLE_LETTERS:
        return word

    return ""


# =========================================================
# تحويل الكلام كله إلى شكل قابل للمقارنة
# =========================================================

def normalize_spoken_text(text):

    text = clean_text(text)

    words = re.findall(
        r"[\u0621-\u064A]+|\d+",
        text
    )

    result = ""

    for word in words:

        converted = convert_spoken_word(
            word
        )

        if converted:
            result += converted

    return result


# =========================================================
# إنشاء أشكال محتملة للوحة
# =========================================================

def generate_plate_variants(plate):

    plate = normalize_plate(plate)

    variants = set()

    # الشكل الأصلي
    variants.add(plate)

    # -----------------------------------------------------
    # فصل الحروف والأرقام
    # -----------------------------------------------------

    letters = re.sub(
        r"\d",
        "",
        plate
    )

    numbers = re.findall(
        r"\d",
        plate
    )

    # -----------------------------------------------------
    # إضافة الشكل بالحروف نفسها + الرقم
    # -----------------------------------------------------

    if letters and numbers:

        variants.add(
            letters + "".join(numbers)
        )


    # -----------------------------------------------------
    # أسماء الحروف
    # -----------------------------------------------------

    reverse_letters = {}

    for name, letter in LETTER_WORDS.items():

        if letter not in reverse_letters:

            reverse_letters[
                letter
            ] = name


    spoken_letters = ""

    for letter in letters:

        if letter in reverse_letters:

            spoken_letters += reverse_letters[
                letter
            ]


    # -----------------------------------------------------
    # الأرقام بالكلمات
    # -----------------------------------------------------

    reverse_numbers = {

        "0": "صفر",
        "1": "واحد",
        "2": "اثنين",
        "3": "ثلاثة",
        "4": "اربعة",
        "5": "خمسة",
        "6": "ستة",
        "7": "سبعة",
        "8": "ثمانية",
        "9": "تسعة"
    }


    spoken_numbers = ""

    for number in numbers:

        spoken_numbers += reverse_numbers.get(
            number,
            number
        )


    # -----------------------------------------------------
    # إضافة الأشكال
    # -----------------------------------------------------

    if spoken_letters and spoken_numbers:

        # راء سين قاف 2 4 3 4
        variants.add(
            spoken_letters +
            spoken_numbers
        )

        # رسق2434
        variants.add(
            letters +
            "".join(numbers)
        )


    return variants


# =========================================================
# البحث عن لوحة داخل الكلام
# =========================================================

def find_plate_in_speech(
    spoken_text,
    plates
):

    if not spoken_text:
        return None


    # =====================================================
    # الشكل الأول:
    # تحويل النص المنطوق كله إلى حروف/أرقام
    # =====================================================

    normalized_speech = normalize_spoken_text(
        spoken_text
    )


    # =====================================================
    # البحث عن اللوحات
    # =====================================================

    for plate in plates:

        plate_normalized = normalize_plate(
            plate
        )


        # -------------------------------------------------
        # 1. تطابق مباشر
        # -------------------------------------------------

        if plate_normalized in normalized_speech:

            return plate


        # -------------------------------------------------
        # 2. البحث عن أرقام اللوحة داخل النص
        # مع التأكد من الحروف
        # -------------------------------------------------

        plate_letters = re.sub(
            r"\d",
            "",
            plate_normalized
        )

        plate_numbers = "".join(
            re.findall(
                r"\d",
                plate_normalized
            )
        )


        if not plate_letters:
            continue

        if not plate_numbers:
            continue


        # -------------------------------------------------
        # تحويل أسماء الحروف إلى الشكل الطبيعي
        # -------------------------------------------------

        letter_positions = []

        for i, char in enumerate(
            normalized_speech
        ):

            if char in SINGLE_LETTERS:

                letter_positions.append(
                    (i, char)
                )


        # -------------------------------------------------
        # البحث عن الرقم الكامل
        # -------------------------------------------------

        if plate_numbers in normalized_speech:

            number_position = normalized_speech.find(
                plate_numbers
            )

            before_number = normalized_speech[
                :number_position
            ]


            # نبحث عن الحروف قبل الرقم
            if before_number.endswith(
                plate_letters
            ):

                return plate


    # =====================================================
    # 3. البحث في الكلمات الأصلية
    # =====================================================

    words = re.findall(
        r"[\u0621-\u064A]+|\d+",
        clean_text(spoken_text)
    )


    # نحول كل جزء منفرد
    converted_words = []

    for word in words:

        converted = convert_spoken_word(
            word
        )

        if converted:

            converted_words.append(
                converted
            )


    # =====================================================
    # البحث عن تسلسل لوحة داخل الكلمات
    # =====================================================

    converted_text = "".join(
        converted_words
    )


    for plate in plates:

        plate_normalized = normalize_plate(
            plate
        )


        if plate_normalized in converted_text:

            return plate


    return None


# =========================================================
# تجهيز الصوت
# =========================================================

def prepare_audio(audio_bytes):

    try:

        audio = AudioSegment.from_file(
            io.BytesIO(audio_bytes)
        )

        audio = audio.set_channels(1)

        audio = audio.set_frame_rate(16000)

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


    # =====================================================
    # تقسيم التسجيل الطويل
    # =====================================================

    chunk_length = 30000

    chunks = []

    for start in range(
        0,
        len(audio),
        chunk_length
    ):

        chunks.append(
            audio[
                start:start + chunk_length
            ]
        )


    texts = []


    progress = st.progress(
        0,
        text="🎙️ جاري التعرف على الكلام..."
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

                if text:

                    texts.append(
                        text
                    )

            except (
                sr.UnknownValueError,
                sr.RequestError
            ):

                pass


        except Exception:

            pass


        progress.progress(
            (index + 1) / len(chunks),
            text="🎙️ جاري التعرف على الكلام..."
        )


    progress.empty()


    return " ".join(
        texts
    ).strip()


# =========================================================
# معالجة التسجيل
# =========================================================

def process_audio(audio_bytes):

    if not plates:

        st.error(
            "⚠️ ارفعي ملف Excel أولًا."
        )

        return


    # مسح النتيجة السابقة
    st.session_state.matched_plate = None
    st.session_state.spoken_text = ""


    # =====================================================
    # تحويل الصوت
    # =====================================================

    spoken_text = audio_to_text(
        audio_bytes
    )


    st.session_state.spoken_text = spoken_text


    if not spoken_text:

        return


    # =====================================================
    # البحث داخل التسجيل
    # =====================================================

    matched_plate = find_plate_in_speech(
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

with
